#!/usr/bin/env python3
"""Synthetic two-channel speaker-isolation study (signal level only, no ASR).

This is a SIMULATION with known components. It answers a narrow question:
*if* a close pastor mic and a room mic existed, how much interference rejection
and target distortion would simple selection / delay-and-level cancellation
produce, and how well would an energy-based overlap detector separate the two?

It is NOT a recorded two-microphone result and NOT a church-accuracy claim.
"""
from __future__ import annotations

import csv
import sys
import wave

import numpy as np

SR = 16000


def read_wav(path):
    with wave.open(path) as w:
        if w.getframerate() != SR or w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError(f"expected 16 kHz mono s16: {path}")
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0


def fit(x, n):
    if len(x) >= n:
        return x[:n]
    reps = int(np.ceil(n / len(x)))
    return np.tile(x, reps)[:n]


def delay(x, d):
    d = int(d)
    if d <= 0:
        return x
    return np.concatenate([np.zeros(d), x[:-d]])


def rms(x):
    return float(np.sqrt(np.mean(x * x))) or 1e-12


def mix_pair(target, interf, tir_db, leak_db, delay_room, delay_close):
    """Return (close, room, target_aligned) for a given target-to-interference ratio."""
    n = len(target)
    t = target / rms(target) * 0.08
    i = fit(interf, n)
    i = i / rms(i) * 0.08
    g_close = 10 ** (-tir_db / 20.0)          # interference relative to target in close mic
    g_room_i = 10 ** (-(tir_db - leak_db) / 20.0)  # room mic interference
    g_room_t = 10 ** (-leak_db / 20.0)        # target attenuated in room mic
    close = t + g_close * delay(i, delay_close)
    room = g_room_t * delay(t, delay_room) + g_room_i * delay(i, delay_room)
    return close, room, delay(t, 0)


def est_delay(a, b, max_lag=160):
    """Cross-correlation delay estimate (b relative to a), bounded."""
    n = min(len(a), len(b))
    a = a[:n] - a[:n].mean()
    b = b[:n] - b[:n].mean()
    best, best_lag = -np.inf, 0
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            x, y = a[lag:], b[: n - lag]
        else:
            x, y = a[: n + lag], b[-lag:]
        if len(x) < 1000:
            continue
        c = float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-12))
        if c > best:
            best, best_lag = c, lag
    return best_lag


def cancel(close, room, delay_est, mu=1.0):
    """Delay-and-level cancellation: subtract mu * (room aligned to close).

    `est_delay` returns negative values when the room channel lags the close
    channel, so the room must be advanced by `-delay_est` samples.
    """
    if delay_est <= 0:
        aligned = room[-delay_est:]
    else:
        aligned = np.concatenate([np.zeros(delay_est), room[:-delay_est]])
    n = min(len(close), len(aligned))
    c, r = close[:n], aligned[:n]
    alpha = mu * float(np.dot(c, r) / (np.dot(r, r) + 1e-12))
    return c - alpha * r


def sir_db(out, target_aligned, interference):
    """SIR of the output using the known components (oracle metric)."""
    n = min(len(out), len(target_aligned), len(interference))
    t = target_aligned[:n]
    i = interference[:n]
    # project out target and interference contributions from the output
    t_energy = float(np.dot(t, t))
    i_energy = float(np.dot(i, i))
    if t_energy == 0 or i_energy == 0:
        return 0.0
    # least-squares decomposition of the output onto [t, i]
    a = np.vstack([t, i]).T
    coef, *_ = np.linalg.lstsq(a, out[:n], rcond=None)
    t_comp, i_comp = coef[0] * t, coef[1] * i
    return 10 * np.log10((float(np.dot(t_comp, t_comp)) + 1e-12) / (float(np.dot(i_comp, i_comp)) + 1e-12))


def frame_overlap_labels(interference, target, frame=800, thr_db=-20.0):
    n = min(len(interference), len(target))
    nf = n // frame
    labels = []
    for k in range(nf):
        seg_i = interference[k * frame:(k + 1) * frame]
        seg_t = target[k * frame:(k + 1) * frame]
        ratio = 20 * np.log10((rms(seg_i) + 1e-12) / (rms(seg_t) + 1e-12))
        labels.append(1 if ratio > thr_db else 0)
    return np.array(labels)


def frame_scores(close, room, frame=800):
    """Energy-ratio overlap score per frame: positive means room is interference-dominant."""
    n = min(len(close), len(room))
    nf = n // frame
    scores = []
    for k in range(nf):
        c = rms(close[k * frame:(k + 1) * frame])
        r = rms(room[k * frame:(k + 1) * frame])
        scores.append(20 * np.log10((r + 1e-12) / (c + 1e-12)))
    return np.array(scores)


def roc_auc(scores, labels):
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    auc = 0.0
    for p in pos:
        auc += float(np.mean(p > neg)) + 0.5 * float(np.mean(p == neg))
    return auc / len(pos)


def main(targets, sources, out_path):
    rows = []
    for name, src in sources.items():
        interf = read_wav(src)
        for tir in (0.0, -5.0):
            sir_improvements, distortions, target_loss, retention = [], [], [], []
            aucs = []
            for path in targets:
                target = read_wav(path)
                close, room, tgt = mix_pair(target, interf, tir_db=tir, leak_db=6.0,
                                            delay_room=48, delay_close=0)
                n = len(close)
                i_aligned = fit(interf, n)
                sir_in = sir_db(close, tgt, i_aligned)
                d = est_delay(close, room)
                out = cancel(close, room, d)
                sir_out = sir_db(out, tgt, i_aligned)
                sir_improvements.append(sir_out - sir_in)
                # target distortion: residual target energy relative to the close mic
                k = min(len(out), len(close))
                ratio = np.dot(out[:k], close[:k]) / (np.dot(close[:k], close[:k]) + 1e-12)
                residual = out[:k] - ratio * close[:k]
                distortions.append(10 * np.log10((np.dot(residual, residual) + 1e-12) /
                                                  (np.dot(close[:k], close[:k]) + 1e-12)))
                # target retention per frame, measured on the KNOWN target component
                frame = 800
                nf = k // frame
                lost = 0
                t_known = tgt[:k]
                for fi in range(nf):
                    seg_t = t_known[fi * frame:(fi + 1) * frame]
                    e = float(np.dot(seg_t, seg_t))
                    if e < 1e-9:
                        continue
                    a_out = float(np.dot(out[fi * frame:(fi + 1) * frame], seg_t)) / e
                    a_close = float(np.dot(close[fi * frame:(fi + 1) * frame], seg_t)) / e
                    if a_close > 1e-6 and 20 * np.log10((abs(a_out) + 1e-12) / a_close) < -6:
                        lost += 1
                target_loss.append(lost / max(1, nf))
                a_out_all = float(np.dot(out[:k], t_known)) / (float(np.dot(t_known, t_known)) + 1e-12)
                a_close_all = float(np.dot(close[:k], t_known)) / (float(np.dot(t_known, t_known)) + 1e-12)
                retention.append(20 * np.log10((abs(a_out_all) + 1e-12) / (abs(a_close_all) + 1e-12)))
                labels = frame_overlap_labels(i_aligned, tgt)
                scores = frame_scores(close, room)
                m = min(len(labels), len(scores))
                auc = roc_auc(scores[:m], labels[:m])
                if auc is not None:
                    aucs.append(auc)
            rows.append({
                'source': name, 'target_to_interference_db': tir,
                'clips': len(targets),
                'mean_delta_sir_db': round(float(np.mean(sir_improvements)), 2),
                'mean_residual_vs_close_db': round(float(np.mean(distortions)), 2),
                'mean_target_retention_db': round(float(np.mean(retention)), 2),
                'mean_target_frames_lost_pct': round(100 * float(np.mean(target_loss)), 2),
                'overlap_auc': round(float(np.mean(aucs)), 3) if aucs else 'NA',
            })
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)
    return rows


if __name__ == '__main__':
    import glob
    base = sys.argv[1]
    targets = sorted(glob.glob(f'{base}/recovery_v4_work/bench/evidence/kjv40/wav/*.wav'))[:8]
    sources = {
        'chatter': f'{base}/recovery_v4_work/bench/sources/chatter_pewbeam_16k.wav',
        'preacher2': f'{base}/recovery_v4_work/bench/sources/overlap_smartverse_16k.wav',
    }
    main(targets, sources, f'{base}/chat3_scorer_wt/research/chat3/data/two_channel_sim.csv')
