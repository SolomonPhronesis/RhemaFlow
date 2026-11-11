#!/usr/bin/env python3
"""Causal adaptive FIR isolation with frozen splits (train/tune/holdout).

Evidence class: SYNTHETIC_2CH_SIMULATION with frozen partitions. The algorithm
sees only the two microphone channels; the clean target and the mixing
coefficients are used for *scoring* and for synthesis only.

Splits (frozen, by case number): train 01-20, tune 21-30, holdout 31-40.
Parameters are chosen on the tune split with a signal-level objective; the
holdout is scored once.
"""
import csv
import json
import os
import sys
import time
import wave
import zlib

import numpy as np

SR = 16000
BASE = '/Users/solomonphronesis/Documents/deepseek-harness/default-workspace'
WAV = f'{BASE}/recovery_v4_work/bench/evidence/kjv40/wav'
SRC = f'{BASE}/recovery_v4_work/bench/sources'
OUT = f'{BASE}/rounds_restart/fir'
BLOCK = 160          # 10 ms
CAL_MS = 400
TIR_LIST = (0, -5)


def read_wav(p):
    with wave.open(p) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2, p
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0


def write_wav(p, x):
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def rms(x):
    return float(np.sqrt(np.mean(x * x))) or 1e-12


def fit(x, n):
    return x[:n] if len(x) >= n else np.tile(x, int(np.ceil(n / len(x))))[:n]


def shift(x, d):
    if d <= 0:
        return x
    return np.concatenate([np.zeros(d), x[:-d]])


def moving_shift(x, d0, d1):
    """Time-varying delay: speaker motion between d0 and d1 samples."""
    idx = np.arange(len(x)) - np.linspace(d0, d1, len(x))
    i0 = np.clip(np.floor(idx).astype(int), 0, len(x) - 1)
    i1 = np.clip(i0 + 1, 0, len(x) - 1)
    frac = np.clip(idx - i0, 0, 1)
    return x[i0] * (1 - frac) + x[i1] * frac


def reverb(x, ms=150, seed=0):
    """Causal room response: direct path + decaying diffuse tail (unit energy).

    A smooth exponential kernel alone is a ~5 Hz low-pass and destroys speech;
    the diffuse tail keeps the spectrum broadband, which is what a room does.
    """
    n = int(SR * ms / 1000)
    rng = np.random.default_rng(seed)
    ir = np.zeros(n)
    ir[0] = 0.75
    tail = rng.standard_normal(n) * np.exp(-np.arange(n) / max(1.0, n / 4.0))
    tail /= np.sqrt(float(np.sum(tail * tail)) + 1e-12)
    ir += 0.55 * tail
    ir /= np.sqrt(float(np.sum(ir * ir)) + 1e-12)
    return np.convolve(x, ir, mode='full')[:len(x)]


def est_delay(a, b, cal, max_lag=200):
    """Return L such that b ≈ a shifted right by L samples (b lags a when L > 0)."""
    a = a[:cal] - a[:cal].mean()
    b = b[:cal] - b[:cal].mean()
    n = len(a)
    best, lag_best = -np.inf, 0
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            x, y = a[: n - lag], b[lag:]
        else:
            x, y = a[-lag:], b[: n + lag]
        if len(x) < 800:
            continue
        c = float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-12))
        if c > best:
            best, lag_best = c, lag
    return lag_best


def align(room, lag):
    """Advance the room channel by `lag` samples so it lines up with the close channel."""
    if lag > 0:
        return room[lag:]
    if lag < 0:
        return np.concatenate([np.zeros(-lag), room[:lag]])
    return room


def synth(clip_path, interf, seed, tir):
    """Per-clip mixing parameters are random but frozen by seed; never given to the algorithm."""
    rng = np.random.default_rng(seed)
    t = read_wav(clip_path)
    n = len(t)
    tt = t / rms(t) * 0.08
    ii = fit(interf, n)
    ii = ii / rms(ii) * 0.08
    d0 = int(rng.integers(40, 61))
    d1 = d0 + int(rng.integers(0, 13))
    leak_db = float(rng.uniform(5.0, 7.0))   # target attenuation in the room mic (positive dB)
    drift = 10 ** (rng.uniform(-1.5, 1.5) * np.sin(2 * np.pi * rng.uniform(0.2, 0.5) * np.arange(n) / SR) / 20.0)
    close = tt + 10 ** (-tir / 20.0) * ii
    room = 10 ** (-leak_db / 20.0) * moving_shift(tt, d0, d1) + 10 ** (-(tir - leak_db) / 20.0) * moving_shift(ii, d0, d1)
    room = reverb(room, rng.uniform(120, 200), seed=int(rng.integers(1, 10**6))) * drift
    return close, room


def scalar_nlms(close, room, mu=0.5, gate=True, cal=CAL_MS):
    lag = est_delay(close, room, SR * cal // 1000)
    r = align(room, lag)
    n = min(len(close), len(r))
    c, r = close[:n], r[:n]
    out = np.empty(n)
    alpha = 0.0
    for s in range(0, n, BLOCK):
        e_end = min(s + BLOCK, n)
        cb, rb = c[s:e_end], r[s:e_end]
        out[s:e_end] = cb - alpha * rb
        if (not gate) or rms(rb) > rms(cb):
            alpha = float(np.clip(alpha + mu * float(np.dot(out[s:e_end], rb)) / (float(np.dot(rb, rb)) + 1e-9), 0.0, 1.2))
    return out, lag


def fir_nlms(close, room, taps=64, mu=0.3, gate=True, double_talk=False, cal=CAL_MS):
    """Causal block NLMS FIR.

    Output block k uses w from updates made on blocks < k (strictly causal); the
    window matrix row i references room samples [i-taps+1 .. i] only.
    """
    lag = est_delay(close, room, SR * cal // 1000)
    r = align(room, lag)
    n = min(len(close), len(r))
    c, r = close[:n], r[:n]
    rpad = np.concatenate([np.zeros(taps - 1), r])
    windows = np.lib.stride_tricks.sliding_window_view(rpad, taps)
    w = np.zeros(taps)
    out = np.empty(n)
    energy_hist = []
    t0 = time.perf_counter()
    for s in range(0, n, BLOCK):
        e_end = min(s + BLOCK, n)
        W = windows[s:e_end]
        y = W @ w
        out[s:e_end] = c[s:e_end] - y
        rb = r[s:e_end]
        cb = c[s:e_end]
        if (not gate) or rms(rb) > rms(cb):
            freeze = False
            if double_talk:
                energy = float(np.dot(cb, cb))
                energy_hist.append(energy)
                if len(energy_hist) > 50:
                    energy_hist.pop(0)
                freeze = energy > 1.8 * float(np.median(energy_hist)) + 1e-9
            if not freeze:
                e = out[s:e_end]
                w = w + mu * (W.T @ e) / (float(np.sum(W * W)) + 1e-9)
                w = np.clip(w, -2.0, 2.0)
    elapsed = time.perf_counter() - t0
    return out, lag, elapsed


def sir_db(out, target, interf):
    n = min(len(out), len(target), len(interf))
    t, i = target[:n], interf[:n]
    a = np.vstack([t, i]).T
    coef, *_ = np.linalg.lstsq(a, out[:n], rcond=None)
    tc, ic = coef[0] * t, coef[1] * i
    return 10 * np.log10((float(np.dot(tc, tc)) + 1e-12) / (float(np.dot(ic, ic)) + 1e-12))


def retention_db(out, target, close):
    k = min(len(out), len(target))
    t = target[:k]
    a_out = float(np.dot(out[:k], t)) / (float(np.dot(t, t)) + 1e-12)
    a_close = float(np.dot(close[:k], t)) / (float(np.dot(t, t)) + 1e-12)
    return 20 * np.log10((abs(a_out) + 1e-12) / (abs(a_close) + 1e-12))


def split_of(cid):
    n = int(cid)
    if n <= 20:
        return 'train'
    if n <= 30:
        return 'tune'
    return 'holdout'


def build(mode='build'):
    os.makedirs(OUT, exist_ok=True)
    gold = list(csv.DictReader(open(f'{BASE}/recovery_v4_work/bench/evidence/kjv40/manifest/40_verse_gold_manifest.csv')))
    sources = {'chatter': f'{SRC}/chatter_pewbeam_16k.wav', 'preacher2': f'{SRC}/overlap_smartverse_16k.wav'}
    interfs = {k: read_wav(v) for k, v in sources.items()}
    split_rows = []
    tune_metrics = []
    # ---- parameter selection on TUNE split only (signal level) -------------
    grid = [{'taps': L, 'mu': m} for L in (32, 64, 128) for m in (0.1, 0.3)]
    tune_clips = [g for g in gold if split_of(g['case_id']) == 'tune']
    for params in grid:
        ris = []
        for g in tune_clips:
            for name in sources:
                for tir in TIR_LIST:
                    close, room = synth(os.path.join(WAV, os.path.basename(g['wav_path'])), interfs[name],
                                        seed=zlib.crc32(f"{g['case_id']}|{name}|{tir}|synth".encode()), tir=tir)
                    out, _, _ = fir_nlms(close, room, taps=params['taps'], mu=params['mu'])
                    # recovery of target/interference for measurement only
                    t = read_wav(os.path.join(WAV, os.path.basename(g['wav_path'])))
                    tt = t / rms(t) * 0.08
                    ii = fit(interfs[name], len(t)); ii = ii / rms(ii) * 0.08
                    ris.append(sir_db(out, tt, ii) - sir_db(close, tt, ii))
        tune_metrics.append({'taps': params['taps'], 'mu': params['mu'],
                             'mean_delta_sir': round(float(np.mean(ris)), 3)})
    tune_metrics.sort(key=lambda r: -r['mean_delta_sir'])
    best = tune_metrics[0]
    with open(f'{OUT}/tune_grid.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(tune_metrics[0])); w.writeheader(); w.writerows(tune_metrics)
    # ---- build holdout processed audio ------------------------------------
    manifests = {m: [] for m in ('close', 'room', 'mix', 'scalar', 'fir', 'fir_dt')}
    for name in sources:
        for tir in TIR_LIST:
            for g in [x for x in gold if split_of(x['case_id']) == 'holdout']:
                cid = g['case_id']
                close, room = synth(os.path.join(WAV, os.path.basename(g['wav_path'])), interfs[name],
                                    seed=zlib.crc32(f"{cid}|{name}|{tir}|synth".encode()), tir=tir)
                mix = 0.5 * (close + room)
                scalar, _ = scalar_nlms(close, room)
                fir, _, _ = fir_nlms(close, room, taps=best['taps'], mu=best['mu'])
                fir_dt, _, _ = fir_nlms(close, room, taps=best['taps'], mu=best['mu'], double_talk=True)
                base = f"{cid}_{name}_{'m5' if tir < 0 else '0'}"
                for tag, sig in (('close', close), ('room', room), ('mix', mix), ('scalar', scalar),
                                 ('fir', fir), ('fir_dt', fir_dt)):
                    p = f'{OUT}/{base}_{tag}.wav'
                    write_wav(p, sig)
                    manifests[tag].append({'file': os.path.basename(p), 'path': p, 'case_id': cid,
                                           'verse_id': g['verse_id'], 'condition': f'{name}_{tir}dB',
                                           'snr_db': tir, 'split': 'holdout', 'src': tag})
                split_rows.append({'case_id': cid, 'split': 'holdout', 'source': name, 'tir_db': tir})
    # controls through the winning FIR
    chatter = interfs['chatter']
    for i in range(20):
        n = SR * 8
        start = (i * n) % max(1, len(chatter))
        seg = fit(None if False else np.concatenate([chatter[start:], chatter[:start]]), n)
        ii = seg / rms(seg) * 0.08
        out, _, _ = fir_nlms(ii, 2.0 * shift(ii, 48), taps=best['taps'], mu=best['mu'])
        p = f'{OUT}/CTRL{i:02d}_fir.wav'; write_wav(p, out)
        manifests.setdefault('controls', []).append({'file': os.path.basename(p), 'path': p, 'case_id': f'CTRL{i:02d}',
                                                     'verse_id': '', 'condition': 'chatter_only', 'snr_db': '-inf',
                                                     'split': 'holdout', 'src': 'fir'})
    for i in range(8):
        z = np.zeros(SR * 8)
        out, _, _ = fir_nlms(z, z, taps=best['taps'], mu=best['mu'])
        p = f'{OUT}/SIL{i:02d}_fir.wav'; write_wav(p, out)
        manifests.setdefault('controls', []).append({'file': os.path.basename(p), 'path': p, 'case_id': f'SIL{i:02d}',
                                                     'verse_id': '', 'condition': 'silence', 'snr_db': '-inf',
                                                     'split': 'holdout', 'src': 'fir'})
    for tag, rows in manifests.items():
        with open(f'{OUT}/manifest_{tag}.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['file', 'path', 'case_id', 'verse_id', 'condition', 'snr_db', 'split', 'src'])
            w.writeheader(); w.writerows(rows)
    # frozen split manifest for all 40
    with open(f'{OUT}/split_manifest.csv', 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['case_id', 'split'])
        for i in range(1, 41):
            w.writerow([f'{i:04d}', split_of(f'{i:04d}')])
    print(json.dumps({'best': best, 'manifests': {k: len(v) for k, v in manifests.items()}, 'dir': OUT}, indent=1))


if __name__ == '__main__':
    build()
