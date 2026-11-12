#!/usr/bin/env python3
"""Read-only arithmetic/saved-detection and strict prefix-causality audit.

No stored ASR/matcher result is described as freshly executed. The original
artifacts remain byte-for-byte unchanged, including their historical labels.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

import fir_isolation as old
from pbfdaf import Config, process
import target_gate


def card_audit(records, expected_ids):
    ids = [r['case_id'] for r in records]
    if len(set(ids)) != len(ids) or set(ids) != set(expected_ids):
        raise ValueError('card audit requires complete, unique expected control/target IDs')
    result = {'records': len(records), 'correct_quotes': 0, 'wrong_quotes': 0,
              'no_target_quotes': 0, 'review': 0, 'no_card': 0, 'words_on_no_target': 0}
    for row in records:
        if type(row.get('has_target')) is not bool:
            raise ValueError('explicit boolean has_target annotation required for offline audit')
        kind = row.get('card_kind', '').upper()
        if not row['has_target']:
            result['words_on_no_target'] += len(row.get('text', '').split())
        if kind == 'QUOTE':
            if not row['has_target']:
                result['wrong_quotes'] += 1; result['no_target_quotes'] += 1
            elif row.get('card_ref') and row.get('card_ref') == row.get('verse_id'):
                result['correct_quotes'] += 1
            else:
                result['wrong_quotes'] += 1
        elif kind == 'REVIEW':
            result['review'] += 1
        elif kind in ('', 'NONE', 'NO_CARD'):
            result['no_card'] += 1
        else:
            raise ValueError('unrecognised card kind')
    return result


def legacy_causality():
    rng = np.random.default_rng(876)
    n, cut = 32000, 16079
    target, interference = rng.normal(0, .08, (2, n))
    c = target+interference
    r = old.shift(.5*target+2*interference, 48)
    changed = r.copy(); changed[cut:] += rng.normal(0, .7, n-cut)
    output = {}
    methods = {'legacy_scalar': lambda c, r: old.scalar_nlms(c, r)[0],
               'legacy_fir32': lambda c, r: old.fir_nlms(c, r, taps=32)[0],
               'legacy_fir32_dt': lambda c, r: old.fir_nlms(c, r, taps=32, double_talk=True)[0],
               'legacy_tracking': lambda c, r: old.fir_tracking(c, r, taps=32, chunk_s=.25)[0],
               'pbfdaf': lambda c, r: process(c, r, Config())}
    for name, fn in methods.items():
        a, b = fn(c, r), fn(c, changed)
        diff = np.abs(a[:cut]-b[:cut])
        affected = np.flatnonzero(diff > 1e-10)
        output[name] = {'future_mutation_starts': cut, 'room_lag_estimated': old.est_delay(c, r, 6400),
                        'max_past_output_difference': float(np.max(diff)),
                        'first_affected_sample': int(affected[0]) if len(affected) else None,
                        'strict_source_time_prefix_pass': not len(affected)}
    # A second counterexample isolates the pre-read calibration dependency.
    calibration_cut = 320
    r2 = r.copy()
    r2[calibration_cut:6400] = old.shift(.5*target+2*interference, 96)[calibration_cut:6400]
    a, b = old.scalar_nlms(c, r)[0], old.scalar_nlms(c, r2)[0]
    output['legacy_initial_calibration'] = {
        'mutation_starts': calibration_cut,
        'old_estimated_lag': old.est_delay(c, r, 6400),
        'new_estimated_lag': old.est_delay(c, r2, 6400),
        'max_output_difference_before_mutation': float(np.max(np.abs(a[:calibration_cut]-b[:calibration_cut])))}
    return output


def audit(root):
    def read(name):
        with (root/'data'/name).open() as f: return list(csv.DictReader(f))
    hash_issues, checked = [], 0
    for line in (root/'SHA256SUMS.txt').read_text().splitlines():
        if not line.strip(): continue
        expected, name = line.split(maxsplit=1); path = root/name.lstrip('*')
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        checked += 1
        if actual != expected: hash_issues.append(name)
    aggregate, sdi, replication = read('results_holdout.csv'), read('holdout_sdi.csv'), []
    for row in aggregate:
        method = row['method']; expected = 100*int(row['edits'])/int(row['ref_words'])
        detail = [r for r in sdi if r['method'] == method]
        edits = sum(int(r['S'])+int(r['D'])+int(r['I']) for r in detail) if detail else None
        replication.append({'method': method, 'clips': int(row['clips']),
                            'ref_words': int(row['ref_words']), 'edits': int(row['edits']),
                            'wer_recomputed_pct': expected, 'stored_wer_pct': float(row['wer_pct']),
                            'rounding_agrees': abs(expected-float(row['wer_pct'])) < .00051,
                            'sdi_sum': edits, 'sdi_agrees': edits == int(row['edits']) if detail else None,
                            'status': 'SAVED_COUNTS_ARITHMETIC_ONLY'})
    baseline = []
    for row in read('scorer_provenance.csv'):
        edits = sum(int(row[k]) for k in ('substitutions', 'deletions', 'insertions'))
        baseline.append({'arm': row['arm'], 'clips': int(row['n_clips']),
                         'ref_words': int(row['ref_words']), 'edits': edits,
                         'wer_recomputed_pct': 100*edits/int(row['ref_words']),
                         'stored_wer_pct': float(row['wer_v2_pct']),
                         'status': 'SAVED_COUNTS_ARITHMETIC_ONLY'})
    saved = json.loads((root/'data/ctrl03_saved_detection.json').read_text())
    return {'source_hashes_checked': checked, 'source_hash_issues': hash_issues,
            'saved_aggregate_replication': replication, 'saved_single_channel_replication': baseline,
            'stored_ci_only_not_recomputed': read('results_ci.csv'),
            'stored_control_counts_not_acoustically_rerun': read('fir_cards.csv'),
            'ctrl03_saved_detection_audit': card_audit([saved], ['CTRL03']),
            'ctrl03_confidence_threshold_08_replay': target_gate.gate_metrics([saved], .8),
            'actual_matcher_reexecution': 'BLOCKED_MATCHER',
            'acoustic_reproduction': 'BLOCKED_FIXTURE',
            'strict_causality_counterexamples': legacy_causality(),
            'legacy_numbers_preserved_but_causal_label_disputed': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = audit(Path(__file__).resolve().parents[1])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
