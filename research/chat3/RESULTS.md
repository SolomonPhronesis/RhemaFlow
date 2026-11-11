# RESULTS — causal adaptive FIR under realistic acoustics

**Date:** 2026-11-11 22:13–23:25 UTC · **Disk:** 8.8 GiB at start · **Branch:** `adaptive-fir-isolation-20261111`
**Verdict: `RESEARCH_GO` / `BLOCKED_GOLD` for church accuracy / `PRODUCTION_NO_GO`.**

## 1. What ran

Frozen-split synthetic two-channel corpus (train 01–20, tune 21–30, **holdout 31–40**), rebuilt with realistic
acoustics: reverb 120–200 ms, speaker motion (delay ramp), 5–7 dB room target leak, ±1.5 dB drift, TIR 0/−5 dB.
Six front-ends (close, room, mix, scalar NLMS, 32/64/128-tap FIR grid, FIR + double-talk) plus Q4 Metal ASR and the
V3 card stage on the holdout.

## 2. Holdout results (40 clips, 1,128 words)

| Method | WER | Δ vs close | 95 % CI | intrusion /100 |
|---|---:|---:|---|---:|
| close | 67.199 % | — | — | 26.42 |
| room | 92.287 % | −25.1 | −34.5…−16.6 | 52.30 |
| mix | 84.043 % | −16.8 | −23.5…−11.0 | 43.53 |
| **scalar** | **41.223 %** | **+26.0** | **+17.4…+35.1** | 14.89 |
| FIR 32 taps | 51.862 % | +15.3 | +7.6…+23.0 | 16.84 |
| FIR + double-talk | 54.610 % | +12.6 | +5.2…+20.6 | 19.59 |

Tuning on the tune split selected 32 taps, μ 0.3 (ΔSIR 3.39 dB). Signal level on holdout: scalar +6.32 dB ΔSIR,
FIR +3.40 dB; retention ≈ −1 dB.

## 3. Negative results that matter

* **The scalar canceller beats the FIR** under motion + heavy reverb (41.2 % vs 51.9 %). Longer filters adapt too
  slowly; the tune grid already showed 128 taps at 2.27 dB vs 32 taps at 3.39 dB.
* **No-target safety fails**: 20 chatter-only + 8 silence clips through the FIR emitted **418 words** and
  **1 wrong card**. The card stage will quote the competing speaker when cancellation is incomplete.
* **Cards on holdout**: 19 QUOTE, 19 correct, 0 wrong — but only 19 of 40 clips produced a card (vs 34/40 on clean).

## 4. Comparison with the idealised result

| Setting | close | best causal | oracle |
|---|---:|---:|---:|
| idealised pair (previous round, 160 clips) | 66.535 % | **2.822 %** | 2.542 % |
| realistic reverb/motion/drift (holdout, 40 clips) | 67.199 % | **41.223 %** | not recomputed |

The idealised number does **not** survive realistic acoustics. Reverb is the dominant obstacle, not ASR quality.

## 5. Throughput

FIR processing is 0.0017–0.0059 RTF (170–590× real time) on one M1 core; ASR remains the bottleneck.

## 6. Milestones on the same defined test

`<20 %`, `<15 %`, `<10 %`, `<6 %`: **none reached** on realistic two-channel isolation (best 41.2 %).
`<6 %` remains reached only on the oracle/idealised pair, which is not deployable and not church audio.

## 7. Status table

| Requirement | Status | Evidence |
|---|---|---|
| Lineage verification + new branch | **DONE** | base `ddb36f1`, branch `adaptive-fir-isolation-20261111` |
| Reproduce clean/noisy/reverb/drift baselines | **DONE** | close/room/mix/scalar/FIR on frozen holdout |
| Causal adaptive FIR alternatives | **DONE** | 32/64/128-tap grid, double-talk variant, unit tests |
| Past-only proof | **DONE** | `test_future_samples_do_not_change_past_output` |
| Bounded memory/latency + throughput | **DONE** | 10 ms blocks, 32 taps, RTF ≤ 0.006 |
| Frozen train/tune/holdout, no oracle tuning | **DONE** | `data/split_manifest.csv`, tune grid on tune only |
| Reverb ≥120 ms, drift, motion, leakage | **DONE** | synthesis params documented |
| Q4 on processed audio + CIs | **DONE** | holdout table with paired bootstrap |
| Qwen arm on processed audio | **NOT_RUN** | time/priority; disk was sufficient but the Q4 result already answered the question |
| Cards / no-target hallucinations | **DONE (negative)** | 19/19 correct on holdout; 1 wrong card on controls |
| Real two-mic corpus | **BLOCKED** | `REAL_GOLD_NOT_AVAILABLE`; protocol in `SPLIT_AND_PROTOCOL.md` |
| Production | **NO-GO** | research only |

## 8. Reproduction

```bash
python3 research/chat3/scripts/fir_isolation.py   # builds frozen-split corpus + tune grid
python3 research/chat3/scripts/score_fir.py       # holdout WER, CIs, cards
python3 research/chat3/tests/test_fir_isolation.py -v   # 5/5
```
