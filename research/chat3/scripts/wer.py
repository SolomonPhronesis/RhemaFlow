#!/usr/bin/env python3
"""Word error rate scorer (v2) with explicit ids, coverage and fail-closed policies.

Changed from v1: tokenisation now splits on whitespace after mapping punctuation
to spaces (v1's `re.split(r"[^a-z0-9' ]+", s)` kept whole phrases as one token).
See SCORER_AUDIT.md for the defect, the fixture tests and the provenance verdict.

usage:
    wer.py --gold gold.csv --jsonl out.jsonl [--manifest fixtures.csv]
           [--mode normalise|verbatim] [--json]

gold.csv      : case_id,gold_text  (required)
jsonl         : one JSON object per line; requires `case_id`, or `file` plus --manifest
manifest.csv  : file,case_id       (maps transcript basenames to gold ids)
mode          : normalise (default; lowercase, punctuation -> space, keep apostrophes)
                verbatim  (lowercase + apostrophe folding only, punctuation kept)
"""
import argparse
import csv
import json
import re
import sys


def tokens(text, mode='normalise'):
    s = text.lower().replace('\u2019', "'")
    if mode == 'normalise':
        s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return [t for t in s.split() if t]


def edit_counts(ref, hyp):
    """Levenshtein distance plus explicit S/D/I counts (minimal alignment)."""
    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    sub = dele = ins = 0
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == hyp[j - 1]:
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            sub += 1
            i, j = i - 1, j - 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            dele += 1
            i -= 1
        else:
            ins += 1
            j -= 1
    return sub, dele, ins, dp[n][m]


def read_gold(path):
    gold = {}
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            cid = (row.get('case_id') or '').strip()
            if not cid:
                raise SystemExit(f'gold row without case_id: {row}')
            text = row.get('gold_text') or ''
            if cid not in gold:
                gold[cid] = text
            elif text and gold[cid] and text != gold[cid]:
                raise SystemExit(f'conflicting gold text for case_id {cid}')
            elif text and not gold[cid]:
                gold[cid] = text
    if not gold:
        raise SystemExit('empty gold table')
    return gold


def read_manifest(path):
    mapping = {}
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            fn = (row.get('file') or '').strip()
            cid = (row.get('case_id') or '').strip()
            if not fn or not cid:
                raise SystemExit(f'manifest row missing file/case_id: {row}')
            if fn in mapping and mapping[fn] != cid:
                raise SystemExit(f'manifest maps {fn} twice')
            mapping[fn] = cid
    return mapping


def load_rows(path, manifest, key_fields=('case_id',)):
    rows, seen = [], set()
    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise SystemExit(f'{path}:{lineno}: invalid JSON ({e})')
            if obj.get('type') == 'batch_header':
                continue
            cid = obj.get('case_id')
            if not cid:
                name = (obj.get('file') or '').split('/')[-1]
                cid = manifest.get(name)
                if not cid:
                    raise SystemExit(f'{path}:{lineno}: no case_id and no manifest match for {name!r}')
            identity = tuple(str(obj.get(f) or '') for f in key_fields) if len(key_fields) > 1 else (cid,)
            if identity in seen:
                raise SystemExit(f'{path}:{lineno}: duplicate transcript for key {identity}')
            seen.add(identity)
            rows.append({'case_id': cid, 'text': obj.get('text') or '',
                         'condition': obj.get('condition') or ''})
    if not rows:
        raise SystemExit('no transcript rows')
    return rows


def score(rows, gold, mode='normalise', exclude_conditions=()):
    totals = {'n_rows': len(rows), 'n_used': 0, 'n_missing_gold': 0, 'n_empty_ref': 0,
              'hyp_words_on_empty_ref': 0, 'n_ref_words': 0, 'n_hyp_words': 0,
              'substitutions': 0, 'deletions': 0, 'insertions': 0, 'edits': 0}
    per_condition = {}
    excluded = set(exclude_conditions)
    for r in rows:
        if r['condition'] in excluded:
            continue
        if r['case_id'] not in gold:
            totals['n_missing_gold'] += 1
            continue
        ref = tokens(gold[r['case_id']], mode)
        hyp = tokens(r['text'], mode)
        if not ref:
            # no reference for this clip (e.g. music-only control): report the
            # false-speech volume, never mix it into the WER denominator
            totals['n_empty_ref'] += 1
            totals['hyp_words_on_empty_ref'] += len(hyp)
            continue
        s, d, i, dist = edit_counts(ref, hyp)
        assert s + d + i == dist, (s, d, i, dist)
        totals['n_used'] += 1
        totals['n_ref_words'] += len(ref)
        totals['n_hyp_words'] += len(hyp)
        totals['substitutions'] += s
        totals['deletions'] += d
        totals['insertions'] += i
        totals['edits'] += dist
        c = per_condition.setdefault(r['condition'] or 'all',
                                     {'n': 0, 'ref_words': 0, 'edits': 0})
        c['n'] += 1
        c['ref_words'] += len(ref)
        c['edits'] += dist
    totals['wer_pct'] = round(100.0 * totals['edits'] / totals['n_ref_words'], 4) if totals['n_ref_words'] else None
    totals['coverage_pct'] = round(100.0 * totals['n_used'] / totals['n_rows'], 2) if totals['n_rows'] else 0.0
    for name, c in per_condition.items():
        c['wer_pct'] = round(100.0 * c['edits'] / c['ref_words'], 4) if c['ref_words'] else None
    totals['per_condition'] = per_condition
    return totals


def main(argv=None):
    ap = argparse.ArgumentParser(description='WER scorer with explicit ids and coverage')
    ap.add_argument('--gold', required=True)
    ap.add_argument('--jsonl', required=True)
    ap.add_argument('--manifest')
    ap.add_argument('--mode', choices=['normalise', 'verbatim'], default='normalise')
    ap.add_argument('--key', default='case_id',
                    help='comma-separated JSONL fields that identify a row (default case_id; '
                         'use case_id,condition when one case appears in several conditions)')
    ap.add_argument('--fail-on-missing-gold', action='store_true', default=True)
    ap.add_argument('--exclude-conditions', default='',
                    help='comma-separated conditions to skip (e.g. music_only,chatter_only,silence)')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)

    gold = read_gold(args.gold)
    manifest = read_manifest(args.manifest) if args.manifest else {}
    rows = load_rows(args.jsonl, manifest, tuple(args.key.split(',')))
    exclude = tuple(c.strip() for c in args.exclude_conditions.split(',') if c.strip())
    result = score(rows, gold, args.mode, exclude)
    if args.fail_on_missing_gold and result['n_missing_gold']:
        result['error'] = 'missing gold rows (fail-closed)'
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"ERROR: {result['n_missing_gold']} transcripts have no gold row")
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"rows {result['n_rows']} used {result['n_used']} coverage {result['coverage_pct']}% "
              f"ref_words {result['n_ref_words']} S/D/I {result['substitutions']}/"
              f"{result['deletions']}/{result['insertions']} WER {result['wer_pct']}%")
        for name, c in sorted(result['per_condition'].items()):
            print(f"  {name:16s} n={c['n']:3d} ref={c['ref_words']:5d} WER={c['wer_pct']}%")
    return 0


if __name__ == '__main__':
    sys.exit(main())
