#!/usr/bin/env python3
"""Offline research gates; no decoder, speaker classifier, card emitter or trainer.

Research eligibility is an evidence check, never permission to promote a product.
Gold and speaker labels are consumed only by offline scoring.
"""
import hashlib
import json
import math
import random
import re
from pathlib import PurePosixPath

import wer

SHA = re.compile(r'^[a-f0-9]{64}$')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit_splits(cases):
    """Prevent connected church/speaker/session/source groups crossing splits."""
    identities = {}
    seen = set()
    for case in cases:
        require(case['case_id'] not in seen, 'duplicate case')
        seen.add(case['case_id'])
        require(case['split'] in ('train', 'tune', 'holdout', 'control'), 'invalid split')
        # Controls evaluated with holdout are the same frozen evaluation split.
        split = 'holdout' if case['split'] == 'control' else case['split']
        require(case.get('speaker_ids'), 'all audible speakers must be grouped')
        keys = [('church', case['church_id']), ('session', case['session_id']),
                ('source', case.get('parent_source_sha256') or case['source_sha256'])]
        keys += [('speaker', speaker) for speaker in case['speaker_ids']]
        for kind, identity in keys:
            require(bool(identity), 'missing grouping identity')
            old = identities.setdefault((kind, identity), split)
            require(old == split, 'train/tune/evaluation contamination: ' + kind)
    return True


def inference_envelope(case, model):
    """Only observed audio and a pinned base model enter the independent adapter."""
    require(case.get('rights_status') == 'verified' and case.get('research_allowed') is True,
            'BLOCKED_RIGHTS')
    require(model.get('family') in ('qwen3-asr-1.7b-base', 'parakeet-v2-q4', 'parakeet-v2-q8'),
            'unapproved model family; restricted R2T2 teachers are excluded')
    require(SHA.fullmatch(model.get('sha256', '')), 'model hash required')
    precision = {'qwen3-asr-1.7b-base': {'4bit', '4bit-embed8', 'bf16'},
                 'parakeet-v2-q4': {'q4_k_m'}, 'parakeet-v2-q8': {'q8_0'}}
    require(model.get('precision') in precision[model['family']], 'precision/family mismatch')
    require(SHA.fullmatch(model.get('tokenizer_sha256', '')), 'tokenizer identity required')
    channels = []
    for channel in case['channels']:
        require(channel['role'] in ('close', 'room') and SHA.fullmatch(channel['sha256']), 'channel identity')
        path = PurePosixPath(channel['path'])
        require(not path.is_absolute() and '..' not in path.parts, 'relative local path required')
        require(channel['sample_rate'] in (16000, 48000) and channel['samples'] > 0 and
                channel['clock_id'], 'channel timing required')
        channels.append({key: channel[key] for key in
                         ('role', 'path', 'sha256', 'sample_rate', 'samples', 'clock_id')})
    require(1 <= len(channels) <= 2 and channels[0]['role'] == 'close', 'channel roles')
    require(len({c['role'] for c in channels}) == len(channels), 'duplicate channel')
    require(len({(c['sample_rate'], c['samples'], c['clock_id']) for c in channels}) == 1,
            'same-clock aligned channels required')
    # V1 does not accept the Q8 family; this V2 proposal is offline and versioned.
    # Opaque request IDs avoid verse-bearing case names becoming model context.
    request_id = hashlib.sha256(case['case_id'].encode()).hexdigest()[:24]
    return {'schema': 'RF_RESEARCH_TRIAL_V2_DRAFT', 'request_id': request_id,
            'channels': channels,
            'model': {key: model[key] for key in ('family', 'precision', 'sha256', 'tokenizer_sha256')}}


def connected_clusters(cases):
    groups = []
    for case in cases:
        keys = {('church', case['church_id']), ('session', case['session_id'])}
        keys |= {('speaker', speaker) for speaker in case['speaker_ids']}
        matching = [group for group in groups if group['keys'] & keys]
        merged = {'keys': keys, 'cases': {case['case_id']}}
        for group in matching:
            merged['keys'] |= group['keys']; merged['cases'] |= group['cases']
            groups.remove(group)
        groups.append(merged)
    return [sorted(group['cases']) for group in groups]


def paired_interval(cases, pairs, resamples=2000, seed=20261112):
    """Paired corpus-WER gain, resampling connected clusters, never clip means."""
    clusters = connected_clusters(cases)
    if len(clusters) < 2:
        return {'low_pp': None, 'high_pp': None, 'clusters': len(clusters),
                'reason': 'insufficient independent clusters', 'seed': seed}
    rng = random.Random(seed)
    samples = []
    for _ in range(resamples):
        ids = [case_id for _ in clusters for case_id in rng.choice(clusters)]
        total = sum(pairs[identity]['reference_words'] for identity in ids)
        if total:
            samples.append(100 * sum(pairs[i]['baseline_edits'] - pairs[i]['candidate_edits'] for i in ids) / total)
    require(samples, 'no reference words in bootstrap')
    samples.sort()
    return {'low_pp': samples[int(.025 * (len(samples) - 1))],
            'high_pp': samples[int(.975 * (len(samples) - 1))],
            'clusters': len(clusters), 'resamples': resamples, 'seed': seed,
            'unit': 'connected church/speaker/session groups'}


def score_trial(cases, records, baseline, candidate, run):
    if not cases:
        return {'status': 'BLOCKED_GOLD', 'goal_met': False, 'corpus_wer_pct': None,
                'paired_gain_pp': None, 'no_target_cards': None, 'retention': None,
                'real_inference_runs': 0, 'production': 'PRODUCTION_NO_GO'}
    audit_splits(cases)
    require(all(case['split'] in ('holdout', 'control') for case in cases), 'frozen evaluation only')
    indexed = {}
    for row in records:
        key = (row['case_id'], row['model_id'])
        require(key not in indexed, 'duplicate result')
        require(row.get('status') == 'OK', 'failed inference is not omitted')
        indexed[key] = row
    require(set(indexed) == {(c['case_id'], m) for c in cases for m in (baseline, candidate)},
            'incomplete or unexpected paired coverage')
    reference_words = 0
    edits = {baseline: 0, candidate: 0}
    pairs = {}
    correct = {baseline: set(), candidate: set()}
    no_target_cards = {baseline: 0, candidate: 0}
    wrong_cards = {baseline: 0, candidate: 0}
    cards_complete = True
    for case in cases:
        gold = wer.tokens(case['gold_text'])
        require(bool(gold) == case['has_target'], 'target-only gold mismatch')
        reference_words += len(gold)
        pair = {'reference_words': len(gold)}
        for label, model in [('baseline', baseline), ('candidate', candidate)]:
            row = indexed[(case['case_id'], model)]
            require(row['source_sha256'] == case['source_sha256'], 'mismatched audio')
            require(row.get('source_channel_sha256') == {c['role']: c['sha256'] for c in case['channels']},
                    'incomplete/mismatched channel provenance')
            amount = wer.edit_counts(gold, wer.tokens(row['text']))[-1]
            pair[label + '_edits'] = amount if gold else 0
            if gold:
                edits[model] += amount
            cards = row.get('cards')
            if cards is None:
                cards_complete = False
                continue
            require(isinstance(cards, list), 'explicit observed card list required')
            if not case['has_target']:
                no_target_cards[model] += len(cards)  # Includes REVIEW, not just QUOTE.
            for card in cards:
                require(card.get('attribution') in ('target', 'other', 'unknown'),
                        'independent per-card speaker annotation required')
                valid = (case['has_target'] and card['attribution'] == 'target' and
                         card.get('gold_event_id') in case['expected_card_events'] and
                         card.get('verse_ref') == case['expected_card_events'][card['gold_event_id']])
                if not valid:
                    wrong_cards[model] += 1
                if valid and card.get('kind') == 'QUOTE':
                    correct[model].add((case['case_id'], card['gold_event_id']))
        pairs[case['case_id']] = pair
    require(reference_words > 0, 'no target reference denominator')
    candidate_wer = 100 * edits[candidate] / reference_words
    gain = 100 * (edits[baseline] - edits[candidate]) / reference_words
    retention = (len(correct[baseline] & correct[candidate]) / len(correct[baseline])
                 if cards_complete and correct[baseline] else None)
    interval = paired_interval(cases, pairs)
    model_provenance = run.get('models', {})
    provenance_complete = all(
        isinstance(model_provenance.get(model), dict) and
        all(SHA.fullmatch(model_provenance[model].get(key, '')) for key in
            ('weights_sha256', 'tokenizer_sha256', 'transcript_log_sha256')) and
        bool(model_provenance[model].get('runtime_revision'))
        for model in (baseline, candidate)) and bool(SHA.fullmatch(run.get('frozen_manifest_sha256', '')))
    if run.get('evidence_class') == 'NEW_REAL_INFERENCE' and provenance_complete:
        require(all(row.get('model_sha256') == model_provenance[row['model_id']]['weights_sha256']
                    for row in records), 'result/checkpoint provenance mismatch')
    authentic = (run.get('evidence_class') == 'NEW_REAL_INFERENCE' and provenance_complete and
                 run.get('actual_model_inference') is True and
                 run.get('matcher_and_ui_observed') is True and
                 all(c['evidence_class'] == 'REAL_CHURCH' and
                     c.get('rights_status') == 'verified' and c.get('research_allowed') is True and
                     len(set(c.get('transcriber_ids', []))) >= 2 and c.get('adjudicated') is True and
                     c.get('gold_source') == 'HUMAN_INDEPENDENT' and
                     len(c.get('channels', [])) == 2 and
                     all(x.get('sample_rate') == 48000 for x in c['channels']) and
                     all(type(x.get('samples')) is int and x['samples'] > 0 for x in c['channels']) and
                     all(x.get('clock_id') and SHA.fullmatch(x.get('sha256', '')) for x in c['channels']) and
                     {x.get('role') for x in c['channels']} == {'close', 'room'} and
                     len({(x.get('clock_id'), x.get('samples')) for x in c['channels']}) == 1
                     for c in cases))
    rtf = run.get('measured_pipeline_p95_rtf')
    def finite_number(value):
        return type(value) in (float, int) and math.isfinite(value) and value >= 0
    energy = run.get('energy_measurement') or {}
    realtime = (run.get('device') == 'Apple M1 Pro' and run.get('ram_gib') == 16 and
                finite_number(rtf) and rtf <= 1 and
                all(finite_number(run.get(key)) for key in ('e2e_p50_ms', 'e2e_p95_ms', 'peak_rss_bytes')) and
                run['e2e_p50_ms'] <= run['e2e_p95_ms'] and run['peak_rss_bytes'] > 0 and
                isinstance(energy, dict) and finite_number(energy.get('joules')) and
                bool(energy.get('method')) and finite_number(energy.get('duration_s')) and
                energy['duration_s'] > 0 and type(run.get('dropouts')) is int and run['dropouts'] >= 0)
    gates = {'run_provenance_complete': provenance_complete,
             'real_independent_gold': authentic,
             'three_services': len({c['session_id'] for c in cases}) >= 3,
             'corpus_under_six': candidate_wer < 6,
             'paired_gain_at_least_five_pp': gain >= 5,
             'paired_interval_available': interval['low_pp'] is not None,
             'no_target_controls_present': any(not c['has_target'] for c in cases),
             'zero_no_target_cards': cards_complete and no_target_cards[candidate] == 0,
             'no_extra_false_cards': cards_complete and wrong_cards[candidate] <= wrong_cards[baseline],
             'correct_card_loss_at_most_five_pct': retention is not None and retention >= .95,
             'real_time_observed_on_owner_device': realtime}
    return {'status': 'RESEARCH_GATES_MET' if all(gates.values()) else 'GATES_NOT_MET',
            'goal_met': all(gates.values()), 'evidence_class': run.get('evidence_class'),
            'reference_words': reference_words, 'baseline_edits': edits[baseline],
            'candidate_edits': edits[candidate], 'corpus_wer_pct': candidate_wer,
            'paired_gain_pp': gain, 'paired_gain_95_ci': interval,
            'no_target_cards': no_target_cards[candidate] if cards_complete else None,
            'wrong_cards_candidate': wrong_cards[candidate] if cards_complete else None,
            'baseline_correct_card_events': len(correct[baseline]) if cards_complete else None,
            'retention': retention, 'gates': gates, 'production': 'PRODUCTION_NO_GO'}


def validate_training_plan(plan, cases):
    require(plan.get('teacher_models') == [], 'no teacher output use in this local plan')
    require(plan.get('base_family') in ('qwen3-asr-base', 'parakeet-base'), 'approved base only')
    require(plan.get('commercial_base_reviewed') is True, 'base/derivative rights review required')
    for field in ('base_weights_sha256', 'tokenizer_sha256', 'frozen_holdout_sha256', 'config_sha256'):
        require(SHA.fullmatch(plan.get(field, '')), 'missing frozen identity: ' + field)
    audit_splits(cases)
    require(all(c.get('rights_status') == 'verified' and c.get('commercial_training_allowed') is True
                for c in cases), 'training data rights blocked')
    require(any(c['split'] == 'train' for c in cases) and any(c['split'] == 'holdout' for c in cases),
            'separate train and immutable holdout required')
    require(plan.get('inference_uses_gold') is False, 'reference leakage forbidden')
    require(plan.get('optimizer') and plan.get('trainable_modules'), 'explicit optimization scope required')
    return {'status': 'PLAN_VALIDATED_ONLY', 'training_executed': False,
            'production': 'PRODUCTION_NO_GO'}


if __name__ == '__main__':
    print(json.dumps(score_trial([], [], 'close', 'candidate', {}), indent=2))
