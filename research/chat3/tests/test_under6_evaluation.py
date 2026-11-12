"""All fixtures are authored/model-free; passing tests are not church accuracy."""
import copy
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from under6_evaluation import (audit_splits, inference_envelope, score_trial,
                              validate_training_plan)
from qwen_base_stream import PseudoStreamingBase


def fixtures():
    cases, rows = [], []
    for n in range(3):
        case = {'case_id': f'opaque{n}', 'church_id': f'church{n}', 'session_id': f'service{n}',
                'speaker_ids': [f'target{n}', f'other{n}'], 'split': 'holdout',
                'source_sha256': str(n) * 64, 'rights_status': 'verified',
                'research_allowed': True, 'commercial_training_allowed': True,
                'evidence_class': 'MODEL_FREE', 'gold_text': 'one two three four five six seven eight nine ten',
                'has_target': True, 'expected_card_events': {'g1': 'John 3:16'},
                'channels': [{'role': role, 'path': role + '.wav', 'sha256': str(n) * 64,
                              'sample_rate': 48000, 'samples': 48000, 'clock_id': 'clock' + str(n)}
                             for role in ('close', 'room')]}
        cases.append(case)
        for model in ('close', 'candidate'):
            rows.append({'case_id': case['case_id'], 'model_id': model, 'status': 'OK',
                         'source_sha256': case['source_sha256'],
                         'source_channel_sha256': {c['role']: c['sha256'] for c in case['channels']},
                         'text': case['gold_text'] if model == 'candidate' else 'wrong ' + ' '.join(case['gold_text'].split()[1:]),
                         'cards': [{'kind': 'QUOTE', 'verse_ref': 'John 3:16', 'gold_event_id': 'g1',
                                    'attribution': 'target'}]})
    control = copy.deepcopy(cases[0])
    control.update(case_id='negative', split='control', has_target=False, gold_text='', expected_card_events={})
    cases.append(control)
    for model in ('close', 'candidate'):
        rows.append({'case_id': 'negative', 'model_id': model, 'status': 'OK',
                     'source_sha256': control['source_sha256'],
                     'source_channel_sha256': {c['role']: c['sha256'] for c in control['channels']},
                     'text': 'other speaker can quote scripture', 'cards': []})
    return cases, rows


class UnderSixTests(unittest.TestCase):
    def score(self, cases=None, rows=None):
        if cases is None:
            cases, rows = fixtures()
        return score_trial(cases, rows, 'close', 'candidate', {'evidence_class': 'MODEL_FREE'})

    def test_empty_real_data_is_blocked_not_zero_wer(self):
        result = self.score([], [])
        self.assertEqual(result['status'], 'BLOCKED_GOLD')
        self.assertIsNone(result['corpus_wer_pct'])

    def test_perfect_authored_text_cannot_pass_real_goal(self):
        result = self.score()
        self.assertEqual(result['corpus_wer_pct'], 0)
        self.assertFalse(result['goal_met'])
        self.assertFalse(result['gates']['real_independent_gold'])
        self.assertFalse(result['gates']['run_provenance_complete'])
        self.assertEqual(result['production'], 'PRODUCTION_NO_GO')

    def test_wrong_no_target_review_counts_as_card_failure(self):
        cases, rows = fixtures()
        rows[-1]['cards'] = [{'kind': 'REVIEW', 'verse_ref': 'Luke 1:17', 'gold_event_id': None,
                             'attribution': 'other'}]
        result = self.score(cases, rows)
        self.assertEqual(result['no_target_cards'], 1)
        self.assertFalse(result['gates']['zero_no_target_cards'])

    def test_matching_verse_from_other_speaker_is_not_correct(self):
        cases, rows = fixtures()
        rows[1]['cards'][0]['attribution'] = 'other'
        result = self.score(cases, rows)
        self.assertAlmostEqual(result['retention'], 2/3)
        self.assertFalse(result['gates']['no_extra_false_cards'])

    def test_suppression_all_cards_fails_retention(self):
        cases, rows = fixtures()
        for row in rows:
            if row['model_id'] == 'candidate': row['cards'] = []
        self.assertEqual(self.score(cases, rows)['retention'], 0)

    def test_unknown_cards_not_reported_as_zero(self):
        cases, rows = fixtures(); rows[-1]['cards'] = None
        result = self.score(cases, rows)
        self.assertIsNone(result['no_target_cards'])
        self.assertIsNone(result['retention'])

    def test_coverage_and_input_hash_mismatch_rejected(self):
        cases, rows = fixtures()
        with self.assertRaises(ValueError): self.score(cases, rows[:-1])
        rows[0]['source_channel_sha256']['room'] = 'a'*64
        with self.assertRaises(ValueError): self.score(cases, rows)

    def test_connected_cluster_interval_and_seed_reproducible(self):
        first = self.score()['paired_gain_95_ci']
        self.assertEqual(first, self.score()['paired_gain_95_ci'])
        self.assertEqual(first['clusters'], 3)
        cases, rows = fixtures()
        for case in cases: case['church_id'] = 'one-related-church'
        result = self.score(cases, rows)
        self.assertIsNone(result['paired_gain_95_ci']['low_pp'])
        self.assertFalse(result['gates']['paired_interval_available'])

    def test_corpus_wer_is_sum_edits_over_sum_words(self):
        cases, rows = fixtures()
        cases[0]['gold_text'] = 'one'
        rows[0]['text'] = 'wrong'; rows[1]['text'] = ''
        result = self.score(cases, rows)
        self.assertEqual(result['reference_words'], 21)
        self.assertAlmostEqual(result['corpus_wer_pct'], 100/21)

    def test_church_speaker_and_augmentation_leakage_rejected(self):
        for field, value in [('church_id', 'church0'), ('speaker_ids', ['target0']),
                             ('parent_source_sha256', '0'*64)]:
            cases, _ = fixtures(); train = copy.deepcopy(cases[1]); train.update(case_id='train', split='train')
            train[field] = value
            with self.assertRaises(ValueError): audit_splits(cases+[train])

    def test_request_omits_gold_speaker_and_injected_channel_label(self):
        cases, _ = fixtures(); case = cases[0]
        case['channels'][0]['gold'] = 'SECRET GOLD'
        model = {'family': 'parakeet-v2-q8', 'precision': 'q8_0', 'sha256': 'a'*64,
                 'tokenizer_sha256': 'b'*64}
        request = inference_envelope(case, model)
        self.assertNotIn('speaker_ids', request)
        self.assertNotIn('gold', str(request))
        self.assertNotIn(case['case_id'], request['request_id'])
        case['rights_status'] = 'pending'
        with self.assertRaises(ValueError): inference_envelope(case, model)

    def test_restricted_teacher_and_missing_training_rights_rejected(self):
        cases, _ = fixtures()
        train = copy.deepcopy(cases[1]); train.update(case_id='training', split='train', church_id='trainchurch',
                                                      session_id='trainservice', speaker_ids=['trainspeaker'], source_sha256='f'*64)
        plan = {'teacher_models': [], 'base_family': 'qwen3-asr-base', 'commercial_base_reviewed': True,
                **{k: 'a'*64 for k in ('base_weights_sha256', 'tokenizer_sha256', 'frozen_holdout_sha256', 'config_sha256')},
                'inference_uses_gold': False, 'optimizer': 'AdamW', 'trainable_modules': ['decoder.q_proj']}
        self.assertFalse(validate_training_plan(plan, [cases[0], train])['training_executed'])
        plan['teacher_models'] = ['Confucius4-R2T2']
        with self.assertRaises(ValueError): validate_training_plan(plan, [cases[0], train])
        plan['teacher_models'] = []; train['commercial_training_allowed'] = False
        with self.assertRaises(ValueError): validate_training_plan(plan, [cases[0], train])

    def test_adversarial_future_suffix_cannot_change_past_decoder_input(self):
        for cut in (1, 4, 7, 8, 12):
            variants = [np.linspace(0, .5, 16, dtype=np.float32) for _ in range(2)]
            variants[1][cut:] = -.8
            observed = []
            for pcm in variants:
                seen = []
                def decoder(prefix, request_id):
                    seen.append(prefix.copy())
                    return {'request_id': request_id, 'model_id': 'authored-mock', 'text': ''}
                stream = PseudoStreamingBase(decoder, model_id='authored-mock', chunk_samples=4)
                stream.push(pcm); observed.append(seen)
            for a, b in zip(*observed):
                if len(a) <= cut: np.testing.assert_array_equal(a, b)


if __name__ == '__main__': unittest.main()
