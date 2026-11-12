#!/usr/bin/env python3
"""Recompute coverage and paired statistics from one immutable PBFDAF run."""
import argparse
import json
from pathlib import Path

from pbfdaf_study import cluster_ci


def summarize(data):
    rows = data['rows']
    methods = sorted({r['method'] for r in rows})
    expected_methods = {'close', 'scalar_causal_no_alignment', 'fir32_causal_no_alignment',
                        'fir32_dt_causal_no_alignment', 'pbfdaf'}
    if set(methods) != expected_methods:
        raise ValueError('missing/unexpected method')
    expected = {(f'{n:04d}', s, t) for n in range(31, 41)
                for s in ('chatter_surrogate', 'preacher_surrogate') for t in (0, -5)}
    coverage, paired = {}, {}
    pidx = {(r['case_id'], r['source'], r['tir_db']): r for r in rows if r['method'] == 'pbfdaf'}
    for method in methods:
        subset = [r for r in rows if r['method'] == method]
        keys = [(r['case_id'], r['source'], r['tir_db']) for r in subset]
        if len(keys) != 40 or len(set(keys)) != 40 or set(keys) != expected:
            raise ValueError('incomplete/duplicate paired coverage')
        if not all(r['samples_in'] == r['samples_out'] == 64000 for r in subset):
            raise ValueError('truncated sample coverage')
        coverage[method] = {'expected': 40, 'observed_unique': len(keys),
                            'coverage_pct': 100.0, 'sample_coverage_pct': 100.0,
                            'transcript_coverage_pct': None}
    # Validate every arm before indexing any paired comparison.
    for method in methods:
        if method == 'pbfdaf': continue
        subset = [r for r in rows if r['method'] == method]
        paired[method] = {}
        for metric in ('si_sdr_db', 'target_retention_db', 'delta_sir_db'):
            diffs = [{'case_id': r['case_id'],
                      'difference': pidx[(r['case_id'], r['source'], r['tir_db'])][metric]-r[metric]}
                     for r in subset]
            paired[method][metric] = cluster_ci(diffs, 'difference')
    controls = data['controls']
    if len(controls) != 28 or len({c['case_id'] for c in controls}) != 28:
        raise ValueError('incomplete/duplicate procedural controls')
    other = [r for r in controls if r['kind'] == 'other_signal_only']
    silence = [r for r in controls if r['kind'] == 'silence']
    if len(other) != 20 or len(silence) != 8:
        raise ValueError('expected 20 other-signal + 8 silence controls')
    return {'coverage': coverage, 'paired_pbfdaf_minus_baseline': paired,
            'control_audio_coverage': {'other_signal_only': 20, 'silence': 8, 'asr_and_cards': None},
            'empty_reference_wer': 'Excluded; procedural no-target signals have no reference words; no fabricated WER.',
            'no_target_residuals': {'other_signal_only_mean_rms': sum(c['residual_rms'] for c in other)/20,
                                    'silence_max_rms': max(c['residual_rms'] for c in silence)}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(json.loads((args.run/'results.json').read_text())), indent=2))
