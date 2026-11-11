#!/usr/bin/env python3
"""Fixture tests for the WER scorer (research/chat3/scripts/wer.py).

Run: python3 research/chat3/tests/test_wer.py -v
"""
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, '..', 'scripts')
sys.path.insert(0, SCRIPTS)

import wer  # noqa: E402


def independent_distance(a, b):
    """Second implementation: two-row DP, no backtrace, no shared code with wer.edit_counts."""
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return prev[-1]


class TokenTests(unittest.TestCase):
    def test_splits_phrase(self):
        self.assertEqual(wer.tokens('for god so loved the world'),
                         ['for', 'god', 'so', 'loved', 'the', 'world'])

    def test_unicode_punctuation(self):
        self.assertEqual(wer.tokens('God’s love—endures.'),
                         ["god's", 'love', 'endures'])

    def test_numbers(self):
        self.assertEqual(wer.tokens('John 3:16'), ['john', '3', '16'])

    def test_verbatim_mode_keeps_punctuation(self):
        self.assertNotEqual(wer.tokens('end, now.', 'verbatim'), ['end', 'now'])
        self.assertEqual(wer.tokens('end, now.', 'verbatim'), ['end,', 'now.'])


class EditCountTests(unittest.TestCase):
    def test_identical(self):
        self.assertEqual(wer.edit_counts(['a', 'b', 'c'], ['a', 'b', 'c']), (0, 0, 0, 0))

    def test_one_substitution(self):
        self.assertEqual(wer.edit_counts(['a', 'b', 'c'], ['a', 'x', 'c']), (1, 0, 0, 1))

    def test_one_deletion(self):
        self.assertEqual(wer.edit_counts(['a', 'b', 'c'], ['a', 'c']), (0, 1, 0, 1))

    def test_one_insertion(self):
        self.assertEqual(wer.edit_counts(['a', 'c'], ['a', 'b', 'c']), (0, 0, 1, 1))

    def test_empty_hypothesis(self):
        self.assertEqual(wer.edit_counts(['a', 'b'], []), (0, 2, 0, 2))

    def test_empty_reference(self):
        self.assertEqual(wer.edit_counts([], ['x', 'y']), (0, 0, 2, 2))

    def test_counts_match_independent_distance(self):
        rng = random.Random(5)
        alphabet = ['a', 'b', 'c', 'the', 'lord']
        for _ in range(200):
            ref = [rng.choice(alphabet) for _ in range(rng.randint(0, 9))]
            hyp = [rng.choice(alphabet) for _ in range(rng.randint(0, 9))]
            s, d, i, dist = wer.edit_counts(ref, hyp)
            self.assertEqual(s + d + i, dist)
            self.assertEqual(dist, independent_distance(ref, hyp))


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='wertest_')
        self.gold = os.path.join(self.tmp, 'gold.csv')
        with open(self.gold, 'w') as f:
            f.write('case_id,gold_text\n0001,for god so loved the world\n0002,the lord is my shepherd\n')

    def write(self, name, lines):
        p = os.path.join(self.tmp, name)
        with open(p, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        return p

    def test_repeated_identical_gold_rows_allowed_conflicting_rejected(self):
        with open(self.gold, 'a') as f:
            f.write('0001,for god so loved the world\n')
        self.assertEqual(wer.main(['--gold', self.gold, '--jsonl', self.write(
            't.jsonl', [json.dumps({'case_id': '0001', 'text': 'for god so loved the world'})])]), 0)
        with open(self.gold, 'a') as f:
            f.write('0001,a different text\n')
        with self.assertRaises(SystemExit):
            wer.main(['--gold', self.gold, '--jsonl', self.write(
                't2.jsonl', [json.dumps({'case_id': '0001', 'text': 'x'})])])

    def test_corpus_wer(self):
        j = self.write('t.jsonl', [json.dumps({'case_id': '0001', 'text': 'for god so loved a world'}),
                                   json.dumps({'case_id': '0002', 'text': 'the lord is my shepherd'})])
        r = wer.main(['--gold', self.gold, '--jsonl', j, '--json'])
        self.assertEqual(r, 0)

    def test_duplicate_ids_rejected(self):
        j = self.write('t.jsonl', [json.dumps({'case_id': '0001', 'text': 'x'}),
                                   json.dumps({'case_id': '0001', 'text': 'y'})])
        with self.assertRaises(SystemExit):
            wer.main(['--gold', self.gold, '--jsonl', j])

    def test_missing_gold_fails_closed(self):
        j = self.write('t.jsonl', [json.dumps({'case_id': '9999', 'text': 'x'})])
        self.assertEqual(wer.main(['--gold', self.gold, '--jsonl', j]), 2)

    def test_truncated_jsonl_rejected(self):
        j = self.write('t.jsonl', ['{"case_id": "0001", "text": "x"'])
        with self.assertRaises(SystemExit):
            wer.main(['--gold', self.gold, '--jsonl', j])

    def test_composite_key_allows_same_case_in_two_conditions(self):
        j = self.write('t.jsonl', [
            json.dumps({'case_id': '0001', 'condition': 'clean', 'text': 'for god so loved the world'}),
            json.dumps({'case_id': '0001', 'condition': 'overlap_0', 'text': 'for god so loved the world'})])
        self.assertEqual(wer.main(['--gold', self.gold, '--jsonl', j, '--key', 'case_id,condition']), 0)
        with self.assertRaises(SystemExit):
            wer.main(['--gold', self.gold, '--jsonl', j])

    def test_empty_reference_excluded_from_wer_but_reported(self):
        with open(self.gold, 'a') as f:
            f.write('0003,\n')
        j = self.write('t.jsonl', [json.dumps({'case_id': '0001', 'text': 'for god so loved the world'}),
                                   json.dumps({'case_id': '0003', 'text': 'false speech words here'})])
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = wer.main(['--gold', self.gold, '--jsonl', j, '--json'])
        payload = json.loads(buf.getvalue())
        self.assertEqual(rc, 0)
        self.assertEqual(payload['n_used'], 1)
        self.assertEqual(payload['n_empty_ref'], 1)
        self.assertEqual(payload['hyp_words_on_empty_ref'], 4)

    def test_exclude_conditions(self):
        j = self.write('t.jsonl', [
            json.dumps({'case_id': '0001', 'condition': 'clean', 'text': 'for god so loved the world'}),
            json.dumps({'case_id': '0002', 'condition': 'music_only', 'text': 'noise words'})])
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = wer.main(['--gold', self.gold, '--jsonl', j, '--key', 'case_id,condition',
                           '--exclude-conditions', 'music_only', '--json'])
        payload = json.loads(buf.getvalue())
        self.assertEqual(rc, 0)
        self.assertEqual(payload['n_used'], 1)
        self.assertEqual(payload['n_ref_words'], 6)

    def test_manifest_mapping(self):
        j = self.write('t.jsonl', [json.dumps({'file': '/tmp/0001_clean.wav', 'text': 'for god so loved the world'})])
        m = self.write('m.csv', ['file,case_id', '0001_clean.wav,0001'])
        self.assertEqual(wer.main(['--gold', self.gold, '--jsonl', j, '--manifest', m]), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
