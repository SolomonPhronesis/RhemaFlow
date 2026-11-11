#!/usr/bin/env python3
"""Tests for the independent stable-prefix prototype (no models, no audio).

Run: python3 research/chat3/tests/test_streaming.py -v
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))

from stable_prefix import CardGate, Divergence, ProtocolError, StablePrefix, normalise, parse_reply  # noqa: E402

SENTENCE = ('for god so loved the world that he gave his only begotten son '
            'that whosoever believeth in him should not perish but have everlasting life')


class CommitTests(unittest.TestCase):
    def test_repeated_words_are_not_dropped_or_duplicated(self):
        sp = StablePrefix(holdback=1)
        for text in ['the', 'the the', 'the the lord', 'the the lord is']:
            sp.update(text)
        sp.final('the the lord is')
        self.assertEqual(sp.text(), 'the the lord is')

    def test_committed_prefix_never_changes(self):
        sp = StablePrefix(holdback=1, lookahead_updates=0)
        seen = []
        words = SENTENCE.split()
        for i in range(1, len(words) + 1):
            sp.update(' '.join(words[:i]))
            seen.append(sp.text())
        for a, b in zip(seen, seen[1:]):
            self.assertTrue(b.startswith(a), f'prefix changed: {a!r} -> {b!r}')

    def test_punctuation_and_unicode_apostrophes(self):
        self.assertEqual(normalise('God\u2019s'), normalise("God's"))
        sp = StablePrefix(holdback=0, lookahead_updates=0)
        sp.update('God\u2019s love')
        sp.update("God's love endures")
        sp.final("God's love endures")
        self.assertEqual(sp.text(), "God's love endures")

    def test_partial_word_is_replaced_not_duplicated(self):
        sp = StablePrefix(holdback=1, lookahead_updates=0)
        sp.update('and have everlast')
        sp.update('and have everlasting life')
        sp.final('and have everlasting life')
        self.assertEqual(sp.text(), 'and have everlasting life')

    def test_filler_is_preserved_verbatim(self):
        sp = StablePrefix(holdback=1, lookahead_updates=0)
        for t in ['um', 'um the', 'um the lord']:
            sp.update(t)
        sp.final('um the lord')
        self.assertEqual(sp.text(), 'um the lord')

    def test_silence_commits_nothing(self):
        sp = StablePrefix(holdback=1, lookahead_updates=0)
        sp.update('the lord')
        before = sp.text()
        for _ in range(5):
            self.assertEqual(sp.update(''), [])
        self.assertEqual(sp.text(), before)

    def test_abrupt_cutoff_raises_and_keeps_committed(self):
        sp = StablePrefix(holdback=0, lookahead_updates=0)
        sp.update('for god so loved')
        committed = sp.text()
        with self.assertRaises(Divergence):
            sp.update('for god')
        self.assertEqual(sp.text(), committed)

    def test_speaker_handoff_is_rejected(self):
        sp = StablePrefix(holdback=0, lookahead_updates=0)
        sp.update('for god so loved the world')
        committed = sp.text()
        with self.assertRaises(Divergence):
            sp.update("let's see that in the new living translation")
        self.assertEqual(sp.text(), committed)

    def test_long_utterance_grows_monotonically(self):
        sp = StablePrefix(holdback=1, lookahead_updates=0)
        words = SENTENCE.split() * 3
        last = 0
        for i in range(1, len(words) + 1):
            sp.update(' '.join(words[:i]))
            self.assertGreaterEqual(len(sp.committed), last)
            last = len(sp.committed)
        sp.final(' '.join(words))
        self.assertEqual(sp.text(), ' '.join(words))

    def test_holdback_values(self):
        for hb, expected in [(0, 'for god so loved'), (1, 'for god so'), (2, 'for god')]:
            sp = StablePrefix(holdback=hb, lookahead_updates=0)
            sp.update('for god so loved')
            self.assertEqual(sp.text(), expected, f'holdback {hb}')

    def test_initial_lookahead_delays_commit(self):
        sp = StablePrefix(holdback=0, lookahead_updates=2)
        sp.update('for god')
        sp.update('for god so')
        self.assertEqual(sp.text(), '')
        sp.update('for god so loved')
        self.assertTrue(sp.text().startswith('for god so'))


class ProtocolTests(unittest.TestCase):
    def test_valid_reply(self):
        self.assertEqual(parse_reply('{"id": 1, "ok": true, "text": "hello"}', 1)['text'], 'hello')

    def test_malformed_json(self):
        with self.assertRaises(ProtocolError) as cm:
            parse_reply('{not json', 1)
        self.assertEqual(cm.exception.code, 'malformed_json')

    def test_stale_id(self):
        with self.assertRaises(ProtocolError) as cm:
            parse_reply('{"id": 9, "ok": true, "text": "x"}', 1)
        self.assertEqual(cm.exception.code, 'stale_id')

    def test_error_reply(self):
        with self.assertRaises(ProtocolError) as cm:
            parse_reply('{"id": 1, "ok": false, "error": "boom"}', 1)
        self.assertEqual(cm.exception.code, 'not_ok')

    def test_empty_text(self):
        with self.assertRaises(ProtocolError) as cm:
            parse_reply('{"id": 1, "ok": true, "text": "   "}', 1)
        self.assertEqual(cm.exception.code, 'empty_text')


class CardGateTests(unittest.TestCase):
    def test_duplicate_card_suppressed(self):
        g = CardGate()
        self.assertTrue(g.consider('John 3:16'))
        self.assertFalse(g.consider('John 3:16'))
        self.assertTrue(g.consider('Psalms 23:1'))

    def test_pending_duplicate_suppressed(self):
        g = CardGate()
        self.assertTrue(g.consider('Romans 8:28', pending=True))
        self.assertFalse(g.consider('Romans 8:28', pending=True))
        self.assertTrue(g.consider('Romans 8:28'))

    def test_empty_ref_ignored(self):
        g = CardGate()
        self.assertFalse(g.consider(''))
        self.assertFalse(g.consider(None))


class NoAudioLeakageTests(unittest.TestCase):
    def test_module_has_no_audio_or_file_io(self):
        path = os.path.join(HERE, '..', 'scripts', 'stable_prefix.py')
        with open(path, encoding='utf-8') as fh:
            src = fh.read()
        for banned in ('import wave', 'import audio', 'soundfile', 'open(', 'subprocess', 'requests'):
            self.assertNotIn(banned, src, f'{banned} must not appear in the prototype')


if __name__ == '__main__':
    unittest.main(verbosity=2)
