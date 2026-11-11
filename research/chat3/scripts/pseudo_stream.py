#!/usr/bin/env python3
"""Heuristic pseudo-streaming demo with the real Qwen 1.7B MLX sidecar.

Feeds cumulative audio every 640 ms / 1000 ms, decodes full-context each time,
and applies the independent stable-prefix committer. This is NOT R2T2: no LSP
training, no vLLM, no cache-aware decoding. It measures commit stability and
latency on 4 clips, not church accuracy.
"""
import csv
import glob
import json
import os
import subprocess
import sys
import time
import wave

import numpy as np

BASE = '/Users/solomonphronesis/Documents/deepseek-harness/default-workspace'
ADAPTER = f'{BASE}/RF_CHAT3_NEXT_20261110/external/qwen_mlx_adapter.sh'
OUT = f'{BASE}/rounds_restart/out'
TMP = f'{BASE}/rounds_restart/tmp_ps'
sys.path.insert(0, f'{BASE}/chat3_scorer_wt/research/chat3/scripts')
import wer as W  # noqa: E402
from stable_prefix import StablePrefix  # noqa: E402

SR = 16000


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


def write_wav(path, pcm):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def send(proc, rid, path):
    proc.stdin.write(json.dumps({'id': rid, 'wav': path, 'language': 'en'}) + '\n')
    proc.stdin.flush()
    deadline = time.time() + 30
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError('adapter closed stdout')
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get('id') != rid:
            continue
        if not obj.get('ok'):
            raise RuntimeError(obj.get('error', 'adapter error'))
        return obj['text'], obj.get('ms', 0)
    raise TimeoutError('adapter timeout')


def main():
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    clips = sorted(glob.glob(f'{BASE}/recovery_v4_work/bench/evidence/kjv40/wav/*.wav'))[:4]
    import csv as _csv
    gmap = {r['case_id']: r['gold_text'] for r in _csv.DictReader(open(f'{BASE}/recovery_v4_work/bench/evidence/kjv40/manifest/40_verse_gold_manifest.csv'))}
    rows = []
    proc = subprocess.Popen([ADAPTER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)
    try:
        ready = None
        for _ in range(200):
            line = proc.stdout.readline()
            if not line:
                break
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get('ready'):
                ready = obj
                break
        if not ready:
            raise RuntimeError('adapter never announced readiness')
        rid = 0
        for chunk_ms in (640, 1000):
            for path in clips:
                pcm = read_wav(path)
                total = len(pcm)
                step = SR * chunk_ms // 1000
                sp = StablePrefix(holdback=1, lookahead_updates=1)
                first_commit_s, commits, decodes, ms_list, last_text = None, 0, 0, [], ''
                for end in range(step, total + step, step):
                    end = min(end, total)
                    part = pcm[:end]
                    p = f'{TMP}/ps.wav'
                    write_wav(p, part)
                    rid += 1
                    text, ms = send(proc, rid, p)
                    decodes += 1
                    ms_list.append(ms)
                    last_text = text
                    try:
                        new = sp.update(text)
                    except Exception:
                        new = []
                    commits += len(new)
                    if new and first_commit_s is None:
                        first_commit_s = end / SR
                full = sp.final(last_text)
                final_text = sp.text()
                cid = os.path.basename(path)[:4]
                g = W.tokens(gmap.get(cid, ''))
                h = W.tokens(final_text)
                hfull = W.tokens(last_text)
                rows.append({
                    'clip': cid, 'chunk_ms': chunk_ms, 'updates': decodes,
                    'first_commit_s': round(first_commit_s, 2) if first_commit_s else None,
                    'committed_words': len(h), 'full_context_words': len(hfull),
                    'committed_vs_full_edits': W.edit_counts(hfull, h)[3],
                    'committed_wer_vs_gold_pct': round(100 * W.edit_counts(g, h)[3] / max(1, len(g)), 2),
                    'full_context_wer_vs_gold_pct': round(100 * W.edit_counts(g, hfull)[3] / max(1, len(g)), 2),
                    'decode_ms_p50': sorted(ms_list)[len(ms_list) // 2] if ms_list else None,
                })
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.kill()
    with open(f'{OUT}/pseudo_stream.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    for r in rows:
        print(r)


if __name__ == '__main__':
    main()
