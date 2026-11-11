# ADAPTIVE_FIR_RESULTS — causal FIR under realistic acoustics (frozen splits)

**Evidence class:** `SYNTHETIC_2CH_SIMULATION` with frozen train/tune/holdout partitions. Not church audio.

## 1. Why this round exists

The previous 2.822 % causal result was measured on an **idealised** pair: no reverb, fixed delay, fixed leak, no
motion. Under 120 ms reverb + drift it collapsed to 68.1 %. This round rebuilds the corpus with realistic acoustics
and asks whether a causal **adaptive FIR** (not a scalar gain) recovers the gain.

## 2. Frozen partitions (written before tuning)

| Split | Case ids | Use |
|---|---|---|
| train | `0001–0020` | sanity only; no parameter fitted on it |
| tune | `0021–0030` | parameter selection only |
| **holdout** | `0031–0040` | **scored once, after selection** |

`data/split_manifest.csv` is the frozen record. The holdout was not touched during tuning.

## 3. Realistic synthesis per clip (randomised, frozen by seed)

* delay 40–60 samples with **speaker motion** ramping up to +12 samples across the utterance;
* room target leak **5–7 dB below** the close mic (not a pure interferer);
* reverberation **120–200 ms** (direct path + diffuse tail, unit energy; a smooth exponential kernel was rejected
  because it is a ~5 Hz low-pass and destroys speech);
* slow level drift ±1.5 dB at 0.2–0.5 Hz;
* TIR 0 / −5 dB, two interfering sources.

## 4. Methods (all past-only)

| Method | Description |
|---|---|
| close | close mic alone |
| room | room mic alone |
| mix | 0.5·(close + room) |
| scalar | gated NLMS, 1 tap (previous round) |
| **fir** | block NLMS FIR, 32/64/128 taps, 10 ms blocks, gate: adapt only when room RMS > close RMS |
| fir_dt | same + double-talk freeze when close energy > 1.8× its running median |

Delay is estimated from the **first 400 ms only** and then held; no target, interference, leak or true delay is ever
passed to the algorithm (enforced by a unit test).

## 5. Tuning (tune split only, signal-level objective)

| taps | mu | mean ΔSIR (dB) |
|---:|---:|---:|
| **32** | **0.3** | **3.39** |
| 64 | 0.3 | 2.82 |
| 128 | 0.3 | 2.27 |
| 32 | 0.1 | 2.07 |
| 64 | 0.1 | 1.62 |
| 128 | 0.1 | 1.18 |

Short filters win: with motion and drift, longer filters adapt too slowly. The selected FIR is **32 taps, μ = 0.3**.

## 6. Holdout results (40 clips, 1,128 reference words)

| Method | WER | Δ vs close (pp) | 95 % CI (paired bootstrap) | intrusion /100 |
|---|---:|---:|---|---:|
| close | 67.199 % | — | — | 26.42 |
| room | 92.287 % | −25.1 | −34.5 … −16.6 | 52.30 |
| mix | 84.043 % | −16.8 | −23.5 … −11.0 | 43.53 |
| **scalar** | **41.223 %** | **+26.0** | **+17.4 … +35.1** | **14.89** |
| fir (32 taps) | 51.862 % | +15.3 | +7.6 … +23.0 | 16.84 |
| fir + double-talk | 54.610 % | +12.6 | +5.2 … +20.6 | 19.59 |

Signal level on the holdout: scalar ΔSIR **+6.32 dB** (p10 3.24, p90 10.28), FIR **+3.40 dB** (p10 1.48, p90 6.29);
target retention −1.12 dB / −0.99 dB.

**The scalar canceller beats the adaptive FIR** in this room. That is the opposite of the intuitive hypothesis and
it is reported as measured: under time-varying delay and heavy reverb, a 32-tap filter cannot track the room, while
the scalar at least removes the direct-path interference.

## 7. Cards and safety

| Set | QUOTE | correct | wrong | review | none | words |
|---|---:|---:|---:|---:|---:|---:|
| FIR holdout | 19 | **19** | **0** | 8 | 13 | 779 |
| FIR no-target controls | 1 | 0 | **1** | 1 | 26 | **418** |

**Negative safety result:** on 20 chatter-only + 8 silence clips through the FIR, the pipeline emitted 418 words and
**one wrong card**. Under realistic reverberation the canceller does not remove the competing speaker, and the card
stage then quotes that speaker. This is exactly the failure mode the project must avoid; a safety gate must not be
shipped on this evidence.

## 8. Throughput (M1 Pro, single core, 60 s audio)

| taps | wall ms | real-time factor |
|---:|---:|---:|
| 16 | 99.6 | 0.0017 |
| 32 | 133.9 | 0.0022 |
| 64 | 205.6 | 0.0034 |
| 128 | 351.5 | 0.0059 |

The DSP front-end is 170–590× faster than real time; ASR remains the latency bottleneck (Q4 ≈ 120 ms per 8 s clip).

## 9. Conclusion

* Under realistic reverb + motion + drift, causal isolation reduces WER from **67.2 % to 41.2 %** (scalar) or
  **51.9 %** (FIR) — real but far from **<20 %**, let alone <6 %.
* The idealised 2.8 % does **not** survive realistic acoustics; the oracle ceiling remains 2.5 %.
* A short FIR is **worse** than a scalar gain here; room-tracking requires a longer filter with faster adaptation,
  which this tuning shows overfits motion.
* No-target safety fails on this evidence (1 wrong card, 418 words).
* Next: real two-mic recordings (protocol in `REAL_GOLD_PROTOCOL.md`, updated checklist below), then a filter that
  tracks delay (e.g., per-block re-estimation) evaluated on those recordings only.
