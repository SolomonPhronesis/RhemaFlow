#!/usr/bin/env python3
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_pbfdaf_evidence import card_audit, legacy_causality


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


if __name__ == '__main__':
    unittest.main(verbosity=2)
