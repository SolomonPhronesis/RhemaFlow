#!/usr/bin/env python3
from pathlib import Path
import sys
import unittest
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from qwen_base_stream import Policy, PrefixCommitter, PseudoStreamingBase, StreamError


class CommitTests(unittest.TestCase):
    def test_two_observations_required(self):
        c = PrefixCommitter(Policy(0))
        self.assertEqual(c.observe(['a'], request_id=1, audio_samples=1)['delta'], '')
        self.assertEqual(c.observe(['a'], request_id=2, audio_samples=2)['delta'], 'a')

    def test_holdback_zero_and_one(self):
        for hold, expected in [(0, 'one two'), (1, 'one')]:
            c = PrefixCommitter(Policy(hold))
            for n in (1, 2): event = c.observe(['one', 'two'], request_id=n, audio_samples=n)
            self.assertEqual(event['committed_text'], expected)

    def test_final_releases_suffix(self):
        c = PrefixCommitter()
        c.observe(['a', 'b'], request_id=1, audio_samples=1)
        self.assertEqual(c.observe(['a', 'b'], request_id=2, audio_samples=2, final=True)['committed_text'], 'a b')

    def test_committed_display_never_changes_case_or_punctuation(self):
        c = PrefixCommitter(Policy(0))
        for n in (1, 2): c.observe(['God’s', 'word.'], request_id=n, audio_samples=n)
        with self.assertRaises(StreamError): c.observe(["God's", 'word'], request_id=3, audio_samples=3)
        self.assertEqual(c.text, 'God’s word.')

    def test_repeated_words_remain(self):
        c = PrefixCommitter(Policy(0))
        for n in (1, 2): c.observe(['very', 'very', 'clear'], request_id=n, audio_samples=n)
        self.assertEqual(c.text, 'very very clear')

    def test_revision_before_commit_can_recover(self):
        c = PrefixCommitter(Policy(0))
        c.observe(['red', 'cup'], request_id=1, audio_samples=1)
        c.observe(['red', 'cap'], request_id=2, audio_samples=2)
        c.observe(['red', 'cap'], request_id=3, audio_samples=3)
        self.assertEqual(c.text, 'red cap')

    def test_speaker_handoff_divergence_rejected(self):
        c = PrefixCommitter(Policy(0))
        for n in (1, 2): c.observe(['first', 'voice'], request_id=n, audio_samples=n)
        with self.assertRaises(StreamError): c.observe(['other', 'voice'], request_id=3, audio_samples=3)

    def test_stable_other_voice_still_commits(self):
        c = PrefixCommitter(Policy(0))
        for n in (1, 2): c.observe(['other', 'preacher'], request_id=n, audio_samples=n)
        self.assertEqual(c.text, 'other preacher')  # Stability is not speaker identity.

    def test_stale_request_and_regressing_time(self):
        c = PrefixCommitter(); c.observe([], request_id=1, audio_samples=10)
        with self.assertRaises(StreamError): c.observe([], request_id=1, audio_samples=11)
        with self.assertRaises(StreamError): c.observe([], request_id=2, audio_samples=9)

    def test_truncated_final_rejected(self):
        c = PrefixCommitter(Policy(0))
        for n in (1, 2): c.observe(['keep', 'me'], request_id=n, audio_samples=n)
        with self.assertRaises(StreamError): c.observe(['keep'], request_id=3, audio_samples=3, final=True)

    def test_true_token_id_budget(self):
        vocab = {1: 'ab', 2: 'cd', 3: 'ef'}
        c = PrefixCommitter(Policy(1, 'model_tokens'), lambda ids: ''.join(vocab[i] for i in ids))
        for n in (1, 2): c.observe([1, 2, 3], request_id=n, audio_samples=n)
        self.assertEqual(c.committed, (1, 2)); self.assertEqual(c.text, 'abcd')

    def test_tokenizer_byte_rewrite_rejected(self):
        decode = lambda ids: '' if not ids else ('old' if len(ids) == 1 else 'new')
        c = PrefixCommitter(Policy(0, 'model_tokens'), decode)
        for n in (1, 2): c.observe([1], request_id=n, audio_samples=n)
        with self.assertRaises(StreamError): c.observe([1, 2], request_id=3, audio_samples=3, final=True)

    def test_oversized_and_invalid_units_rejected(self):
        c = PrefixCommitter(Policy(max_units=2))
        for units in ([1], ['a', 'b', 'c']):
            with self.assertRaises(StreamError): c.observe(units, request_id=1, audio_samples=1)


class AdapterTests(unittest.TestCase):
    def decoder(self, pcm, request_id):
        self.assertFalse(pcm.flags.writeable)
        return {'request_id': request_id, 'model_id': 'mock-base', 'text': 'a b'}

    def test_chunks_share_state_and_exact_boundary_finishes(self):
        s = PseudoStreamingBase(self.decoder, model_id='mock-base', chunk_samples=4)
        self.assertEqual(s.push(np.zeros(3)), [])
        s.push(np.zeros(5))
        self.assertEqual(s.finish()['committed_text'], 'a b')

    def test_future_samples_never_reach_decoder_early(self):
        seen = []
        def decoder(pcm, rid):
            seen.append(pcm.copy()); return {'request_id': rid, 'model_id': 'mock', 'text': ''}
        s = PseudoStreamingBase(decoder, model_id='mock', chunk_samples=4)
        s.push(np.arange(8, dtype=np.float32)/10)
        np.testing.assert_array_equal(seen[0], np.arange(4, dtype=np.float32)/10)

    def test_no_audio_finish_never_calls_model(self):
        s = PseudoStreamingBase(lambda *args: self.fail('empty input decoded'), model_id='mock')
        self.assertEqual(s.finish()['committed_text'], '')

    def test_stale_wrong_model_and_malformed_replies_rejected(self):
        for reply in ({'request_id': 0, 'model_id': 'mock', 'text': ''},
                      {'request_id': 1, 'model_id': 'other', 'text': ''}, {'text': ''}, None):
            s = PseudoStreamingBase(lambda *args: reply, model_id='mock', chunk_samples=1)
            with self.assertRaises(StreamError): s.push(np.zeros(1))

    def test_pcm_shape_and_nonfinite_rejected(self):
        for pcm in (np.zeros((2, 2)), [np.nan], [np.inf], [2.]):
            s = PseudoStreamingBase(self.decoder, model_id='mock-base', chunk_samples=1)
            with self.assertRaises(StreamError): s.push(pcm)

    def test_memory_bound_requires_endpoint(self):
        s = PseudoStreamingBase(self.decoder, model_id='mock-base', chunk_samples=4, max_seconds=.001)
        with self.assertRaises(StreamError): s.push(np.zeros(17))
        self.assertEqual(s.received, 0)

    def test_finished_stream_cannot_restart(self):
        s = PseudoStreamingBase(self.decoder, model_id='mock-base'); s.finish()
        with self.assertRaises(StreamError): s.push([])
        with self.assertRaises(StreamError): s.finish()


if __name__ == '__main__': unittest.main(verbosity=2)
