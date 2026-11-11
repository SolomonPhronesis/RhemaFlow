#!/usr/bin/env python3
"""Independent stable-prefix / provisional-suffix commit engine (research prototype).

This is a *heuristic* longest-common-prefix committer, inspired by the general
published idea of committing a stable prefix and withholding a provisional
suffix. It is NOT R2T2, not LSP-trained, and performs no model inference.

Design rules
------------
* committed text can never change once emitted;
* a new hypothesis may only extend the committed prefix, never rewrite it;
* a divergent hypothesis (speaker change, truncation, ASR restart) is rejected;
* the last U tokens stay provisional until a later hypothesis confirms them;
* the first `lookahead_updates` updates commit nothing (initial lookahead).
"""
from __future__ import annotations

import json
import re

TOKEN_SPLIT = re.compile(r"\s+")


def tokens(text):
    """Unicode-aware display tokens; consecutive whitespace collapses."""
    return [t for t in TOKEN_SPLIT.split(text.strip()) if t]


def normalise(token):
    t = token.lower().replace("\u2019", "'")
    return re.sub(r"^[^\w']+|[^\w']+$", "", t)


class Divergence(Exception):
    """The hypothesis no longer agrees with the committed prefix."""


class ProtocolError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


class StablePrefix:
    def __init__(self, holdback=1, lookahead_updates=1):
        if holdback < 0:
            raise ValueError("holdback must be >= 0")
        self.holdback = holdback
        self.lookahead_updates = lookahead_updates
        self.committed = []
        self.provisional = []
        self.updates = 0
        self.rejected_updates = 0

    def _agree(self, hyp):
        """Committed tokens must be a prefix of the hypothesis (by normalised form)."""
        if len(hyp) < len(self.committed):
            return False
        return all(normalise(hyp[i]) == normalise(self.committed[i]) for i in range(len(self.committed)))

    def update(self, text):
        """Feed a new full hypothesis; return the tokens newly committed."""
        self.updates += 1
        hyp = tokens(text)
        if hyp and not self._agree(hyp):
            self.rejected_updates += 1
            raise Divergence(f"hypothesis diverges from committed prefix at update {self.updates}")
        if not hyp:
            # silence: never clear what is already committed
            return []
        if self.updates <= self.lookahead_updates:
            self.provisional = hyp
            return []
        # longest common prefix between the previous hypothesis and this one;
        # on the very first update the whole hypothesis is provisional-stable
        if not self.provisional and not self.committed:
            self.provisional = hyp
            commit_upto = max(0, len(hyp) - self.holdback)
            new = hyp[:commit_upto]
            self.committed = list(new)
            return new
        stable = 0
        while (stable < len(self.provisional) and stable < len(hyp)
               and normalise(hyp[stable]) == normalise(self.provisional[stable])):
            stable += 1
        commit_upto = max(len(self.committed), stable - self.holdback)
        commit_upto = min(commit_upto, len(hyp))
        new = [hyp[j] for j in range(len(self.committed), commit_upto)]
        self.committed = hyp[:commit_upto]
        self.provisional = hyp
        return new

    def text(self):
        return " ".join(self.committed)

    def final(self, text):
        """Flush at end of utterance: everything left is committed once."""
        hyp = tokens(text)
        if not self._agree(hyp):
            raise Divergence("final hypothesis diverges from committed prefix")
        new = hyp[len(self.committed):]
        self.committed = list(hyp)
        self.provisional = []
        return new


def parse_reply(line, expected_id):
    """Validate one sidecar reply line; raises ProtocolError with a typed code."""
    if not isinstance(line, str) or not line.strip():
        raise ProtocolError("empty_line")
    try:
        obj = json.loads(line)
    except json.JSONDecodeError as e:
        raise ProtocolError("malformed_json", str(e))
    if not isinstance(obj, dict):
        raise ProtocolError("not_an_object")
    if obj.get("id") != expected_id:
        raise ProtocolError("stale_id", f"got {obj.get('id')!r} expected {expected_id!r}")
    if obj.get("ok") is not True:
        raise ProtocolError("not_ok", str(obj.get("error", "")))
    text = obj.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ProtocolError("empty_text")
    return {"id": obj["id"], "text": text}


class CardGate:
    """Suppress duplicate Scripture cards for the same verse within a session."""

    def __init__(self):
        self._seen = set()
        self._pending = set()

    def consider(self, verse_ref, pending=False):
        if not verse_ref:
            return False
        key = verse_ref.strip().lower()
        if key in self._seen:
            return False
        if pending:
            if key in self._pending:
                return False
            self._pending.add(key)
            return True
        self._pending.discard(key)
        self._seen.add(key)
        return True
