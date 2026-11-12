#!/usr/bin/env python3
"""Research-only constrained PBFDAF; NumPy only, no audio/model/file access.

The reference is the room microphone, NOT a clean far-end echo reference.
Energy/coherence controls are heuristics, never speaker identity evidence.
No room advancement, calibration pre-read, delay oracle, or lookahead is used.
Each output sample depends on inputs at or before its source sample index.
Scheduling waits for a full block (at most B-1 samples); flush pads only zeros.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Config:
    sample_rate: int = 16000
    fft_size: int = 256
    partitions: int = 8
    mu: float = 0.15
    room_ratio: float = 1.05
    surge_ratio: float = 3.0
    min_coherence: float = 0.05
    prediction_budget: float = 0.5
    max_norm: float = 1.5
    power_floor: float = 1e-9
    control: bool = True

    def __post_init__(self):
        if self.fft_size not in (256, 512) or self.partitions not in (4, 8, 16):
            raise ValueError('research grid: FFT 256/512, partitions 4/8/16')
        if not isinstance(self.sample_rate, int) or self.sample_rate <= 0:
            raise ValueError('sample_rate must be a positive integer')
        values = (self.mu, self.room_ratio, self.surge_ratio, self.min_coherence,
                  self.prediction_budget, self.max_norm, self.power_floor)
        if not all(np.isfinite(v) for v in values):
            raise ValueError('configuration must be finite')
        if not 0 <= self.mu <= 0.5 or self.room_ratio <= 0 or self.surge_ratio <= 1:
            raise ValueError('invalid adaptation parameters')
        if not 0 <= self.min_coherence <= 1 or not 0 < self.prediction_budget <= 1:
            raise ValueError('invalid control bounds')
        if self.max_norm <= 0 or self.power_floor <= 0:
            raise ValueError('invalid stability bounds')

    @property
    def block_size(self):
        return self.fft_size // 2

    @property
    def support_samples(self):
        return self.partitions * self.block_size


class PBFDAF:
    """Persistent stream. push(close, room) emits only complete output blocks.

    W_p stores the FFT of B causal taps followed by B exact zeros. X_p stores
    FFT([previous reference block, current reference block]) delayed p blocks.
    e_k = close_k - gain_k * IFFT(sum_p W_{k,p} X_{k-p})[B:2B].
    W_k and gain_k are functions of blocks strictly before k. Gradient and
    control decisions from k affect k+1 only. No current-block output limiter.
    """

    def __init__(self, config=Config()):
        self.config = config
        b, p = config.block_size, config.partitions
        self._w = np.zeros((p, b + 1), dtype=np.complex128)
        self._x = np.zeros_like(self._w)
        self._previous = np.zeros(b)
        self._pending = np.zeros((2, b))
        self._pending_n = 0
        self._power = np.zeros(b + 1)
        self._cross = np.zeros(b + 1, dtype=np.complex128)
        self._pc = np.zeros(b + 1)
        self._pr = np.zeros(b + 1)
        self._close_power = 0.0
        self._error_power = 0.0
        self._gain = 1.0
        self._closed = False
        self.blocks = 0
        self.adapted_blocks = 0
        self.frozen_blocks = 0

    @property
    def state_bytes(self):
        """Persistent ndarray storage, excluding Python objects/FFT temporaries."""
        return sum(v.nbytes for v in vars(self).values() if isinstance(v, np.ndarray))

    @property
    def buffering_ms(self):
        return 1000 * (self.config.block_size - 1) / self.config.sample_rate

    def push(self, close, room):
        if self._closed:
            raise RuntimeError('stream already flushed')
        c, r = np.asarray(close, dtype=np.float64), np.asarray(room, dtype=np.float64)
        if c.ndim != 1 or r.ndim != 1 or c.shape != r.shape:
            raise ValueError('equal-length mono chunks required')
        if not np.all(np.isfinite(c)) or not np.all(np.isfinite(r)):
            raise ValueError('non-finite audio input')
        b = self.config.block_size
        outputs, start = [], 0
        while start < len(c):
            count = min(b - self._pending_n, len(c) - start)
            end = self._pending_n + count
            self._pending[0, self._pending_n:end] = c[start:start + count]
            self._pending[1, self._pending_n:end] = r[start:start + count]
            self._pending_n = end
            start += count
            if end == b:
                outputs.append(self._block(self._pending[0], self._pending[1]))
                self._pending_n = 0
        return np.concatenate(outputs) if outputs else np.empty(0)

    def flush(self):
        if self._closed:
            raise RuntimeError('stream already flushed')
        self._closed = True
        count = self._pending_n
        if not count:
            return np.empty(0)
        self._pending[:, count:] = 0.0
        result = self._block(self._pending[0], self._pending[1])[:count]
        self._pending_n = 0
        return result

    def _block(self, c, r):
        cfg, b = self.config, self.config.block_size
        self._x[1:] = self._x[:-1].copy()
        self._x[0] = np.fft.rfft(np.concatenate((self._previous, r)))
        self._previous[:] = r
        prediction = np.fft.irfft(np.sum(self._w * self._x, axis=0), n=2*b)[b:]
        out = c - self._gain * prediction

        # The following statistics cannot affect the just-computed output.
        cp, rp = float(c @ c / b), float(r @ r / b)
        cc = np.fft.rfft(np.concatenate((np.zeros(b), c)))
        rr = np.fft.rfft(np.concatenate((np.zeros(b), r)))
        self._cross = .9*self._cross + .1*cc*np.conj(rr)
        self._pc = .9*self._pc + .1*np.abs(cc)**2
        self._pr = .9*self._pr + .1*np.abs(rr)**2
        coh = float(np.sum(np.abs(self._cross)**2) /
                    (np.sum(self._pc*self._pr) + cfg.power_floor))
        surge = self.blocks > 8 and cp > cfg.surge_ratio * max(self._close_power, cfg.power_floor)
        allow = rp > cfg.power_floor
        if cfg.control:
            allow = allow and rp > cfg.room_ratio*cp and not surge
            allow = allow and (self.blocks < 8 or coh >= cfg.min_coherence)

        current_power = np.sum(np.abs(self._x)**2, axis=0)
        self._power = .8*self._power + .2*current_power
        denom = np.maximum(np.maximum(current_power, self._power), cfg.power_floor)
        if allow and cfg.mu:
            # A past-error-derived clip limits impulsive adaptation, never output.
            limit = 4*np.sqrt(max(self._error_power, cfg.power_floor))
            error = np.clip(out, -limit, limit) if self.blocks > 8 else out
            ef = np.fft.rfft(np.concatenate((np.zeros(b), error)))
            gradient = np.fft.irfft(np.conj(self._x)*ef[None, :]/denom[None, :], n=2*b, axis=1)
            taps = np.fft.irfft(self._w, n=2*b, axis=1)[:, :b]
            taps += cfg.mu*gradient[:, :b]
            norm = float(np.linalg.norm(taps))
            if norm > cfg.max_norm:
                taps *= cfg.max_norm/norm
            self._w = np.fft.rfft(np.pad(taps, ((0, 0), (0, b))), axis=1)
            self.adapted_blocks += 1
        else:
            self.frozen_blocks += 1
        if cfg.control:
            pp = float(prediction @ prediction / b)
            self._gain = min(1.0, np.sqrt(cfg.prediction_budget*cp/(pp + cfg.power_floor)))
        self._close_power = .95*self._close_power + .05*cp
        self._error_power = .95*self._error_power + .05*float(out @ out / b)
        self.blocks += 1
        return out


def process(close, room, config=Config()):
    stream = PBFDAF(config)
    return np.concatenate((stream.push(close, room), stream.flush()))
