#!/usr/bin/env python3
"""Build synthetic two-channel close/room pairs and a cancelled (isolated) channel.

Evidence class: SYNTHETIC_2CH_SIMULATION. The "close" channel is a mixture of a
frozen KJV clip (target) and an owner-approved competing recording at a known
target-to-interference ratio. The "room" channel is a delayed, attenuated copy
of the target plus a hotter interference copy. A least-squares delay-and-level
canceller then produces the "isolated" channel.

No real two-microphone recording exists on this machine; this harness exists to
measure, end-to-end through the real ASR, whether target-speaker isolation would
help if such capture existed.
"""
import csv
import json
import os
import sys
import wave

import numpy as np

SR = 16000
BASE = '/Users/solomonphronesis/Documents/deepseek-harness/default-workspace'
WAV = f'{BASE}/recovery_v4_work/bench/evidence/kjv40/wav'
SRC = f'{BASE}/recovery_v4_work/bench/sources'
OUT = f'{BASE}/rounds_restart/twoch'
DELAY = 48          # 3 ms room delay
LEAK_DB = 6.0       # target attenuation in the room mic


def read_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2, path
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0


def write_wav(path, x):
    y = np.clip(x, -1.0, 1.0)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


def fit(x, n):
    if len(x) >= n:
        return x[:n]
    return np.tile(x, int(np.ceil(n / len(x))))[:n]


def rms(x):
    return float(np.sqrt(np.mean(x * x))) or 1e-12


def delay(x, d):
    if d <= 0:
        return x
    return np.concatenate([np.zeros(d), x[:-d]])


def est_delay(a, b, max_lag=160):
    n = min(len(a), len(b))
    a = a[:n] - a[:n].mean()
    b = b[:n] - b[:n].mean()
    best, lag_best = -np.inf, 0
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            x, y = a[lag:], b[: n - lag]
        else:
            x, y = a[: n + lag], b[-lag:]
        if len(x) < 1000:
            continue
        c = float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-12))
        if c > best:
            best, lag_best = c, lag
    return lag_best


def cancel(close, room):
    d = est_delay(close, room)
    aligned = room[-d:] if d <= 0 else np.concatenate([np.zeros(d), room[:-d]])
    n = min(len(close), len(aligned))
    c, r = close[:n], aligned[:n]
    alpha = float(np.dot(c, r) / (np.dot(r, r) + 1e-12))
    return c - alpha * r, d, alpha


def main():
    os.makedirs(OUT, exist_ok=True)
    gold = list(csv.DictReader(open(f'{BASE}/recovery_v4_work/bench/evidence/kjv40/manifest/40_verse_gold_manifest.csv')))
    sources = {'chatter': f'{SRC}/chatter_pewbeam_16k.wav',
               'preacher2': f'{SRC}/overlap_smartverse_16k.wav'}
    rows_close, rows_canc = [], []
    for name, src in sources.items():
        interf = read_wav(src)
        for tir in (0, -5):
            for g in gold:
                cid = g['case_id']
                t = read_wav(os.path.join(WAV, os.path.basename(g['wav_path'])))
                n = len(t)
                tt = t / rms(t) * 0.08
                ii = fit(interf, n) / rms(fit(interf, n)) * 0.08
                g_close = 10 ** (-tir / 20.0)
                close = tt + g_close * ii
                room = 10 ** (-LEAK_DB / 20.0) * delay(tt, DELAY) + 10 ** (-(tir - LEAK_DB) / 20.0) * delay(ii, DELAY)
                iso, d, alpha = cancel(close, room)
                base = f"{cid}_{name}_{'m5' if tir < 0 else '0'}"
                pc = f'{OUT}/{base}_close.wav'
                pi = f'{OUT}/{base}_iso.wav'
                write_wav(pc, close)
                write_wav(pi, iso)
                rows_close.append({'file': f'{base}_close.wav', 'path': pc, 'case_id': cid,
                                   'verse_id': g['verse_id'], 'condition': f'{name}_{tir}dB', 'snr_db': tir,
                                   'src': 'synthetic close mic (target + interference)'})
                rows_canc.append({'file': f'{base}_iso.wav', 'path': pi, 'case_id': cid,
                                  'verse_id': g['verse_id'], 'condition': f'{name}_{tir}dB', 'snr_db': tir,
                                  'src': 'synthetic cancellation output'})
    for tag, rows in (('close', rows_close), ('iso', rows_canc)):
        with open(f'{OUT}/manifest_{tag}.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['file', 'path', 'case_id', 'verse_id', 'condition', 'snr_db', 'src'])
            w.writeheader()
            w.writerows(rows)
    print(json.dumps({'close_clips': len(rows_close), 'iso_clips': len(rows_canc),
                      'dir': OUT, 'delay_samples': DELAY, 'leak_db': LEAK_DB}))


if __name__ == '__main__':
    main()
