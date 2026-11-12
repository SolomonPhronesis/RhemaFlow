#!/usr/bin/env python3
"""RF_RESEARCH_AUDIO_V1 reference producer, consumer and offline paired scorer.

Expected target/reference labels belong to offline scoring, never to the decoder
request. This module grants no permission to integrate with Personal or emit UI.
"""
import hashlib
import json
import math
from pathlib import PurePosixPath
import random
import re

import wer

SCHEMA = 'RF_RESEARCH_AUDIO_V1'
SHA = re.compile(r'^[0-9a-f]{64}$')


def require(condition, message):
    if not condition: raise ValueError(message)


def validate_case(case):
    require(case.get('schema') == SCHEMA, 'unsupported exchange schema')
    for field in ('case_id', 'session_id', 'speaker_id', 'condition', 'evidence_class'):
        require(isinstance(case.get(field), str) and bool(case[field]), 'missing '+field)
    require(case.get('split') in ('train', 'tune', 'holdout', 'control'), 'invalid split')
    require(case.get('rights_status') in ('verified', 'pending', 'denied'), 'explicit rights status required')
    require(type(case.get('research_allowed')) is bool, 'explicit research permission required')
    expected = case.get('expected', {})
    require(type(expected.get('has_target')) is bool and isinstance(expected.get('gold_text'), str), 'offline gold/target labels required')
    require(expected['has_target'] or not expected['gold_text'], 'no-target reference must be empty')
    require(not expected['has_target'] or bool(wer.tokens(expected['gold_text'])), 'target reference must contain scored words')
    require(isinstance(expected.get('verse_ref'), str), 'explicit expected verse reference required')
    channels = case.get('channels')
    require(isinstance(channels, list) and 1 <= len(channels) <= 2, 'one or two raw channels required')
    roles = []
    for channel in channels:
        require(channel.get('role') in ('close', 'room'), 'invalid channel role')
        roles.append(channel['role'])
        p = PurePosixPath(channel.get('path', ''))
        require(bool(channel.get('path')) and not p.is_absolute() and '..' not in p.parts and '\\' not in str(p), 'relative local audio path required')
        require(SHA.fullmatch(channel.get('sha256', '')) is not None, 'audio hash required')
        require(channel.get('sample_rate') in (16000, 48000), 'unsupported sample rate')
        require(type(channel.get('samples')) is int and channel['samples'] > 0, 'positive audio sample count required')
        require(isinstance(channel.get('clock_id'), str) and bool(channel['clock_id']), 'clock metadata required')
    require(len(set(roles)) == len(roles) and 'close' in roles, 'duplicate/missing channel role')
    require(channels[0]['role'] == 'close', 'first channel must be the close reference')
    if len(channels) == 2:
        require(len({c['clock_id'] for c in channels}) == 1, 'two channels require a shared clock')
        require(len({(c['sample_rate'], c['samples']) for c in channels}) == 1, 'paired channels must share rate and length')
    return case


def inference_request(case, model, request_id):
    validate_case(case)
    require(case['rights_status'] == 'verified' and case['research_allowed'], 'asset eligibility blocked')
    require(type(request_id) is int and request_id >= 0, 'invalid request ID')
    require(model.get('family') in ('qwen3-asr-1.7b-base', 'parakeet-v2-q4', 'whisper-tiny.en'), 'approved BASE model family required')
    require(SHA.fullmatch(model.get('sha256', '')) is not None, 'model fingerprint required')
    require(model.get('precision') in ('bf16', 'fp16', 'q4_k_m', '4bit', '4bit-embed8', 'ggml-tiny.en'), 'explicit supported precision required')
    allowed = {'qwen3-asr-1.7b-base': {'bf16', 'fp16', '4bit', '4bit-embed8'},
               'parakeet-v2-q4': {'q4_k_m'}, 'whisper-tiny.en': {'ggml-tiny.en'}}
    require(model['precision'] in allowed[model['family']], 'precision/family mismatch')
    require(isinstance(model.get('id'), str) and bool(model['id']), 'model ID required')
    # Producer allow-list: gold, verse, target presence, speaker ID, split,
    # condition and all expected annotations are deliberately absent.
    return {'schema': SCHEMA, 'request_id': request_id, 'case_id': case['case_id'],
            'channels': case['channels'], 'model': dict(model)}


class CardEventConsumer:
    """Append-only offline event sink. No matcher and no speaker guard."""
    def __init__(self):
        self.events = {}

    def accept(self, event, *, committed_text):
        require(event.get('schema') == SCHEMA, 'unsupported event schema')
        require(event.get('kind') in ('QUOTE', 'REVIEW'), 'unsupported card event')
        require(isinstance(event.get('card_id'), str) and bool(event['card_id']), 'card ID required')
        require(isinstance(event.get('verse_ref'), str) and bool(event['verse_ref']), 'verse required')
        for field in ('audio_end_ms', 'asr_done_ms', 'matcher_done_ms'):
            value = event.get(field)
            require(type(value) in (float, int) and math.isfinite(value) and value >= 0, 'invalid event timestamp')
        require(event['audio_end_ms'] <= event['asr_done_ms'] <= event['matcher_done_ms'], 'timestamp ordering')
        require(event.get('card_visible_ms') is None, 'offline contract cannot assert card_visible')
        digest = hashlib.sha256(committed_text.encode()).hexdigest()
        require(event.get('committed_text_sha256') == digest, 'card not backed by current committed text')
        canonical = json.dumps(event, sort_keys=True)
        identity = event['card_id']
        if identity in self.events:
            require(self.events[identity] == canonical, 'previously projected card mutation rejected')
            return False
        self.events[identity] = canonical
        return True


def score_paired(cases, records, model_ids, baseline_id, seed=20261112):
    require(bool(cases) and len(model_ids) >= 2, 'nonempty cases and at least two paired models required')
    require(len(model_ids) == len(set(model_ids)) and baseline_id in model_ids, 'invalid models')
    require(len({c['case_id'] for c in cases}) == len(cases), 'duplicate case IDs')
    for case in cases:
        validate_case(case)
        require(case['split'] in ('holdout', 'control'), 'evaluation accepts only frozen holdout/control cases')
    expected_keys = {(c['case_id'], m) for c in cases for m in model_ids}
    indexed = {}
    for row in records:
        key = (row.get('case_id'), row.get('model_id'))
        require(key not in indexed and key in expected_keys, 'duplicate/unexpected result key')
        require(isinstance(row.get('text'), str), 'text required, including explicit empty text')
        require(row.get('status') == 'OK', 'failed inference is not omitted or scored as success')
        indexed[key] = row
    require(set(indexed) == expected_keys, 'incomplete transcript coverage')
    output, per_model, correct_cases = {}, {}, {}
    for model in model_ids:
        correct_cases[model] = set()
        per_case = []
        cards_available = True
        totals = {'target_cases': 0, 'reference_words': 0, 'S': 0, 'D': 0, 'I': 0,
                  'no_target_cases': 0, 'words_on_no_target': 0,
                  'correct_quotes': 0, 'wrong_quotes': 0, 'no_target_emitted_cards': 0}
        for case in cases:
            row = indexed[(case['case_id'], model)]
            require(row.get('input_sha256') == case['channels'][0]['sha256'], 'mismatched model input')
            if len(case['channels']) == 2:
                require(row.get('input_channel_sha256') == {c['role']: c['sha256'] for c in case['channels']}, 'mismatched paired channels')
            gold = wer.tokens(case['expected']['gold_text']); hyp = wer.tokens(row['text'])
            s, d, i, edits = wer.edit_counts(gold, hyp)
            if gold:
                totals['target_cases'] += 1; totals['reference_words'] += len(gold)
                totals['S'] += s; totals['D'] += d; totals['I'] += i
            else:
                totals['no_target_cases'] += 1; totals['words_on_no_target'] += len(hyp)
            # None means the actual matcher was not run; [] means run, no cards.
            cards = row.get('cards')
            if cards is None:
                cards_available = False
            else:
                require(isinstance(cards, list), 'invalid cards')
                for card in cards:
                    require(card.get('kind') in ('QUOTE', 'REVIEW'), 'unrecognised card event')
                    if not case['expected']['has_target']:
                        totals['no_target_emitted_cards'] += 1
                    if card['kind'] == 'QUOTE':
                        correct = case['expected']['has_target'] and card.get('verse_ref') == case['expected']['verse_ref']
                        totals['correct_quotes' if correct else 'wrong_quotes'] += 1
                        if correct: correct_cases[model].add(case['case_id'])
            per_case.append({'case_id': case['case_id'], 'ref': len(gold), 'edits': edits if gold else 0,
                             'cluster': case['speaker_id'] if case['evidence_class'] == 'REAL_CHURCH' else case.get('cluster_id', case['case_id'])})
        n = totals['reference_words']
        totals['edits'] = totals['S']+totals['D']+totals['I']
        totals['wer_pct'] = 100*totals['edits']/n if n else None
        totals['coverage_pct'] = 100.0
        if not cards_available:
            for field in ('correct_quotes', 'wrong_quotes', 'no_target_emitted_cards'): totals[field] = None
        totals['cards_status'] = 'MEASURED_RECORDS' if cards_available else 'NOT_RUN'
        timings = [indexed[(c['case_id'], model)].get('timing') for c in cases]
        timings = [t for t in timings if t is not None]
        for t in timings:
            require(isinstance(t, dict), 'timing object required')
            for key, value in t.items():
                require(key in ('load_ms', 'decode_wall_ms', 'audio_duration_ms', 'end_to_end_ms', 'peak_rss_bytes', 'energy_joules'), 'unsupported timing/resource field')
                require(value is None or (type(value) in (int, float) and math.isfinite(value) and value >= 0), 'invalid timing/resource value')
        def percentiles(key):
            values = sorted(t[key] for t in timings if t.get(key) is not None)
            if not values: return {'p50': None, 'p95': None, 'measured_cases': 0}
            def q(p):
                at = (len(values)-1)*p; lo = int(at); hi = min(lo+1, len(values)-1)
                return values[lo]+(values[hi]-values[lo])*(at-lo)
            return {'p50': q(.5), 'p95': q(.95), 'measured_cases': len(values)}
        totals['latency'] = {key: percentiles(key) for key in ('load_ms', 'decode_wall_ms', 'end_to_end_ms')}
        duration_rows = [t for t in timings if t.get('decode_wall_ms') is not None and t.get('audio_duration_ms') is not None]
        require(all(t['audio_duration_ms'] > 0 for t in duration_rows), 'positive RTF duration required')
        totals['rtf_measured_cases'] = len(duration_rows)
        totals['rtf'] = sum(t['decode_wall_ms'] for t in duration_rows)/sum(t['audio_duration_ms'] for t in duration_rows) if duration_rows else None
        totals['peak_rss_bytes'] = max((t['peak_rss_bytes'] for t in timings if t.get('peak_rss_bytes') is not None), default=None)
        energy = [t['energy_joules'] for t in timings if t.get('energy_joules') is not None]
        totals['energy_joules'] = sum(energy) if len(energy) == len(cases) else None
        output[model], per_model[model] = totals, per_case
    baseline = {r['case_id']: r for r in per_model[baseline_id]}
    cis, retention = {}, {}
    for model in model_ids:
        if model == baseline_id: continue
        if output[model]['cards_status'] == output[baseline_id]['cards_status'] == 'MEASURED_RECORDS':
            denominator = len(correct_cases[baseline_id])
            retained = len(correct_cases[model] & correct_cases[baseline_id])
            retention[model] = {'baseline_correct_case_opportunities': denominator, 'retained': retained,
                                'lost_pct': 100*(denominator-retained)/denominator if denominator else None,
                                'additional_wrong_quotes': output[model]['wrong_quotes']-output[baseline_id]['wrong_quotes']}
        else: retention[model] = None
        pairs = [dict(r, baseline_edits=baseline[r['case_id']]['edits']) for r in per_model[model] if r['ref']]
        clusters = sorted({r['cluster'] for r in pairs})
        if not clusters:
            cis[model] = None; continue
        rng = random.Random(seed); values = []
        by_cluster = {k: [r for r in pairs if r['cluster'] == k] for k in clusters}
        for _ in range(2000):
            sample = [r for _ in clusters for r in by_cluster[rng.choice(clusters)]]
            values.append(100*sum(r['baseline_edits']-r['edits'] for r in sample)/sum(r['ref'] for r in sample))
        values.sort()
        cis[model] = {'delta_pp': output[baseline_id]['wer_pct']-output[model]['wer_pct'],
                      'ci_low': values[50], 'ci_high': values[1949], 'resamples': 2000,
                      'seed': seed, 'clusters': len(clusters)}
    return {'schema': SCHEMA, 'models': output, 'paired_wer_gain_vs_baseline': cis,
            'correct_card_case_retention_vs_baseline': retention,
            'evidence_classes': sorted({c['evidence_class'] for c in cases}),
            'model_execution': 'Scoring supplied records only; no model is run by this scorer.',
            'production': 'PRODUCTION_NO_GO', 'card_visible': 'NOT_MEASURED'}
