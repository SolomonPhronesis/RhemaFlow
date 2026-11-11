#!/usr/bin/env python3
"""Causal (past-only) two-channel isolation baselines on the synthetic set.

Methods
-------
A close       : close microphone alone (reference)
B room        : room microphone alone
C naive_mix   : 0.5 * (close + room)
D causal_nlms : delay estimated from the first 320 ms only, then a scalar gain
                updated per 20 ms block from PAST samples only (α_{k+1} from e_k, r_k);
                output e_k = c_k - α_k * r_k
E oracle_ls   : the non-causal whole-clip least-squares result already measured
                (reference ceiling, not produced here)

Also builds a clean-audio degradation set and a reverberation + gain-drift set.
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
OUT = f'{BASE}/rounds_restart/causal'
DELAY = 48
LEAK_DB = 6.0
BLOCK = 320          # 20 ms
MU = 0.5
CAL_MS = 320


def read_wav(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2, path
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0


def write_wav(path, x):
    y = np.clip(x, -1.0, 1.0)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


def fit(x, n):
    return x[:n] if len(x) >= n else np.tile(x, int(np.ceil(n / len(x))))[:n]


def rms(x):
    return float(np.sqrt(np.mean(x * x))) or 1e-12


def delay(x, d):
    return x if d <= 0 else np.concatenate([np.zeros(d), x[:-d]])


def est_delay(a, b, max_lag=160):
    n = min(len(a), len(b))
    a = a[:n] - a[:n].mean(); b = b[:n] - b[:n].mean()
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


def align(room, lag):
    return room[-lag:] if lag <= 0 else np.concatenate([np.zeros(lag), room[:-lag]])


def causal_nlms(close, room, block=BLOCK, mu=MU, cal_ms=CAL_MS, adapt_gate=True, alpha_max=1.2):
    """Past-only scalar NLMS with an interference-dominance adaptation gate.

    α is updated only on blocks where the room channel is louder than the close
    channel (interference-dominant), which prevents the canceller from adapting
    to a room mic that contains only the target. Output uses α from previous
    blocks, so the algorithm is strictly causal.
    """
    import time
    cal = SR * cal_ms // 1000
    lag = est_delay(close[:cal], room[:cal])
    r = align(room, lag)
    n = min(len(close), len(r))
    c, r = close[:n], r[:n]
    out = np.empty(n)
    alpha = 0.0
    t0 = time.perf_counter()
    blocks = 0
    for s in range(0, n, block):
        e_end = min(s + block, n)
        cb, rb = c[s:e_end], r[s:e_end]
        out[s:e_end] = cb - alpha * rb
        e = out[s:e_end]
        allow = (not adapt_gate) or (float(np.sqrt(np.mean(rb * rb))) > float(np.sqrt(np.mean(cb * cb))))
        if allow:
            denom = float(np.dot(rb, rb)) + 1e-9
            alpha = float(np.clip(alpha + mu * float(np.dot(e, rb)) / denom, 0.0, alpha_max))
        blocks += 1
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return out, lag, elapsed_ms / max(1, blocks)


def reverb_room(t, i, delay_samples, leak_db, rt60_ms=120):
    """Simple exponential-decay room response applied to the room mic."""
    ir_len = int(SR * rt60_ms / 1000)
    ir = np.exp(-np.arange(ir_len) / (ir_len / 4.0))
    ir /= ir.sum()
    mix = 10 ** (-leak_db / 20.0) * delay(t, delay_samples) + 10 ** (-(0 - leak_db) / 20.0) * delay(i, delay_samples)
    return np.convolve(mix, ir, mode='same')


def main(mode):
    os.makedirs(OUT, exist_ok=True)
    gold = list(csv.DictReader(open(f'{BASE}/recovery_v4_work/bench/evidence/kjv40/manifest/40_verse_gold_manifest.csv')))
    sources = {'chatter': f'{SRC}/chatter_pewbeam_16k.wav', 'preacher2': f'{SRC}/overlap_smartverse_16k.wav'}
    manifests = {m: [] for m in ('close', 'room', 'mix', 'causal', 'causal_clean', 'causal_reverb')}
    rows = []
    for name, src in sources.items():
        interf = read_wav(src)
        for tir in (0, -5):
            for g in gold:
                cid = g['case_id']
                t = read_wav(os.path.join(WAV, os.path.basename(g['wav_path'])))
                n = len(t)
                tt = t / rms(t) * 0.08
                ii_raw = fit(interf, n)
                ii = ii_raw / rms(ii_raw) * 0.08
                close = tt + 10 ** (-tir / 20.0) * ii
                room = 10 ** (-LEAK_DB / 20.0) * delay(tt, DELAY) + 10 ** (-(tir - LEAK_DB) / 20.0) * delay(ii, DELAY)
                mix = 0.5 * (close + room)
                causal, lag, block_ms = causal_nlms(close, room)
                base = f"{cid}_{name}_{'m5' if tir < 0 else '0'}"
                for tag, sig in (('close', close), ('room', room), ('mix', mix), ('causal', causal)):
                    p = f'{OUT}/{base}_{tag}.wav'
                    write_wav(p, sig)
                    manifests[tag].append({'file': f'{base}_{tag}.wav', 'path': p, 'case_id': cid,
                                           'verse_id': g['verse_id'], 'condition': f'{name}_{tir}dB', 'snr_db': tir,
                                           'src': f'{tag} (synthetic 2ch)'})
                rows.append({'case_id': cid, 'source': name, 'tir_db': tir, 'delay_est': lag,
                             'block_ms': round(block_ms, 4)})
    # clean degradation: no interference in either channel
    for g in gold:
        cid = g['case_id']
        t = read_wav(os.path.join(WAV, os.path.basename(g['wav_path'])))
        tt = t / rms(t) * 0.08
        close = tt
        room = 10 ** (-LEAK_DB / 20.0) * delay(tt, DELAY)
        causal, lag, _ = causal_nlms(close, room)
        p = f'{OUT}/{cid}_clean_causal.wav'
        write_wav(p, causal)
        manifests['causal_clean'].append({'file': f'{cid}_clean_causal.wav', 'path': p, 'case_id': cid,
                                          'verse_id': g['verse_id'], 'condition': 'clean', 'snr_db': 'inf',
                                          'src': 'causal on clean 2ch'})
    # reverb + drift robustness
    for g in gold:
        cid = g['case_id']
        t = read_wav(os.path.join(WAV, os.path.basename(g['wav_path'])))
        n = len(t)
        tt = t / rms(t) * 0.08
        ii_raw = fit(read_wav(f'{SRC}/overlap_smartverse_16k.wav'), n)
        ii = ii_raw / rms(ii_raw) * 0.08
        close = tt + ii
        room = reverb_room(tt, ii, DELAY, LEAK_DB)
        drift = 10 ** (1.0 * np.sin(2 * np.pi * 0.3 * np.arange(n) / SR) / 20.0)
        room = room * drift
        causal, lag, _ = causal_nlms(close, room)
        p = f'{OUT}/{cid}_reverb_causal.wav'
        write_wav(p, causal)
        manifests['causal_reverb'].append({'file': f'{cid}_reverb_causal.wav', 'path': p, 'case_id': cid,
                                           'verse_id': g['verse_id'], 'condition': 'reverb_drift', 'snr_db': 0,
                                           'src': 'causal on reverb+drift room'})
    for tag, rows_m in manifests.items():
        with open(f'{OUT}/manifest_{tag}.csv', 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['file', 'path', 'case_id', 'verse_id', 'condition', 'snr_db', 'src'])
            w.writeheader(); w.writerows(rows_m)
    with open(f'{OUT}/causal_delays.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(json.dumps({'manifests': {k: len(v) for k, v in manifests.items()},
                      'dir': OUT}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'build')
