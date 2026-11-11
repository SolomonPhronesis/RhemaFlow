# FILTER_ADVANCE — delay tracking attempted; what improved and what did not

## 1. What was implemented

`fir_tracking()` in `scripts/fir_isolation.py`: a causal block-NLMS FIR whose inter-channel delay is re-estimated at
each 2 s chunk boundary **from the previous chunk only** and applied to the next chunk. All filter updates use past
samples; the chunk delay is never taken from the current or future audio.

A delay-sign bug was found while testing (the aligned window index used `i − lag` instead of `i + lag`), fixed, and
covered by the existing causality test.

## 2. Tune-split result (signal level, 6 clips × 2 TIR × chatter)

| taps | μ | mean ΔSIR | mean target retention |
|---:|---:|---:|---:|
| 32 | 0.3 | **+0.48 dB** | −0.11 dB |
| 64 | 0.3 | +0.21 dB | −0.08 dB |
| 128 | 0.3 | +0.10 dB | −0.05 dB |

Compare with the **fixed-delay** FIR on the full tune grid: 32 taps **+3.39 dB** (selected), 64 taps 2.82 dB,
128 taps 2.27 dB. The scalar canceller on the holdout achieved **+6.32 dB**.

**Delay tracking made the FIR worse, not better.** Per-chunk re-estimation introduces alignment jumps that break the
filter's learned state; a 2 s window with reverb gives noisy lag estimates. This is reported as a negative result,
not hidden.

## 3. Partitioned frequency-domain filter — `NOT_IMPLEMENTED`

A PBFDAF (4–16 partitions, FFT 256–512) is the standard next step for long room responses, but it was not
implemented in this round: the remaining time was spent on the wrong-card forensics and the operator kit, and an
unverified FFT filter would add risk without a holdout-tested result. It is the top item in the next-stage backlog.
