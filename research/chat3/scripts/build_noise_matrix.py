#!/usr/bin/env python3
"""Frozen music/chatter/speaker matrix.

SNR convention: SNR = target speech level relative to the interference level
(negative dB means the interference is louder than the target).
"""
import csv
import hashlib
import math
import os
import wave
from array import array

import os
BASE = os.environ.get('RF_BASE', '/Users/solomonphronesis/Documents/deepseek-harness/default-workspace')
EVID = f'{BASE}/recovery_v4_work/bench/evidence/kjv40'
SRC = f'{BASE}/recovery_v4_work/bench/sources'
OUT = f'{BASE}/matrix_work/audio'
os.makedirs(OUT, exist_ok=True)


def read(p):
    with wave.open(p) as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1 and w.getsampwidth() == 2
        return array('h', w.readframes(w.getnframes()))


def write(p, samples):
    with wave.open(p, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(samples.tobytes())


def rms(a):
    return math.sqrt(sum(float(x) * x for x in a) / max(1, len(a))) or 1.0


def fit(src, n):
    if len(src) >= n:
        return src[:n]
    reps = (n // len(src)) + 1
    return (src * reps)[:n]


def mix(target, interf, snr_db, level=0.08 * 32768.0):
    """Interference RMS = `level` int16 units; target RMS = level*10^(snr/20).

    `level` is expressed in 16-bit sample units (0.08 full scale = 2621).
    """
    n = len(target)
    i = fit(interf, n)
    si = level / rms(i)
    st = (level * (10 ** (snr_db / 20.0))) / rms(target)
    out = array('h', bytes(2 * n))
    peak = 1.0
    for k in range(n):
        v = target[k] * st + i[k] * si
        out[k] = int(max(-32000, min(32000, v)))
        peak = max(peak, abs(out[k]) / 32768.0)
    if peak > 0.95:
        g = 0.95 / peak
        for k in range(n):
            out[k] = int(out[k] * g)
    return out


gold = list(csv.DictReader(open(f'{EVID}/manifest/40_verse_gold_manifest.csv')))
music = read(f'{SRC}/music_freely_16k.wav')
chatter = read(f'{SRC}/chatter_pewbeam_16k.wav')
overlap = read(f'{SRC}/overlap_smartverse_16k.wav')
rows = []


def add(case, verse, cond, snr, data, gold_text, src):
    name = f'{case}_{cond}.wav'
    p = f'{OUT}/{name}'
    write(p, data)
    rows.append({'file': name, 'path': p, 'case_id': case, 'verse_id': verse or '',
                 'condition': cond, 'snr_db': snr, 'src': src,
                 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest(),
                 'duration_s': f'{len(data)/16000:.3f}', 'gold_text': gold_text,
                 'has_target': 'yes' if gold_text else 'no'})


for g in gold:
    t = read(f"{EVID}/{g['wav_path']}")
    cid, gt, vid = g['case_id'], g['gold_text'], g['verse_id']
    add(cid, vid, 'clean', 'inf', t, gt, 'kjv target only')
    add(cid, vid, 'music_only', '-inf', fit(music, len(t)), '', 'music only, no target')
    add(cid, vid, 'chatter_only', '-inf', fit(chatter, len(t)), '', 'chatter only, no target')
    for snr, tag in ((-5, 'm5'), (0, '0'), (5, 'p5'), (10, 'p10')):
        add(cid, vid, f'music_{tag}', str(snr), mix(t, music, snr), gt, f'target + music at {snr} dB SNR')
        add(cid, vid, f'chatter_{tag}', str(snr), mix(t, chatter, snr), gt, f'target + chatter at {snr} dB SNR')
        add(cid, vid, f'overlap_{tag}', str(snr), mix(t, overlap, snr), gt, f'target + second preacher at {snr} dB SNR')
    mixed = mix(t, music, 0)
    mixed = mix(mixed, chatter, 0)
    add(cid, vid, 'mixed_0', '0', mixed, gt, 'target + music + chatter, each at 0 dB')

for i in range(8):
    add(f'S{i+1:02d}', '', 'silence', '-inf', array('h', bytes(2 * 16000 * 8)), '', 'digital silence')

with open(f'{BASE}/matrix_work/out/data/matrix_manifest.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
with open(f'{BASE}/matrix_work/out/data/matrix_fixtures.csv', 'w', newline='') as f:
    fields = ['file', 'path', 'case_id', 'verse_id', 'condition', 'snr_db', 'src', 'sha256', 'duration_s']
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow({k: r[k] for k in fields})
print('clips', len(rows))
