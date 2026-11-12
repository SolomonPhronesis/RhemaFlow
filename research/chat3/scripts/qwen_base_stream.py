#!/usr/bin/env python3
"""Independent local-agreement wrapper for BASE-ASR hypotheses; no weights.

This is not learned R2T2 LSP or a learned Wait action. Words and actual tokenizer
IDs are separate unit modes. No reference transcript or speaker label is input.
"""
from dataclasses import dataclass
import math
import time

import numpy as np


class StreamError(ValueError):
    pass


@dataclass(frozen=True)
class Policy:
    holdback: int = 1
    unit_kind: str = 'words'
    max_units: int = 2048

    def __post_init__(self):
        if type(self.holdback) is not int or self.holdback < 0:
            raise ValueError('nonnegative integer holdback required')
        if self.unit_kind not in ('words', 'model_tokens') or type(self.max_units) is not int or self.max_units < 1:
            raise ValueError('invalid unit policy')


class PrefixCommitter:
    """Two-update local agreement with an immutable released sequence.

    Actual model_tokens mode requires IDs from the BASE model tokenizer and an
    injected decoder. Word mode never claims its budget equals R2T2's BPE U.
    """
    def __init__(self, policy=Policy(), decode=None):
        self.policy = policy
        if policy.unit_kind == 'model_tokens' and decode is None:
            raise ValueError('model-token mode requires a tokenizer decoder')
        self.decode = decode or (lambda units: ' '.join(units))
        if self.decode(()) != '': raise ValueError('tokenizer decoder must map an empty sequence to empty text')
        self.committed = ()
        self.previous = ()
        self.text = ''
        self.last_audio_samples = -1
        self.last_request_id = -1
        self.rejected = 0
        self.closed = False

    def observe(self, units, *, request_id, audio_samples, final=False):
        if self.closed: raise StreamError('utterance already finalized')
        if type(final) is not bool: raise StreamError('explicit boolean final required')
        if type(request_id) is not int or request_id <= self.last_request_id:
            raise StreamError('stale request ID')
        if type(audio_samples) is not int or audio_samples < 0 or audio_samples < self.last_audio_samples:
            raise StreamError('audio timestamp regression')
        if not isinstance(units, (tuple, list)) or len(units) > self.policy.max_units:
            raise StreamError('invalid or oversized hypothesis')
        expected = str if self.policy.unit_kind == 'words' else int
        if any(type(u) is not expected or (expected is str and not u) or (expected is int and u < 0) for u in units):
            raise StreamError('invalid hypothesis units')
        current = tuple(units)
        self.last_request_id, self.last_audio_samples = request_id, audio_samples
        if current[:len(self.committed)] != self.committed:
            self.rejected += 1
            raise StreamError('hypothesis would rewrite committed prefix')
        stable = 0
        while stable < min(len(self.previous), len(current)) and self.previous[stable] == current[stable]:
            stable += 1
        end = len(current) if final else max(len(self.committed), stable-self.policy.holdback)
        candidate = current[:end]
        display = self.decode(candidate)
        if not isinstance(display, str) or not display.startswith(self.text):
            self.rejected += 1
            raise StreamError('tokenizer would rewrite released display bytes')
        delta = display[len(self.text):]
        self.committed, self.previous, self.text = candidate, current, display
        self.closed = bool(final)
        return {'request_id': request_id, 'audio_samples': audio_samples,
                'committed_text': self.text, 'delta': delta, 'units_committed': len(candidate),
                'action': 'EMIT' if delta else 'WAIT_HEURISTIC', 'final': bool(final)}


class PseudoStreamingBase:
    """Cumulative-prefix adapter with a bounded, injectable BASE decoder.

    decoder(pcm16k, request_id) -> {request_id, model_id, text[, token_ids]}.
    No runtime imports, process launches, downloads or product model switching.
    PCM is passed read-only; only already received samples are available.
    Calling the decoder is synchronous; a real process adapter must enforce its
    own hard deadline. No untested timeout guarantee is made for arbitrary code.
    """
    def __init__(self, decoder, *, model_id, chunk_samples=16000, max_seconds=30,
                 policy=Policy(), decode_tokens=None):
        if type(chunk_samples) is not int or chunk_samples < 1:
            raise ValueError('positive integer chunk size required')
        if not math.isfinite(max_seconds) or max_seconds <= 0:
            raise ValueError('positive finite utterance bound required')
        self.decoder, self.model_id = decoder, model_id
        self.chunk_samples, self.max_samples = chunk_samples, int(max_seconds*16000)
        if not isinstance(model_id, str) or not model_id or chunk_samples > self.max_samples:
            raise ValueError('invalid model ID or chunk budget')
        self.pcm = np.zeros(self.max_samples, dtype=np.float32)
        self.received, self.last_decoded, self.request_id = 0, 0, 0
        self.next_decode = chunk_samples
        self.committer = PrefixCommitter(policy, decode_tokens)
        self.closed = False

    def _decode(self, end, final=False):
        self.request_id += 1
        pcm = self.pcm[:end].copy(); pcm.setflags(write=False)
        start = time.perf_counter()
        reply = self.decoder(pcm, self.request_id)
        elapsed = (time.perf_counter()-start)*1000
        if (not isinstance(reply, dict) or type(reply.get('request_id')) is not int
                or reply['request_id'] != self.request_id or reply.get('model_id') != self.model_id
                or not isinstance(reply.get('text'), str)):
            raise StreamError('malformed, stale or wrong-model decoder reply')
        units = reply['text'].split() if self.committer.policy.unit_kind == 'words' else reply.get('token_ids')
        if self.committer.policy.unit_kind == 'model_tokens':
            if not isinstance(units, (list, tuple)) or self.committer.decode(units) != reply['text']:
                raise StreamError('token IDs and decoded text disagree')
        event = self.committer.observe(units, request_id=self.request_id, audio_samples=end, final=final)
        event.update(decode_ms=elapsed, hypothesis=reply['text'])
        self.last_decoded = end
        return event

    def push(self, pcm16k):
        if self.closed: raise StreamError('stream finalized')
        x = np.asarray(pcm16k)
        if x.ndim != 1 or not np.issubdtype(x.dtype, np.number) or np.iscomplexobj(x) or not np.all(np.isfinite(x)):
            raise StreamError('finite mono PCM required')
        if self.received+len(x) > self.max_samples:
            raise StreamError('explicit endpoint required: utterance memory budget exceeded')
        x = x.astype(np.float32)/32768 if x.dtype == np.int16 else x.astype(np.float32)
        if np.max(np.abs(x), initial=0) > 1:
            raise StreamError('PCM outside [-1,1]')
        self.pcm[self.received:self.received+len(x)] = x
        self.received += len(x)
        events = []
        while self.next_decode <= self.received:
            events.append(self._decode(self.next_decode))
            self.next_decode += self.chunk_samples
        return events

    def finish(self):
        if self.closed: raise StreamError('stream finalized')
        if not self.received:
            self.closed = True
            return dict(self.committer.observe([], request_id=0, audio_samples=0, final=True), decode_ms=0, hypothesis='')
        # Re-query the actual received prefix even at exact chunk boundaries:
        # do not silently lose a held-back suffix on an empty tail buffer.
        result = self._decode(self.received, final=True)
        self.closed = True
        return result
