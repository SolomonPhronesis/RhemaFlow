# ACCURACY_ROADMAP — from 26.3 % toward <6 %

## Measured today (frozen 560-clip single-channel matrix)

| Arm | WER |
|---|---:|
| Q4 | 26.306 % |
| Qwen 1.7B MLX | 24.387 % |
| V3 / V4 (same decode) | 26.306 % |

Single-channel streaming/verifier changes have **not** moved this. Stable-prefix commitment changes *when* text
appears, not *whose* voice is transcribed.

## Measured today (synthetic two-channel, same utterances)

| Front-end | WER | Evidence class |
|---|---:|---|
| close mic only | 66.535 % | SYNTHETIC_2CH |
| causal NLMS, gated | **2.822 %** | CAUSAL_SIMULATION |
| oracle least squares | 2.542 % | ORACLE_SIMULATION |
| causal NLMS under reverb+drift | 68.097 % | CAUSAL_SIMULATION |

## Milestones on the single-channel matrix

`<26.306 %` not yet beaten by a legal model change; `<20 %`, `<15 %`, `<6 %` **not reached** on any real
single-mic condition. `<6 %` is reached **only** on synthetic two-channel isolation, which is not a church result.

## What transfers to a real church

1. **Capture** dominates: a lapel mic raises target-to-interference by 10–20 dB before any algorithm.
2. **Causal adaptive filtering** (FIR, 32–128 taps) with an interference-dominance gate is required; a scalar gain
   fails under reverb/drift (measured).
3. **Diarisation/separation models** are still `NOT_AVAILABLE` here; they would help the room-mic path, not the
   lapel path.
4. **Domain adaptation** on owned, consented gold is the only remaining acoustic lever; no R2T2 weights.

## Recommended next stage

Record 3 pilot services with dual capture → run the causal front-end → score with the frozen scorer. Success
criterion: ≥ 5 pp target-WER improvement over close-only with no card loss and no clean degradation. If not,
ship close-mic only (better microphone, no DSP risk) and revisit.
