#!/usr/bin/env python3
"""MODEL_FREE_SYNTHETIC study: procedural signals, NO words, audio, ASR or matcher.

These are new surrogate fixtures, not the KJV/owner corpus. Positions preserve
the handoff's split IDs only. Tune and evaluate are separate invocations; a
config/source hash is frozen before holdout generation. Never select on controls.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import time
import zlib

import numpy as np
from scipy.signal import lfilter

from pbfdaf import Config, PBFDAF, process

SR = 16000
SECONDS = 4
EVIDENCE = 'MODEL_FREE_SYNTHETIC'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hashes():
    return {name: digest(Path(__file__).with_name(name))
            for name in ('pbfdaf.py', 'pbfdaf_study.py')}


def surrogate(seed, voice=0, n=SR*SECONDS):
    rng = np.random.default_rng(seed)
    time_axis = np.arange(n)/SR
    f0 = (123 if voice == 0 else 187) + 6*np.sin(2*np.pi*.6*time_axis)
    phase = 2*np.pi*np.cumsum(f0)/SR
    voiced = sum(np.sin(k*phase + rng.uniform(0, 6.28))/k for k in range(1, 9))
    colored = lfilter([1], [1, -.85], rng.standard_normal(n))
    env = (.12 + .88*np.sin(2*np.pi*(2.3 if voice == 0 else 3.1)*time_axis)**2)
    x = env*(.55*voiced + .45*colored/np.std(colored))
    return x/np.sqrt(np.mean(x*x))*.08


def delayed(x, start, end):
    axis = np.arange(len(x))
    return np.interp(axis-np.linspace(start, end, len(x)), axis, x, left=0, right=0)


def fixture(case_id, source, tir):
    seed = zlib.crc32(f'{case_id}|{source}|{tir}|procedural-v1'.encode())
    rng = np.random.default_rng(seed)
    t = surrogate(seed, 0)
    i = surrogate(seed+1, 1)
    if source == 'chatter_surrogate':
        i = lfilter([1], [1, -.7], rng.standard_normal(len(t)))
        i *= .08/np.sqrt(np.mean(i*i))
    d0 = int(rng.integers(40, 61)); d1 = d0+int(rng.integers(0, 13))
    leak = float(rng.uniform(5, 7))
    level = 10**(-tir/20)
    c = t + level*i
    r = 10**(-leak/20)*delayed(t, d0, d1) + 10**(leak/20)*level*delayed(i, d0, d1)
    ir_len = int(SR*rng.uniform(.12, .2))
    ir = rng.normal(size=ir_len)*np.exp(-np.arange(ir_len)/(ir_len/4))
    ir *= .55/np.linalg.norm(ir); ir[0] += .75; ir /= np.linalg.norm(ir)
    r = np.convolve(r, ir, mode='full')[:len(r)]
    r *= 10**(rng.uniform(-1.5, 1.5)*np.sin(2*np.pi*rng.uniform(.2, .5)*np.arange(len(r))/SR)/20)
    return t, i, c, r


def metrics(y, t, i, close):
    # Sources are available here for offline scoring ONLY. No inference call
    # accepts them. Residual distortion is reported separately from 2-source SIR.
    gram = np.array([[t@t, t@i], [t@i, i@i]])
    a, b = np.linalg.solve(gram, np.array([t@y, i@y]))
    ac, bc = np.linalg.solve(gram, np.array([t@close, i@close]))
    sir = 10*np.log10((a*a*(t@t)+1e-15)/(b*b*(i@i)+1e-15))
    before = 10*np.log10((ac*ac*(t@t)+1e-15)/(bc*bc*(i@i)+1e-15))
    proj = (t@y)/(t@t)*t
    sdr = 10*np.log10((proj@proj+1e-15)/((y-proj)@(y-proj)+1e-15))
    return {'delta_sir_db': float(sir-before),
            'target_retention_db': float(20*np.log10((abs(a)+1e-15)/(abs(ac)+1e-15))),
            'si_sdr_db': float(sdr), 'rms_out': float(np.sqrt(np.mean(y*y)))}


def time_baseline(c, r, taps=1, double_talk=False):
    """Original NLMS update/gate with zero alignment and no calibration pre-read.

    These are new causal variants, not reproduction of old aligned ASR arms.
    """
    block = 160
    windows = np.lib.stride_tricks.sliding_window_view(np.pad(r, (taps-1, 0)), taps)
    w, out, history = np.zeros(taps), np.empty_like(c), []
    for s in range(0, len(c), block):
        end = min(s+block, len(c)); x = windows[s:end]; cb, rb = c[s:end], r[s:end]
        out[s:end] = cb-x@w
        energy = float(cb@cb)
        freeze = double_talk and bool(history) and energy > 1.8*np.median(history)
        history = (history+[energy])[-50:]
        if rb@rb > cb@cb and not freeze:
            mu = .5 if taps == 1 else .3
            w += mu*(x.T@out[s:end])/(np.sum(x*x)+1e-9)
            w = np.clip(w, 0, 1.2) if taps == 1 else np.clip(w, -2, 2)
    return out


def tune(outdir):
    if (outdir/'frozen_config.json').exists():
        raise SystemExit('existing freeze: choose a new output directory; never overwrite a study')
    fixtures = [fixture(f'{n:04d}', src, tir) for n in range(21, 31)
                for src in ('chatter_surrogate', 'preacher_surrogate') for tir in (0, -5)]
    grid = []
    for fft in (256, 512):
        for partitions in (4, 8, 16):
            for mu in (.15, .4):
                cfg = Config(fft_size=fft, partitions=partitions, mu=mu)
                rows = [metrics(process(c, r, cfg), t, i, c) for t, i, c, r in fixtures]
                dsir = float(np.mean([x['delta_sir_db'] for x in rows]))
                retention = float(np.mean([x['target_retention_db'] for x in rows]))
                # Fixed before running: reward SIR; penalise >1 dB mean target loss.
                objective = dsir + 2*min(0, retention+1)
                grid.append({'config': asdict(cfg), 'mean_delta_sir_db': dsir,
                             'mean_target_retention_db': retention, 'objective': objective})
    selected = max(grid, key=lambda x: x['objective'])
    frozen = {'evidence_class': EVIDENCE, 'fixture_family': 'procedural-v1',
              'source_hashes': source_hashes(), 'sample_rate': SR, 'duration_s': SECONDS,
              'tune_ids': [f'{n:04d}' for n in range(21, 31)],
              'holdout_ids': [f'{n:04d}' for n in range(31, 41)],
              'tune_cases': 40, 'grid': grid, 'selected': selected,
              'selection_rule': 'mean delta SIR + 2*min(0, mean target retention + 1 dB)',
              'holdout_generated_before_freeze': False,
              'no_target_controls_used_for_selection': False}
    (outdir/'frozen_config.json').write_text(json.dumps(frozen, indent=2)+'\n')
    print(json.dumps({'selected': selected, 'tune_cases': 40, 'grid_size': len(grid)}))


def cluster_ci(rows, metric):
    cases = sorted({r['case_id'] for r in rows})
    values = np.array([np.mean([r[metric] for r in rows if r['case_id'] == cid]) for cid in cases])
    rng = np.random.default_rng(20261112)
    boot = np.mean(values[rng.integers(0, len(cases), (2000, len(cases)))], axis=1)
    lo, hi = np.quantile(boot, [.025, .975])
    return {'mean': float(np.mean(values)), 'ci_low': float(lo), 'ci_high': float(hi),
            'resamples': 2000, 'cluster_unit': 'procedural case_id', 'clusters': len(cases)}


def evaluate(outdir):
    frozen_path = outdir/'frozen_config.json'
    frozen = json.loads(frozen_path.read_text())
    if frozen['source_hashes'] != source_hashes():
        raise SystemExit('source changed after freeze; evaluation refused')
    if (outdir/'results.json').exists():
        raise SystemExit('holdout already evaluated; choose a new study, never overwrite')
    cfg = Config(**frozen['selected']['config'])
    train_error = max(float(np.max(np.abs(process((t:=surrogate(n)), .5*t, cfg)-t))) for n in range(1, 21))
    rows = []
    methods = {'close': lambda c, r: c.copy(),
               'scalar_causal_no_alignment': lambda c, r: time_baseline(c, r),
               'fir32_causal_no_alignment': lambda c, r: time_baseline(c, r, 32),
               'fir32_dt_causal_no_alignment': lambda c, r: time_baseline(c, r, 32, True),
               'pbfdaf': lambda c, r: process(c, r, cfg)}
    for n in range(31, 41):
        cid = f'{n:04d}'
        for src in ('chatter_surrogate', 'preacher_surrogate'):
            for tir in (0, -5):
                t, i, c, r = fixture(cid, src, tir)
                for method, fn in methods.items():
                    start = time.perf_counter(); y = fn(c, r); seconds = time.perf_counter()-start
                    rows.append({'case_id': cid, 'source': src, 'tir_db': tir,
                                 'method': method, 'evidence_class': EVIDENCE,
                                 'samples_in': len(c), 'samples_out': len(y),
                                 'cpu_wall_s': seconds, **metrics(y, t, i, c)})
    summary = {}
    for method in methods:
        subset = [r for r in rows if r['method'] == method]
        summary[method] = {key: cluster_ci(subset, key) for key in
                           ('delta_sir_db', 'target_retention_db', 'si_sdr_db')}
    # Paired comparisons use the same case/source/TIR, with case-cluster bootstrap.
    comparisons = {}
    index = {(r['case_id'], r['source'], r['tir_db']): r for r in rows if r['method'] == 'pbfdaf'}
    for method in methods:
        if method == 'pbfdaf': continue
        pairs = [{'case_id': r['case_id'], 'difference': index[(r['case_id'], r['source'], r['tir_db'])]['delta_sir_db']-r['delta_sir_db']}
                 for r in rows if r['method'] == method]
        comparisons[method] = cluster_ci(pairs, 'difference')
    controls = []
    for n in range(28):
        c = surrogate(9000+n, 1) if n < 20 else np.zeros(SR*SECONDS)
        r = 2*delayed(c, 48, 55)
        y = process(c, r, cfg)
        controls.append({'case_id': f'PROC_CTRL{n+1:02d}', 'kind': 'other_signal_only' if n < 20 else 'silence',
                         'evidence_class': EVIDENCE, 'samples': len(y),
                         'residual_rms': float(np.sqrt(np.mean(y*y))),
                         'emitted_cards': None, 'asr_words': None,
                         'card_status': 'BLOCKED_FIXTURE_ASR_MATCHER'})
    # Identical inputs with two possible speaker labels prove non-identifiability.
    t = surrogate(99999)
    ambiguous = process(t, 2*t, cfg)
    ambiguous_retention = float(20*np.log10(np.linalg.norm(ambiguous[-SR:])/np.linalg.norm(t[-SR:])))
    stream = PBFDAF(cfg)
    throughput_t = surrogate(87654, n=60*SR)
    throughput_r = 2*delayed(throughput_t, 48, 60)
    start = time.perf_counter(); stream.push(throughput_t, throughput_r); stream.flush()
    wall = time.perf_counter()-start
    result = {'evidence_class': EVIDENCE, 'frozen_config_sha256': digest(frozen_path),
              'source_hashes': source_hashes(), 'train_cases': 20, 'train_target_only_max_abs_error': train_error,
              'holdout_cases': 40, 'independent_case_positions': 10, 'samples_per_case': SR*SECONDS,
              'target_reference_words': 0, 'target_wer_pct': None, 'wer_status': 'NOT_APPLICABLE_NO_WORDS',
              'prior_corpus_replication': 'BLOCKED_FIXTURE',
              'summary': summary, 'paired_delta_sir_pbfdaf_minus_baseline': comparisons,
              'rows': rows, 'controls': controls,
              'identity_counterexample': {'same_inputs_different_speaker_labels': True,
                                          'target_retention_last_second_db': ambiguous_retention,
                                          'speaker_identity_guard': 'UNPROVEN'},
              'throughput': {'audio_s': 60, 'wall_s': wall, 'rtf': wall/60,
                             'persistent_ndarray_bytes': stream.state_bytes,
                             'maximum_block_buffer_ms': stream.buffering_ms,
                             'filter_support_ms': 1000*cfg.support_samples/SR,
                             'blocks': stream.blocks, 'adapted_blocks': stream.adapted_blocks,
                             'not_end_to_end_latency': True},
              'runtime': {'python': platform.python_version(), 'numpy': np.__version__,
                          'machine': platform.machine(), 'platform': platform.platform()},
              'no_target_card_gate': 'NOT_EVALUATED_NOT_PASSED',
              'real_church': 'BLOCKED_GOLD', 'card_visible': 'NOT_MEASURED',
              'production': 'PRODUCTION_NO_GO'}
    (outdir/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('rows', 'controls')}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('tune', 'evaluate'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (tune if args.phase == 'tune' else evaluate)(args.out)


if __name__ == '__main__':
    main()
