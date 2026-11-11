#!/usr/bin/env python3
"""Tests for the causal block-NLMS FIR (no models, no audio files)."""
import inspect
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))

import fir_isolation as F  # noqa: E402


def speechlike(n=16000 * 6, seed=1):
    rng = np.random.default_rng(seed)
    t = np.zeros(n)
    for f in (150.0, 260.0, 780.0):
        t += np.sin(2 * np.pi * f * np.arange(n) / F.SR)
    env = 0.5 + 0.5 * np.sin(2 * np.pi * 2.7 * np.arange(n) / F.SR) ** 2
    return (t * env) / np.max(np.abs(t * env))


def noise(n=16000 * 6, seed=2):
    return np.random.default_rng(seed).standard_normal(n) * 0.3


class FirCausalityTests(unittest.TestCase):
    def test_future_samples_do_not_change_past_output(self):
        t, i = speechlike(), noise()
        close = t + i
        room = 0.5 * F.shift(t, 48) + 2.0 * F.shift(i, 48)
        base, _, _ = F.fir_nlms(close, room, taps=32, mu=0.3)
        cut = F.SR * 3
        c2, r2 = close.copy(), room.copy()
        c2[cut:] = 0.0
        r2[cut:] = 0.0
        changed, _, _ = F.fir_nlms(c2, r2, taps=32, mu=0.3)
        # everything up to the cut (minus one block of update granularity) must match
        self.assertTrue(np.allclose(base[:cut - F.BLOCK], changed[:cut - F.BLOCK], atol=1e-9))

    def test_no_oracle_arguments(self):
        for fn in (F.fir_nlms, F.fir_tracking):
            params = set(inspect.signature(fn).parameters)
            for banned in ('target', 'interference', 'leak', 'true_delay', 'tir'):
                self.assertNotIn(banned, params, f'{banned} must not be an algorithm input to {fn.__name__}')

    def test_tracking_future_samples_do_not_change_past_output(self):
        t, i = speechlike(), noise()
        close = t + i
        room = 0.5 * F.shift(t, 48) + 2.0 * F.shift(i, 48)
        base, _, _ = F.fir_tracking(close, room, taps=32, mu=0.3, chunk_s=1.0)
        cut = F.SR * 3
        c2, r2 = close.copy(), room.copy()
        c2[cut:] = 0.0
        r2[cut:] = 0.0
        changed, _, _ = F.fir_tracking(c2, r2, taps=32, mu=0.3, chunk_s=1.0)
        self.assertTrue(np.allclose(base[:cut - F.BLOCK], changed[:cut - F.BLOCK], atol=1e-9))

    def test_delay_estimate_is_causal_calibration(self):
        t = speechlike()
        room = F.shift(t, 48)
        lag = F.est_delay(t, room, F.SR // 2)
        self.assertLessEqual(abs(lag - 48), 4, f'lag {lag}')

    def test_fir_reduces_residual_on_short_reverb(self):
        t, i = speechlike(), noise()
        close = t + i
        room = F.reverb(0.5 * F.shift(t, 48) + 2.0 * F.shift(i, 48), 20, seed=3)
        out, _, _ = F.fir_nlms(close, room, taps=64, mu=0.3)
        n = min(len(out), len(close))
        before = float(np.sqrt(np.mean(close[n // 2:] ** 2)))
        after = float(np.sqrt(np.mean(out[n // 2:] ** 2)))
        self.assertLess(after, 0.85 * before)

    def test_fir_stable_under_zero_input(self):
        z = np.zeros(F.SR)
        out, lag, _ = F.fir_nlms(z, z, taps=32, mu=0.3)
        self.assertTrue(np.all(np.isfinite(out)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
