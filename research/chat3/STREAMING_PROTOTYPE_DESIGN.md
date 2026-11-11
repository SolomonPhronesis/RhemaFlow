# STREAMING_PROTOTYPE_DESIGN — independent stable-prefix engine

## 1. What was implemented (and what was not)

**Implemented and tested:** `research/chat3/scripts/stable_prefix.py` — a pure-Python, model-free commit engine
plus sidecar-reply validator and card de-duplicator. **20/20 tests pass** (`tests/test_streaming.py`).

**Not implemented (blocked):** no model inference, no audio, no 160/320/640/1000 ms feeding. Disk is 672 MiB
(hard floor 4 GiB), and the brief forbids model runs/648-clip reruns under the floor. The engine is the part that
can be verified safely now; the acoustic arms remain `NOT_RUN`.

## 2. Algorithm (heuristic LCP — not LSP-trained)

```
state: committed=[], provisional=[], updates=0, U=holdback (default 1)

update(hypothesis H):
    updates += 1
    if H empty: return []                       # silence never clears committed
    if committed is not a prefix of H (normalised):
        raise Divergence                        # speaker change / truncation / restart
    if updates <= lookahead_updates: provisional = H; return []
    stable = LCP(provisional, H)
    commit_upto = clamp(max(len(committed), stable - U), 0, len(H))
    new = H[len(committed):commit_upto]
    committed = H[:commit_upto]
    provisional = H
    return new

final(H):                                       # end of utterance, single flush
    require committed is a prefix of H
    return H[len(committed):] and commit all
```

Guarantees: committed text is append-only; a divergent hypothesis can never rewrite it; the last U tokens are
provisional; the first `lookahead_updates` updates emit nothing.

## 3. Test matrix (all pass)

| Area | Test |
|---|---|
| repeated words | `the the lord is` preserved exactly once each |
| stable prefix | committed string is a prefix of every later committed string |
| Unicode / punctuation | `God’s` ≡ `God's`; punctuation tokens preserved |
| partial words | `everlast` → `everlasting` replaced, not duplicated |
| filler | `um` preserved verbatim (no silent cleaning) |
| silence | empty hypotheses commit nothing and never clear text |
| abrupt cutoff | shorter hypothesis raises `Divergence`, committed unchanged |
| speaker handoff | divergent speaker text rejected, committed unchanged |
| long audio | 100+ updates, monotonic growth, final text exact |
| U = 0/1/2 | holdback changes commit length as specified |
| lookahead | first N updates commit nothing |
| sidecar | valid, malformed JSON, stale id, `ok:false`, empty text → typed `ProtocolError` |
| cards | duplicate and pending-duplicate verse suppressed |
| leakage | prototype contains no audio/file/network IO |

## 4. What a full experimental run would need (not done)

| Arm | Requirements | Est. temp space |
|---|---|---|
| A. Qwen full-context | MLX 1.7B (present, 1.4 GB), 560 target clips | ~1 GB |
| B. Qwen pseudo-streaming | re-decode every 160–1000 ms → 6–40× decodes | 2–4 GB + hours |
| C. Q4 buffered windows | 5/10/20 s windows + word alignment | 2–3 GB |
| D. speaker ablation | 2-channel consented audio or a separator model | n/a — data missing |
