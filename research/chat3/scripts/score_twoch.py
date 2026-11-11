#!/usr/bin/env python3
"""Score close-mic vs isolated-channel WER on the synthetic two-channel set."""
import csv, json, re, sys
from collections import defaultdict
sys.path.insert(0, '/Users/solomonphronesis/Documents/deepseek-harness/default-workspace/chat3_scorer_wt/research/chat3/scripts')
import wer as W

def norm(s): return W.tokens(s, 'normalise')

def load(path):
    return [json.loads(l) for l in open(path) if l.strip()]

gold = {r['case_id']: r['gold_text'] for r in csv.DictReader(open('rounds_restart/twoch/gold.csv'))}

def score(rows):
    per = defaultdict(lambda: {'ref': 0, 'edits': 0, 'n': 0, 'hyp': 0, 'intrusion': 0})
    for r in rows:
        g = norm(gold[r['case_id']])
        h = norm(r.get('text') or '')
        s, d, i, dist = W.edit_counts(g, h)
        c = per[r['condition']]
        c['ref'] += len(g); c['edits'] += dist; c['n'] += 1; c['hyp'] += len(h)
        gs = set(g)
        c['intrusion'] += sum(1 for w in h if w not in gs)
    out = {}
    for k, c in per.items():
        out[k] = {'n': c['n'], 'ref': c['ref'], 'edits': c['edits'],
                  'wer': round(100 * c['edits'] / c['ref'], 3) if c['ref'] else None,
                  'intrusion_words': c['intrusion'],
                  'intrusion_per_100': round(100 * c['intrusion'] / c['ref'], 2) if c['ref'] else None}
    return out

close = score(load('rounds_restart/raw/b0_close.jsonl'))
iso = score(load('rounds_restart/raw/b0_iso.jsonl'))
rows = []
for cond in sorted(close):
    c, i = close[cond], iso.get(cond, {})
    rows.append({'condition': cond, 'clips': c['n'], 'ref_words': c['ref'],
                 'close_wer': c['wer'], 'iso_wer': i.get('wer'),
                 'delta_pp': round(i.get('wer', 0) - c['wer'], 3) if c['wer'] is not None else None,
                 'close_intrusion_per_100': c['intrusion_per_100'],
                 'iso_intrusion_per_100': i.get('intrusion_per_100')})
with open('rounds_restart/out/twoch_wer.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
