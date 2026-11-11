#!/usr/bin/env python3
"""Word error rate between a JSONL transcript file and a CSV gold table.

usage: wer.py <gold.csv with case_id,gold_text> <transcript.jsonl>
"""
import csv
import json
import re
import sys


def tokens(s):
    s = s.lower().replace('\u2019', "'")
    return [t for t in re.split(r"[^a-z0-9' ]+", s) if t]


def edits(a, b):
    n, m = len(a), len(b)
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, m + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return dp[m]


def main():
    gold = {r['case_id']: r['gold_text'] for r in csv.DictReader(open(sys.argv[1]))}
    ref = err = n = 0
    for line in open(sys.argv[2]):
        r = json.loads(line)
        if r.get('type') == 'batch_header':
            continue
        cid = r['file'].split('/')[-1][:4]
        g = tokens(gold.get(cid, ''))
        if not g:
            continue
        ref += len(g)
        err += edits(g, tokens(r['text']))
        n += 1
    print(json.dumps({'clips': n, 'ref_words': ref, 'edits': err,
                      'wer_pct': round(100 * err / ref, 2) if ref else None}))


if __name__ == '__main__':
    main()
