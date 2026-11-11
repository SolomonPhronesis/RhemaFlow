#!/usr/bin/env python3
"""Deterministic tests for the synthetic two-channel isolation study."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))

import two_channel_sim as sim  # noqa: E402


def target_signal(n=16000 * 8, seed=1):
    rng = np.random.default_rng(seed)
    t = np.zeros(n)
    for f in (180.0, 320.0, 900.0):
        t += np.sin(2 * np.pi * f * np.arange(n) / sim.SR)
    t *= 0.6 + 0.4 * np.sin(2 * np.pi * 3.0 * np.arange(n) / sim.SR) ** 2
    return t / np.max(np.abs(t))


def interference(n=16000 * 8, seed=2):
    rng = np.random.default_rng(seed)
    return rng.standard_normal(n) * 0.3


class DelayTests(unittest.TestCase):
    def test_known_delay_is_recovered(self):
        x = target_signal()
        room = sim.delay(x, 48)
        d = sim.est_delay(x, room)
        self.assertLessEqual(abs(abs(d) - 48), 4, f'estimated {d}')


class CancelTests(unittest.TestCase):
    def test_cancellation_improves_sir(self):
        t = target_signal()
        i = interference()
        close = t + i
        room = 0.5 * sim.delay(t, 48) + 2.0 * sim.delay(i, 48)
        d = sim.est_delay(close, room)
        out = sim.cancel(close, room, d)
        delta = sim.sir_db(out, t, i[:len(out)]) - sim.sir_db(close, t, i)
        self.assertGreater(delta, 8.0, f'delta SIR {delta}')

    def test_target_is_not_erased(self):
        t = target_signal()
        i = interference()
        close = t + i
        room = 0.5 * sim.delay(t, 48) + 2.0 * sim.delay(i, 48)
        out = sim.cancel(close, room, sim.est_delay(close, room))
        k = min(len(out), len(t))
        a_out = float(np.dot(out[:k], t[:k])) / float(np.dot(t[:k], t[:k]))
        a_close = float(np.dot(close[:k], t[:k])) / float(np.dot(t[:k], t[:k]))
        retention = 20 * np.log10((abs(a_out) + 1e-12) / abs(a_close))
        self.assertGreater(retention, -6.0, f'retention {retention}')
        self.assertLess(retention, 1.0)


class OverlapTests(unittest.TestCase):
    def test_auc_high_when_interference_dominates(self):
        t = target_signal()
        i = interference()
        # interference is silent for the first half, loud in the second half
        gate = np.concatenate([np.zeros(len(i) // 2), np.ones(len(i) - len(i) // 2)])
        i = i * gate
        close = t + 0.2 * i
        room = 0.4 * sim.delay(t, 32) + 2.0 * sim.delay(i, 32)
        labels = sim.frame_overlap_labels(i, t)
        scores = sim.frame_scores(close, room)
        m = min(len(labels), len(scores))
        auc = sim.roc_auc(scores[:m], labels[:m])
        self.assertIsNotNone(auc)
        self.assertGreater(auc, 0.85, f'auc {auc}')

    def test_frame_vectors_same_length(self):
        t = target_signal()
        i = interference()
        labels = sim.frame_overlap_labels(i, t)
        scores = sim.frame_scores(t + i, 0.5 * t + 2 * i)
        self.assertEqual(len(labels), len(scores))


class GuardTests(unittest.TestCase):
    def test_rejects_wrong_sample_rate(self):
        import tempfile, wave
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            p = f.name
        try:
            with wave.open(p, 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(b'\0\0' * 800)
            with self.assertRaises(ValueError):
                sim.read_wav(p)
        finally:
            os.unlink(p)


if __name__ == '__main__':
    unittest.main(verbosity=2)
