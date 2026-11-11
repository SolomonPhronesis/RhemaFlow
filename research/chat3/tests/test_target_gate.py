#!/usr/bin/env python3
"""Tests for the model-free card/target gate evaluator."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))

from target_gate import classify, gate_metrics, sweep  # noqa: E402


def rec(kind, ref=None, verse='John 3:16', conf=1.0):
    return {'card_kind': kind, 'card_ref': ref, 'verse_id': verse, 'card_confidence': conf}


class ClassifyTests(unittest.TestCase):
    def test_correct(self):
        self.assertEqual(classify(rec('QUOTE', 'John 3:16')), 'correct')

    def test_wrong(self):
        self.assertEqual(classify(rec('QUOTE', 'Psalms 23:1')), 'wrong')

    def test_review_and_none(self):
        self.assertEqual(classify(rec('REVIEW')), 'review')
        self.assertEqual(classify(rec('NO_CARD')), 'none')
        self.assertEqual(classify({}), 'none')

    def test_quote_without_ref_is_review(self):
        self.assertEqual(classify(rec('QUOTE', None)), 'review')


class GateTests(unittest.TestCase):
    def setUp(self):
        self.records = [rec('QUOTE', 'John 3:16', conf=0.95),
                        rec('QUOTE', 'John 3:16', conf=0.6),
                        rec('QUOTE', 'Psalms 23:1', conf=0.90),
                        rec('REVIEW', None, conf=0.0),
                        rec('NO_CARD', None, conf=0.0)]

    def test_ungated(self):
        m = gate_metrics(self.records)
        self.assertEqual((m['correct'], m['wrong'], m['review'], m['none']), (2, 1, 1, 1))
        self.assertEqual(m['recall'], 1.0)
        self.assertAlmostEqual(m['precision'], 2 / 3, places=4)

    def test_gate_removes_wrong_only_when_below_threshold(self):
        m = gate_metrics(self.records, threshold=0.95)
        self.assertEqual(m['correct'], 1)
        self.assertEqual(m['wrong'], 0)
        self.assertEqual(m['wrong_removed'], 1)
        self.assertEqual(m['correct_lost'], 1)
        self.assertEqual(m['recall'], 0.5)

    def test_gate_below_all_keeps_everything(self):
        m = gate_metrics(self.records, threshold=0.5)
        self.assertEqual(m['kept'], 3)
        self.assertEqual(m['correct_lost'], 0)

    def test_no_cards_precision_is_none(self):
        m = gate_metrics([rec('NO_CARD')], threshold=0.8)
        self.assertIsNone(m['precision'])
        self.assertIsNone(m['recall'])

    def test_sweep_shape(self):
        rows = sweep(self.records, [0.0, 0.9])
        self.assertEqual(len(rows), 2)
        self.assertIn('recall', rows[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
