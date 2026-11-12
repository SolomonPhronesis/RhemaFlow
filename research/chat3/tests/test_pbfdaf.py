#!/usr/bin/env python3
"""Independent convolution, streaming, causality, retention and stability checks."""
from dataclasses import replace
import inspect
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pbfdaf import Config, PBFDAF, process


class PBFDAFTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(761)
        self.r = rng.normal(0, .1, 8197)
        self.c = .4*self.r + rng.normal(0, .025, len(self.r))

    def test_partitioned_output_matches_independent_linear_convolution(self):
        for fft in (256, 512):
            cfg = Config(fft_size=fft, partitions=4, mu=0, control=False)
            f = PBFDAF(cfg)
            h = np.random.default_rng(12).normal(0, .01, cfg.support_samples)
            f._w[:] = np.fft.rfft(np.pad(h.reshape(4, -1), ((0, 0), (0, cfg.block_size))), axis=1)
            got = np.concatenate((f.push(self.c, self.r), f.flush()))
            want = self.c - np.convolve(self.r, h)[:len(self.r)]
            np.testing.assert_allclose(got, want, atol=2e-14, rtol=0)

    def test_every_partial_block_prefix_is_causal(self):
        cfg = Config(control=False)
        original = process(self.c, self.r, cfg)
        for cut in (1, 127, 128, 129, 333, 1025, 4001, 8003):
            c, r = self.c.copy(), self.r.copy()
            c[cut:] += .7
            r[cut:] = np.random.default_rng(cut).normal(0, 5, len(r)-cut)
            np.testing.assert_allclose(process(c, r, cfg)[:cut], original[:cut], atol=2e-13, rtol=0)

    def test_controlled_output_is_causal_inside_blocks(self):
        original = process(self.c, self.r)
        for cut in (79, 999, 4031):
            c, r = self.c.copy(), self.r.copy()
            c[cut:], r[cut:] = 0, 10
            np.testing.assert_allclose(process(c, r)[:cut], original[:cut], atol=2e-13, rtol=0)

    def test_irregular_chunks_keep_exact_state(self):
        f, out, start = PBFDAF(), [], 0
        for size in (1, 15, 127, 999, 0, 312, 9000):
            stop = min(start+size, len(self.c))
            out.append(f.push(self.c[start:stop], self.r[start:stop]))
            start = stop
        out.append(f.flush())
        np.testing.assert_array_equal(np.concatenate(out), process(self.c, self.r))

    def test_flush_is_length_preserving_and_does_not_read_future(self):
        for n in (0, 1, 127, 128, 129, 512):
            out = process(self.c[:n], self.r[:n])
            self.assertEqual(len(out), n)
            np.testing.assert_allclose(out, process(self.c, self.r)[:n], atol=2e-13, rtol=0)

    def test_emission_waits_for_one_block(self):
        f = PBFDAF()
        self.assertEqual(len(f.push(self.c[:127], self.r[:127])), 0)
        self.assertEqual(len(f.push(self.c[127:128], self.r[127:128])), 128)
        self.assertEqual(f.buffering_ms, 7.9375)

    def test_target_only_quiet_room_is_preserved(self):
        f = PBFDAF()
        out = np.concatenate((f.push(self.c, .5*self.c), f.flush()))
        np.testing.assert_array_equal(out, self.c)
        self.assertEqual(f.adapted_blocks, 0)

    def test_reference_free_target_is_preserved_after_adaptation(self):
        f = PBFDAF()
        f.push(self.c[:8192], self.r[:8192])
        b = f.config.support_samples
        f.push(np.zeros(b), np.zeros(b))
        target = self.c[:2048]
        got = f.push(target, np.zeros_like(target))
        np.testing.assert_allclose(got, target, atol=1e-15)

    def test_silence_has_finite_exact_zero_output(self):
        np.testing.assert_array_equal(process(np.zeros(32769), np.zeros(32769)), np.zeros(32769))

    def test_late_impulse_cannot_appear_early(self):
        f = PBFDAF(Config(mu=0, control=False))
        h = np.zeros(f.config.support_samples); h[300] = .6
        f._w[:] = np.fft.rfft(np.pad(h.reshape(8, -1), ((0, 0), (0, 128))), axis=1)
        x = np.zeros(2048); x[513] = 1
        out = f.push(np.zeros_like(x), x)
        self.assertLess(np.max(np.abs(out[:813])), 1e-14)
        self.assertAlmostEqual(out[813], -.6)

    def test_converges_on_known_causal_long_echo(self):
        rng = np.random.default_rng(44)
        r = rng.normal(0, .1, 16000*5)
        h = np.zeros(600); h[0], h[240], h[599] = .4, .2, -.1
        c = np.convolve(r, h)[:len(r)]
        out = process(c, r, Config(mu=.4, control=False))
        self.assertLess(np.mean(out[-16000:]**2), .04*np.mean(c[-16000:]**2))

    def test_weights_remain_causal_after_updates(self):
        f = PBFDAF(); f.push(self.c, self.r)
        taps = np.fft.irfft(f._w, n=256, axis=1)
        self.assertLess(np.max(np.abs(taps[:, 128:])), 1e-14)

    def test_persistent_memory_does_not_grow_with_stream_length(self):
        for fft in (256, 512):
            f = PBFDAF(Config(fft_size=fft, partitions=16))
            size = f.state_bytes
            for _ in range(12): f.push(self.c, self.r)
            self.assertEqual(f.state_bytes, size)
            self.assertLess(size, 200000)

    def test_impulsive_input_does_not_diverge(self):
        r = self.r.copy(); r[2000] = 100
        f = PBFDAF(); out = f.push(self.c, r)
        self.assertTrue(np.all(np.isfinite(out)))
        self.assertLessEqual(np.linalg.norm(np.fft.irfft(f._w, n=256, axis=1)), 1.5+1e-12)

    def test_no_oracle_or_label_inputs(self):
        self.assertEqual(list(inspect.signature(PBFDAF.push).parameters), ['self', 'close', 'room'])
        self.assertEqual(list(inspect.signature(process).parameters), ['close', 'room', 'config'])

    def test_bad_inputs_are_rejected_before_state_change(self):
        f = PBFDAF()
        for c, r in [([1], []), ([[1]], [[1]]), ([np.nan], [0]), ([0], [np.inf])]:
            with self.assertRaises(ValueError): f.push(c, r)
            self.assertEqual(f.blocks, 0)

    def test_closed_stream_cannot_resume(self):
        f = PBFDAF(); f.flush()
        with self.assertRaises(RuntimeError): f.push([], [])
        with self.assertRaises(RuntimeError): f.flush()

    def test_bad_config_is_rejected(self):
        for options in ({'fft_size': 128}, {'partitions': 2}, {'mu': float('nan')},
                        {'mu': -.1}, {'prediction_budget': 0}, {'sample_rate': 0}):
            with self.assertRaises(ValueError): replace(Config(), **options)


if __name__ == '__main__':
    unittest.main(verbosity=2)
