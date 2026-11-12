#!/usr/bin/env python3
import copy
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from rf_research_audio import SCHEMA, validate_case, inference_request, CardEventConsumer, score_paired


def fixture(case_id='TARGET', target=True):
    return {'schema': SCHEMA, 'case_id': case_id, 'session_id': 'synthetic', 'speaker_id': 'procedural',
            'condition': 'word-fixture', 'evidence_class': 'MODEL_FREE_SYNTHETIC', 'split': 'holdout' if target else 'control',
            'rights_status': 'verified', 'research_allowed': True,
            'channels': [{'role': 'close', 'path': 'audio/procedural.wav', 'sha256': '0'*64,
                          'sample_rate': 16000, 'samples': 16000, 'clock_id': 'same-clock'}],
            'expected': {'has_target': target, 'gold_text': 'one two' if target else '', 'verse_ref': 'Test 1:1'}}


class ContractTests(unittest.TestCase):
    def test_producer_excludes_gold_speaker_labels_and_expected_refs(self):
        model = {'id': 'local-qwen', 'family': 'qwen3-asr-1.7b-base', 'precision': '4bit-embed8', 'sha256': '1'*64}
        r = inference_request(fixture(), model, 1)
        self.assertEqual(set(r), {'schema', 'request_id', 'case_id', 'channels', 'model'})

    def test_pending_rights_block_inference(self):
        case = fixture(); case['rights_status'] = 'pending'
        with self.assertRaises(ValueError): inference_request(case, {}, 1)

    def test_r2t2_model_family_rejected(self):
        with self.assertRaises(ValueError): inference_request(fixture(), {'family': 'r2t2'}, 1)

    def test_wrong_precision_family_rejected(self):
        model = {'id': 'q4', 'family': 'parakeet-v2-q4', 'precision': 'bf16', 'sha256': '1'*64}
        with self.assertRaises(ValueError): inference_request(fixture(), model, 1)

    def test_wrong_clock_rejected(self):
        case = fixture(); room = dict(case['channels'][0], role='room', clock_id='different')
        case['channels'].append(room)
        with self.assertRaises(ValueError): validate_case(case)

    def test_unsafe_path_rejected(self):
        for path in ('../audio.wav', '/tmp/audio.wav', 'a\\b.wav'):
            case = fixture(); case['channels'][0]['path'] = path
            with self.assertRaises(ValueError): validate_case(case)

    def test_missing_target_label_rejected(self):
        case = fixture(); del case['expected']['has_target']
        with self.assertRaises(ValueError): validate_case(case)

    def test_no_target_gold_cannot_be_nonempty(self):
        case = fixture(target=False); case['expected']['gold_text'] = 'other speaker'
        with self.assertRaises(ValueError): validate_case(case)

    def event(self):
        return {'schema': SCHEMA, 'card_id': 'session:1', 'kind': 'QUOTE', 'verse_ref': 'Test 1:1',
                'audio_end_ms': 10, 'asr_done_ms': 20, 'matcher_done_ms': 30, 'card_visible_ms': None,
                'committed_text_sha256': hashlib.sha256(b'one two').hexdigest()}

    def test_consumer_deduplicates_identical_cards(self):
        c = CardEventConsumer(); e = self.event()
        self.assertTrue(c.accept(e, committed_text='one two'))
        self.assertFalse(c.accept(e, committed_text='one two'))

    def test_consumer_rejects_rewriting_emitted_card(self):
        c = CardEventConsumer(); e = self.event(); c.accept(e, committed_text='one two')
        e['verse_ref'] = 'Test 2:2'
        with self.assertRaises(ValueError): c.accept(e, committed_text='one two')

    def test_consumer_rejects_uncommitted_or_visible_claim(self):
        with self.assertRaises(ValueError): CardEventConsumer().accept(self.event(), committed_text='different')
        e = self.event(); e['card_visible_ms'] = 31
        with self.assertRaises(ValueError): CardEventConsumer().accept(e, committed_text='one two')

    def records(self):
        return [{'case_id': cid, 'model_id': model, 'status': 'OK', 'input_sha256': '0'*64,
                 'text': 'one two' if cid == 'TARGET' else 'other voice', 'cards': None}
                for cid in ('TARGET', 'CTRL') for model in ('base', 'candidate')]

    def test_empty_references_separately_counted(self):
        result = score_paired([fixture(), fixture('CTRL', False)], self.records(), ['base', 'candidate'], 'base')
        row = result['models']['base']
        self.assertEqual(row['reference_words'], 2); self.assertEqual(row['words_on_no_target'], 2)
        self.assertIsNone(row['wrong_quotes'])

    def test_missing_duplicate_and_wrong_hash_rejected(self):
        cases = [fixture(), fixture('CTRL', False)]
        for mode in ('missing', 'duplicate', 'hash'):
            records = self.records()
            if mode == 'missing': records.pop()
            if mode == 'duplicate': records.append(dict(records[0]))
            if mode == 'hash': records[0]['input_sha256'] = 'f'*64
            with self.assertRaises(ValueError): score_paired(cases, records, ['base', 'candidate'], 'base')

    def test_other_speaker_quote_is_wrong_even_when_verse_matches(self):
        records = self.records()
        for row in records: row['cards'] = [{'kind': 'QUOTE', 'verse_ref': 'Test 1:1'}]
        result = score_paired([fixture(), fixture('CTRL', False)], records, ['base', 'candidate'], 'base')
        self.assertEqual(result['models']['base']['wrong_quotes'], 1)
        self.assertEqual(result['models']['base']['correct_quotes'], 1)
        self.assertEqual(result['models']['base']['no_target_emitted_cards'], 1)

    def test_paired_bootstrap_uses_corpus_edit_counts(self):
        cases = [fixture()]
        records = [r for r in self.records() if r['case_id'] == 'TARGET']
        records[1]['text'] = 'one'
        result = score_paired(cases, records, ['base', 'candidate'], 'base')
        self.assertEqual(result['models']['candidate']['wer_pct'], 50)
        self.assertEqual(result['paired_wer_gain_vs_baseline']['candidate']['ci_low'], -50)

    def test_timing_coverage_and_rtf_are_explicit(self):
        records = self.records()
        for row in records:
            row['timing'] = {'decode_wall_ms': 100, 'audio_duration_ms': 1000, 'end_to_end_ms': None}
        result = score_paired([fixture(), fixture('CTRL', False)], records, ['base', 'candidate'], 'base')
        self.assertEqual(result['models']['base']['rtf'], .1)
        self.assertEqual(result['models']['base']['latency']['decode_wall_ms']['p95'], 100)
        self.assertIsNone(result['models']['base']['latency']['end_to_end_ms']['p95'])

    def test_tune_and_empty_sets_are_not_evaluated_as_holdout(self):
        case = fixture(); case['split'] = 'tune'
        with self.assertRaises(ValueError): score_paired([case], [], ['base', 'candidate'], 'base')
        with self.assertRaises(ValueError): score_paired([], [], ['base', 'candidate'], 'base')

    def test_room_hash_must_also_match(self):
        cases = [fixture()]; cases[0]['channels'].append(dict(cases[0]['channels'][0], role='room', sha256='2'*64))
        records = [r for r in self.records() if r['case_id'] == 'TARGET']
        with self.assertRaises(ValueError): score_paired(cases, records, ['base', 'candidate'], 'base')

    def test_augmentation_clusters_and_correct_card_loss_are_paired(self):
        a, b = fixture('A'), fixture('B'); a['cluster_id'] = b['cluster_id'] = 'same-source'
        rows = [{'case_id': cid, 'model_id': model, 'status': 'OK', 'input_sha256': '0'*64,
                 'text': 'one two', 'cards': [{'kind': 'QUOTE', 'verse_ref': 'Test 1:1'}] if model == 'base' or cid == 'A' else []}
                for cid in ('A', 'B') for model in ('base', 'candidate')]
        result = score_paired([a, b], rows, ['base', 'candidate'], 'base')
        self.assertEqual(result['paired_wer_gain_vs_baseline']['candidate']['clusters'], 1)
        self.assertEqual(result['correct_card_case_retention_vs_baseline']['candidate']['lost_pct'], 50)


if __name__ == '__main__': unittest.main(verbosity=2)
