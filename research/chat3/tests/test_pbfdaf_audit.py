#!/usr/bin/env python3
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_pbfdaf_evidence import card_audit, legacy_causality
from summarize_pbfdaf import summarize


class EvidenceAuditTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1]/'data/ctrl03_saved_detection.json'
        self.row = json.loads(path.read_text())

    def test_wrong_speaker_remains_wrong_even_when_verse_matches(self):
        self.row['verse_id'] = 'Luke 1:17'
        result = card_audit([self.row], ['CTRL03'])
        self.assertEqual(result['wrong_quotes'], 1)
        self.assertEqual(result['correct_quotes'], 0)

    def test_target_labels_and_negative_controls_are_both_retained(self):
        target = dict(self.row, case_id='TARGET01', has_target=True, verse_id='Luke 1:17')
        result = card_audit([self.row, target], ['CTRL03', 'TARGET01'])
        self.assertEqual(result['correct_quotes'], 1)
        self.assertEqual(result['wrong_quotes'], 1)
        self.assertGreater(result['words_on_no_target'], 0)

    def test_coverage_is_fail_closed(self):
        with self.assertRaises(ValueError): card_audit([], ['CTRL03'])
        with self.assertRaises(ValueError): card_audit([self.row, self.row], ['CTRL03'])

    def test_missing_target_annotation_is_rejected(self):
        del self.row['has_target']
        with self.assertRaises(ValueError): card_audit([self.row], ['CTRL03'])

    def test_legacy_lookahead_is_detected_without_hiding_it(self):
        result = legacy_causality()
        self.assertTrue(result['pbfdaf']['strict_source_time_prefix_pass'])
        for name in ('legacy_scalar', 'legacy_fir32', 'legacy_fir32_dt', 'legacy_tracking'):
            self.assertFalse(result[name]['strict_source_time_prefix_pass'])
        self.assertGreater(result['legacy_initial_calibration']['max_output_difference_before_mutation'], 1e-6)


class CoverageAuditTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1]/'data/pbfdaf_20261112/results.json'
        self.result = json.loads(path.read_text())

    def test_saved_complete_run_has_full_coverage(self):
        result = summarize(self.result)
        self.assertEqual(result['coverage']['pbfdaf']['observed_unique'], 40)
        self.assertIsNone(result['coverage']['pbfdaf']['transcript_coverage_pct'])

    def test_missing_pbfdaf_pair_is_rejected(self):
        self.result['rows'].pop()
        with self.assertRaises(ValueError): summarize(self.result)

    def test_duplicate_pair_is_rejected(self):
        self.result['rows'].append(dict(self.result['rows'][0]))
        with self.assertRaises(ValueError): summarize(self.result)

    def test_truncated_samples_and_missing_controls_are_rejected(self):
        row = self.result['rows'][0]
        row['samples_out'] -= 1
        with self.assertRaises(ValueError): summarize(self.result)
        row['samples_out'] += 1
        self.result['controls'].pop()
        with self.assertRaises(ValueError): summarize(self.result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
