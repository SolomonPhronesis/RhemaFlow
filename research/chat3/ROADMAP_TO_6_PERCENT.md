# ROADMAP_TO_6_PERCENT — what can and cannot plausibly close the gap

**Aspirational target: < 6 % WER on the 560-clip frozen mixed-noise set.** Current measured: Qwen 24.39 %,
Q4 26.31 %, Tiny 44.79 %. This is a 4× reduction. The roadmap below is an engineering estimate, not a promise.

## 1. Where the error actually is (measured)

| Condition | WER | Share of total edits |
|---|---:|---:|
| clean | 1.59 % | tiny |
| music −5…+10 dB | 1.87–4.01 % | small |
| chatter 0 dB | 26.59 % | medium |
| chatter −5 dB | 79.57 % | large |
| overlap 0 dB | 68.19 % | large |
| overlap −5 dB | 93.28 % | large |
| triple mix 0 dB | 66.88 % | medium |

Heuristic attribution: at −5 dB, **96.4 %** of overlap errors and **90.6 %** of chatter errors are the other
speaker's words. **Streaming cannot fix this**: committing faster or more stably changes *when* text appears, not
*whose* voice is transcribed.

## 2. What each lever can plausibly buy

| Lever | Expected effect on aggregate | Evidence basis | Status |
|---|---|---|---|
| Stable-prefix streaming (heuristic) | 0 pp WER; latency/revision quality only | V3 identical to Q4 (0.000 pp) | measured |
| Pause-end 900 ms + 20 s cut | ~0 pp on the 560 set; 3 pp on pause-heavy speech | held-out pause tests | measured |
| Better LLM verifier (Qwen 1.7B) | −1.9 pp aggregate (24.39 vs 26.31), but +14 pp on triple mix | matrix | measured |
| Confidence/overlap abstention | 0 pp WER, fewer wrong cards (already 0) | negative result | measured |
| Diarisation / target enrolment | potentially large on overlap cells | literature, not measured here | `NOT_AVAILABLE` |
| Close-talk pastor mic | typically 10–20 dB higher target SNR | physical acoustics, not measured here | `NOT_AVAILABLE` |
| Speech separation / beamforming | potentially large, needs a licensed model | literature, not measured here | `NOT_RUN` |
| Fine-tuning on consented church gold | unknown; could help clean/noisy both | no gold | `BLOCKED_GOLD` |
| R2T2 weights | prohibited | licence §3.4(c) | **NO** |

**Arithmetic:** even if overlap and chatter cells at ≤0 dB were halved (a very optimistic separation result), the
aggregate would fall from ~26 % to roughly 14–16 %. Reaching <6 % requires **both** separation/multi-mic **and** a
model trained or adapted on in-domain data — not streaming.

## 3. Honest checkpoints

| Milestone | Condition | Status |
|---|---|---|
| ≤ 26.3 % (baseline parity) | 560-clip aggregate | **reached** (Q4/V3) |
| ≤ 20 % | aggregate | **Qwen 24.39 % now; not reached** |
| ≤ 15 % | aggregate | requires separation or multi-mic — `NOT_AVAILABLE` |
| ≤ 10 % | aggregate | requires both separation and domain adaptation |
| **< 6 %** | aggregate | **not plausible without new acoustic capture + licensed training data**; do not promise |

## 4. Recommended next actions (in order)

1. Consented, speaker-labelled church gold (still `BLOCKED_GOLD`).
2. Two-channel recording (pastor close mic + room mic) on 10+ sessions — the highest-leverage physical change.
3. A licensed separation/diarisation model evaluated as a **target-speaker** filter, scored on target WER and card
   recall, not generic WER.
4. Only then: decoder adaptation on owned gold; no R2T2 weights or outputs.
