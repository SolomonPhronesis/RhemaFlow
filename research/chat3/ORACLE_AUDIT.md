# ORACLE_AUDIT — what the 2.54 % two-channel result actually used

## 1. The algorithm (as measured)

`scripts/two_channel_sim.py` / `build_twoch.py` computed, per clip:

1. `close = target + g·interference` and `room = 0.5·target(τ) + 2·interference(τ)` with **known** target and
   interference, a **fixed** 3 ms delay, and a **fixed** −6 dB target leak.
2. `est_delay(close, room)` — cross-correlation over the **entire clip**.
3. `α = (close·room)/(room·room)` — least squares over the **entire clip**.
4. `out = close − α·room`.

## 2. Why this is an oracle ceiling, not a deployable method

| Leak | Detail |
|---|---|
| future samples | both the delay estimate and α use samples after each output sample — the output at 1 s depends on audio at 8 s |
| whole-clip stationarity | one α for the whole utterance; no adaptation to changing levels |
| known generative model | the room channel is constructed by us; there is no reverb, no mic self-noise, no drift, no non-linear PA |
| clean interferer | the interferer is one recording with no overlap with the target's own speech content |
| synthetic close mic | "close" still contains the interference at 0/−5 dB; a real lapel mic would not |

**Verdict:** 2.54 % is the **best case** for this synthetic pair. It says a second channel contains enough
information to remove the competing speaker almost completely under ideal conditions. It does **not** say a
real-time system can reach 2.54 %.

## 3. Reproduction

The 160-clip oracle result is reproducible from the saved raw transcripts:
`raw/b0_iso.jsonl` scored with `wer.py` v2 → 109 edits / 4,288 words = **2.542 %** aggregate
(individual conditions 2.15–2.99 %). No model re-run is needed; the transcripts and the scorer are frozen.

## 4. Contamination / leakage checks

* The target gold was used **only** for scoring, never inside the algorithm.
* The interference transcript was used only for attribution analysis, never inside the algorithm.
* The cancellation used the mixture channels, not the clean components; however it used **future** mixture
  samples (non-causal) — this is the leakage that matters and is why it cannot be shipped.
