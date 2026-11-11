#!/usr/bin/env python3
"""Tests for the causal two-channel isolation prototype (no models, no audio files)."""
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))

import causal_isolation as C  # noqa: E402


def target(n=16000 * 8, seed=1):
    t = np.zeros(n)
    for f in (180.0, 320.0, 900.0):
        t += np.sin(2 * np.pi * f * np.arange(n) / C.SR)
    env = 0.6 + 0.4 * np.sin(2 * np.pi * 3.0 * np.arange(n) / C.SR) ** 2
    return (t * env) / np.max(np.abs(t * env))


def interference(n=16000 * 8, seed=2):
    rng = np.random.default_rng(seed)
    return rng.standard_normal(n) * 0.3


class CausalTests(unittest.TestCase):
    def test_delay_calibration_recovers_known_delay(self):
        t = target()
        room = C.delay(t, C.DELAY)
        out, lag, _ = C.causal_nlms(t, room)
        self.assertLessEqual(abs(abs(lag) - C.DELAY), 4, f'lag {lag}')

    def test_only_past_samples_are_used(self):
        t = target()
        i = interference()
        close = t + i
        room = 0.5 * C.delay(t, C.DELAY) + 2.0 * C.delay(i, C.DELAY)
        base, _, _ = C.causal_nlms(close, room)
        cut = C.SR * 4
        close2 = close.copy()
        close2[cut:] = close2[cut:] * 0.0   # destroy all future samples
        room2 = room.copy()
        room2[cut:] = room2[cut:] * 0.0
        changed, _, _ = C.causal_nlms(close2, room2)
        self.assertTrue(np.allclose(base[:cut - C.BLOCK], changed[:cut - C.BLOCK], atol=1e-9),
                        'output before the cut must not depend on future samples')
        self.assertFalse(np.allclose(base[cut:], changed[cut:]))

    def test_converges_toward_room_scale(self):
        t = target()
        i = interference()
        close = t + i
        room = 0.5 * C.delay(t, C.DELAY) + 2.0 * C.delay(i, C.DELAY)
        out, _, _ = C.causal_nlms(close, room)
        # residual interference should be much smaller than input
        n = min(len(out), len(i))
        residual = float(np.sqrt(np.mean(out[-C.SR:] ** 2)))
        before = float(np.sqrt(np.mean(close[-C.SR:] ** 2)))
        self.assertLess(residual, 0.6 * before)

    def test_clean_signal_is_preserved(self):
        t = target()
        room = 0.5 * C.delay(t, C.DELAY)
        out, _, _ = C.causal_nlms(t, room)
        k = min(len(out), len(t))
        a_out = float(np.dot(out[:k], t[:k])) / float(np.dot(t[:k], t[:k]))
        self.assertGreater(a_out, 0.7, 'adaptation gate must prevent target cancellation on a clean room')

    def test_reverb_room_is_harder_than_clean_room(self):
        t = target()
        i = interference()
        close = t + i
        room_clean = 0.5 * C.delay(t, C.DELAY) + 2.0 * C.delay(i, C.DELAY)
        room_rev = C.reverb_room(t, i, C.DELAY, C.LEAK_DB)
        out_clean, _, _ = C.causal_nlms(close, room_clean)
        out_rev, _, _ = C.causal_nlms(close, room_rev)
        tail = slice(-C.SR, None)
        r_clean = float(np.sqrt(np.mean(out_clean[tail] ** 2)))
        r_rev = float(np.sqrt(np.mean(out_rev[tail] ** 2)))
        self.assertGreater(r_rev, r_clean * 0.8, 'reverb should not be easier than a clean room')


if __name__ == '__main__':
    unittest.main(verbosity=2)
