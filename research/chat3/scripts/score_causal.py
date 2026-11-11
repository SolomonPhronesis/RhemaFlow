#!/usr/bin/env python3
"""Score causal isolation variants and compute paired bootstrap CIs."""
import csv
import json
import random
import re
import sys
from collections import defaultdict

sys.path.insert(0, '/Users/solomonphronesis/Documents/deepseek-harness/default-workspace/chat3_scorer_wt/research/chat3/scripts')
import wer as W

random.seed(20261111)
BASE = '/Users/solomonphronesis/Documents/deepseek-harness/default-workspace'
gold = {r['case_id']: r['gold_text'] for r in csv.DictReader(open(f'{BASE}/rounds_restart/twoch/gold.csv'))}


def load(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def score(rows):
    per = defaultdict(lambda: {'n': 0, 'ref': 0, 'edits': 0, 'intrusion': 0})
    for r in rows:
        g = W.tokens(gold[r['case_id']])
        h = W.tokens(r.get('text') or '')
        c = per[r['condition']]
        c['n'] += 1; c['ref'] += len(g); c['edits'] += W.edit_counts(g, h)[3]
        gs = set(g)
        c['intrusion'] += sum(1 for w in h if w not in gs)
    return per


def agg(per, conds=None):
    ref = ed = intr = 0
    for k, c in per.items():
        if conds and k not in conds:
            continue
        ref += c['ref']; ed += c['edits']; intr += c['intrusion']
    return {'ref': ref, 'edits': ed, 'wer': round(100 * ed / ref, 3) if ref else None,
            'intrusion_per_100': round(100 * intr / ref, 2) if ref else None}


def bootstrap(close_rows, causal_rows, n=2000):
    """Paired bootstrap over clips: WER(close) - WER(causal)."""
    cidx = {r['case_id'] + '|' + r['condition']: r for r in close_rows}
    pairs = []
    for r in causal_rows:
        k = r['case_id'] + '|' + r['condition']
        if k not in cidx:
            continue
        g = W.tokens(gold[r['case_id']])
        hc = W.tokens(cidx[k].get('text') or '')
        hi = W.tokens(r.get('text') or '')
        pairs.append((len(g), W.edit_counts(g, hc)[3], W.edit_counts(g, hi)[3]))
    diffs = []
    for _ in range(n):
        s = [pairs[random.randrange(len(pairs))] for _ in range(len(pairs))]
        ref = sum(x[0] for x in s)
        ec = sum(x[1] for x in s); ei = sum(x[2] for x in s)
        if ref:
            diffs.append(100 * (ec - ei) / ref)
    diffs.sort()
    return round(diffs[int(0.025 * len(diffs))], 2), round(diffs[int(0.975 * len(diffs))], 2)


close_rows = load(f'{BASE}/rounds_restart/raw/b0_close.jsonl')
oracle_rows = load(f'{BASE}/rounds_restart/raw/b0_iso.jsonl')
variant_rows = {m: load(f'{BASE}/rounds_restart/raw/b0_{m}.jsonl') for m in ('room', 'mix', 'causal')}

rows = []
for name, per in [('close', score(close_rows)), ('oracle_ls', score(oracle_rows))] + [(m, score(r)) for m, r in variant_rows.items()]:
    a = agg(per)
    rows.append({'method': name, 'clips': sum(c['n'] for c in per.values()), **a})
with open(f'{BASE}/rounds_restart/out/causal_aggregate.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

detail = []
for name, per in [('close', score(close_rows)), ('oracle_ls', score(oracle_rows))] + [(m, score(r)) for m, r in variant_rows.items()]:
    for cond, c in sorted(per.items()):
        detail.append({'method': name, 'condition': cond, 'clips': c['n'], 'ref_words': c['ref'],
                       'wer_pct': round(100 * c['edits'] / c['ref'], 3), 'intrusion_per_100': round(100 * c['intrusion'] / c['ref'], 2)})
with open(f'{BASE}/rounds_restart/out/causal_detail.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(detail[0])); w.writeheader(); w.writerows(detail)

cis = {}
for m in ('room', 'mix', 'causal'):
    cis[m] = bootstrap(close_rows, variant_rows[m])
cis['oracle_ls'] = bootstrap(close_rows, oracle_rows)
with open(f'{BASE}/rounds_restart/out/causal_ci.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['method', 'delta_pp_close_minus_method', 'ci_low', 'ci_high'])
    for m, (lo, hi) in cis.items():
        w.writerow([m, round(100 * (agg(score(close_rows))['wer'] - agg(score(variant_rows[m] if m in variant_rows else oracle_rows))['wer']), 3), lo, hi])

# clean degradation + reverb
clean_causal = load(f'{BASE}/rounds_restart/raw/b0_causal_clean.jsonl')
reverb = load(f'{BASE}/rounds_restart/raw/b0_causal_reverb.jsonl')
close_preacher0 = [r for r in close_rows if r['condition'] == 'preacher2_0dB']
clean_ref = score(clean_causal)
rev_ref = score(reverb)
clean_close = agg(score(close_preacher0))
print('clean causal WER', agg(clean_ref))
print('reverb causal WER', agg(rev_ref), 'close(preacher 0dB) WER', clean_close)
with open(f'{BASE}/rounds_restart/out/causal_robustness.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['set', 'clips', 'ref_words', 'wer_pct'])
    w.writerow(['causal_clean', 40, agg(clean_ref)['ref'], agg(clean_ref)['wer']])
    w.writerow(['close_preacher_0dB(reference for reverb)', 40, clean_close['ref'], clean_close['wer']])
    w.writerow(['causal_reverb_drift', 40, agg(rev_ref)['ref'], agg(rev_ref)['wer']])

for r in rows:
    print(r)
print('CI', cis)
