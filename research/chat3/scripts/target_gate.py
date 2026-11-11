#!/usr/bin/env python3
"""Target-speaker / card gate policy evaluator (model-free).

Answers one question from saved evidence: for a candidate gate, how many *correct*
Scripture cards survive, how many *wrong* cards are removed, and what happens to
recall? It never looks at audio and never runs a model.

usage:
    target_gate.py --jsonl raw.jsonl [--key-ref card_ref --key-verse verse_id]
                   [--thresholds 0,0.5,0.7,0.8,0.9]
"""
import argparse
import csv
import json
import sys


def classify(rec):
    kind = (rec.get('card_kind') or '').upper()
    ref = rec.get('card_ref')
    verse = rec.get('verse_id')
    if kind in ('', 'NONE', 'NO_CARD'):
        return 'none'
    if kind == 'REVIEW':
        return 'review'
    if ref and verse and ref == verse:
        return 'correct'
    if ref:
        return 'wrong'
    return 'review'


def gate_metrics(records, threshold=None):
    """Apply an optional confidence gate, then count card outcomes."""
    out = {'cards_seen': 0, 'kept': 0, 'correct': 0, 'wrong': 0, 'review': 0, 'none': 0,
           'correct_lost': 0, 'wrong_removed': 0}
    total_correct = total_wrong = 0
    for r in records:
        outcome = classify(r)
        conf = r.get('card_confidence')
        conf = 0.0 if conf is None else float(conf)
        if outcome == 'correct':
            total_correct += 1
        elif outcome == 'wrong':
            total_wrong += 1
        if outcome in ('correct', 'wrong'):
            out['cards_seen'] += 1
            if threshold is not None and conf < threshold:
                if outcome == 'correct':
                    out['correct_lost'] += 1
                else:
                    out['wrong_removed'] += 1
                continue
            out['kept'] += 1
            out[outcome] += 1
        else:
            out[outcome] += 1
    out['recall'] = round(out['correct'] / total_correct, 4) if total_correct else None
    out['precision'] = round(out['correct'] / out['kept'], 4) if out['kept'] else None
    out['total_correct'] = total_correct
    out['total_wrong'] = total_wrong
    return out


def sweep(records, thresholds):
    return [dict(threshold=t, **gate_metrics(records, t)) for t in thresholds]


def load_rows(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if obj.get('type') == 'batch_header':
                continue
            rows.append(obj)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--jsonl', required=True)
    ap.add_argument('--thresholds', default='0,0.5,0.6,0.7,0.8,0.9,0.95')
    ap.add_argument('--out')
    args = ap.parse_args(argv)
    thresholds = [float(x) for x in args.thresholds.split(',') if x.strip()]
    rows = load_rows(args.jsonl)
    results = sweep(rows, thresholds)
    if args.out:
        with open(args.out, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(results[0]))
            w.writeheader()
            w.writerows(results)
    for r in results:
        print(f"t={r['threshold']:.2f} kept={r['kept']:3d} correct={r['correct']:3d} "
              f"wrong={r['wrong']:2d} correct_lost={r['correct_lost']:3d} "
              f"wrong_removed={r['wrong_removed']:2d} recall={r['recall']} precision={r['precision']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
