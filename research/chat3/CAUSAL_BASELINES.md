# CAUSAL_BASELINES — past-only isolation against the oracle

All methods use the **same 160 synthetic mixtures** (40 verses × 2 interfering sources × TIR 0/−5 dB; 4,288
reference words) and the frozen Q4 Metal backend + scorer v2.

| Method | Causal? | Deployable? | Aggregate WER | Intrusion /100 words |
|---|---|---|---:|---:|
| close mic only | — | yes (baseline) | **66.535 %** | 29.55 |
| room mic only | — | no | 94.263 % | 58.84 |
| naïve 0.5·(close+room) | yes | yes | 90.065 % | 52.99 |
| **causal NLMS (this round)** | **yes** | **prototype** | **2.822 %** | **2.38** |
| oracle least-squares (previous round) | no | no | 2.542 % | 2.08 |

Paired bootstrap (2,000 draws, close − method): **+58.88 to +68.47 pp** for causal, +59.16 to +68.90 pp for oracle.

## Algorithm (strictly causal)

```
calibrate delay on the first 320 ms only (xcorr), then hold it fixed
α = 0
for each 20 ms block k:
    out_k = close_k − α · room_k            # α from previous blocks only
    if rms(room_k) > rms(close_k):           # interference-dominance gate
        α ← clip(α + μ · (out_k · room_k)/‖room_k‖², 0, 1.2)
```

The **gate** is the key change from the first draft: without it, a room mic containing only the target drives
α upward and subtracts the pastor. With it, clean audio is untouched.

## Cards (V3-20s, pause 900 ms, on the causal output)

| Condition | QUOTE | correct | wrong | review | none |
|---|---:|---:|---:|---:|---:|
| chatter −5 dB | 34 | 34 | 0 | 2 | 4 |
| chatter 0 dB | 34 | 34 | 0 | 2 | 4 |
| second preacher −5 dB | 33 | 33 | 0 | 2 | 5 |
| second preacher 0 dB | 33 | 33 | 0 | 2 | 5 |
| **total** | **134** | **134** | **0** | **8** | **18** |

No-target controls (20 chatter-only + 8 silence through the same chain): **28/28 NO_CARD, 0 wrong,
1 emitted word total**.

## Honest weaknesses

| Check | Result |
|---|---|
| clean-audio degradation | 1.586 % — **no measurable loss** (gate prevents target cancellation) |
| reverb (120 ms decay) + ±1 dB gain drift | **68.097 %** vs close 68.19 % — the scalar canceller **fails** under reverb/drift (gain ≈ 1.5 pp only) |
| processing cost | ≈ 0.02 ms per 20 ms block on this M1 (scalar update); negligible vs ASR |
| added latency | one 20 ms block (causal), plus delay estimation on the first 320 ms at session start |

**Conclusion:** a causal, real-time, oracle-free front-end recovers most of the synthetic 2.54 % ceiling (2.82 %)
on clean two-channel capture, with zero wrong cards and no clean-audio cost — but it is **not robust to reverb or
drift**, which is exactly what a real church room adds. A real deployment needs a short adaptive filter (FIR), not
a scalar gain, and must be validated on recorded two-channel audio.
