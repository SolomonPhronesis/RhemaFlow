# SPEAKER_ISOLATION_STUDY — synthetic two-channel evaluation

**Evidence class: `SYNTHETIC_SIMULATION`.** Known components, simulated microphone channels. Not a recorded
two-microphone result, not live-church data, not an ASR accuracy claim.

## 1. Why this exists

Every measured result so far says the residual error is **competing-speaker energy** (96.4 % of overlap errors,
90.6 % of chatter errors at −5 dB are the other speaker), and streaming cannot change whose voice is transcribed.
The highest-leverage physical intervention is a **close pastor microphone**, optionally with a second room
microphone. Real two-channel audio does not exist on this machine, and disk is 3.9 GiB (below the 4 GiB floor),
so this round quantifies *what such capture would have to deliver* using a controlled simulation.

## 2. Simulation model (explicit, reproducible)

For each of 8 clean KJV clips (`scripts/two_channel_sim.py`):

```
target t  = KJV speech, normalised to 0.08 RMS
interf i  = owner-approved chatter or second-preacher recording, 0.08 RMS
close mic = t + g_c · i            g_c = 10^(−TIR/20)     (TIR = 0 or −5 dB)
room mic  = 0.5 · t(τ) + 2.0 · i(τ)  τ = 48 samples (3 ms) delay, i.e. target −6 dB in the room mic
```

Methods compared on identical signals:

| Method | Description |
|---|---|
| A. close-only | baseline: the close mic alone |
| B. two-channel cancellation | estimate the inter-channel delay by cross-correlation, align the room mic, subtract `α·room` where `α` is the least-squares coefficient for that clip |

Metrics use the **known components** (oracle for measurement, not for the algorithm): output SIR, target retention
(projection of output onto the known target), frames where the target component drops more than 6 dB, and an
energy-ratio **overlap detector** scored against known interference-vs-target frame labels (AUC).

## 3. Measured results (8 clips per cell)

| Source | TIR | ΔSIR | residual vs close | target retention | frames with >6 dB target loss | overlap AUC |
|---|---:|---:|---:|---:|---:|---:|
| chatter | 0 dB | **+11.93 dB** | −7.13 dB | −3.07 dB | 7.24 % | 0.990 |
| chatter | −5 dB | **+21.88 dB** | −9.42 dB | −2.72 dB | 7.41 % | 0.999 |
| second preacher | 0 dB | **+12.30 dB** | −7.08 dB | −2.93 dB | 5.35 % | 0.956 |
| second preacher | −5 dB | **+22.57 dB** | −9.37 dB | −2.53 dB | 6.33 % | 0.991 |

**Reading:**

* A simple delay-and-level cancellation removes 12–23 dB of interference in this model — far more than any
  streaming or verifier change measured so far.
* It is **not free**: the target is attenuated by ~2.5–3 dB because the room mic contains 0.5× the target, and
  5–7 % of frames lose more than 6 dB of target. That is exactly the "don't erase quiet pastor speech" risk.
* A trivial overlap detector (room/close energy ratio) reaches AUC 0.96–0.999 on this model, which makes a
  review-vs-drop gate feasible **if** real channels behave similarly.

## 4. What this does NOT show

| Claim | Status |
|---|---|
| Real two-microphone capture improves WER | **NOT_TESTED** — no two-channel recordings exist |
| ASR accuracy improves after cancellation | **NOT_RUN** — model runs blocked by disk; audio-level SIR ≠ WER |
| Bible-card recall is preserved | **NOT_RUN** — requires ASR + matcher |
| Delays/leakage match a real room | **NO** — 3 ms delay, fixed −6 dB target leakage, no reverb, no clock drift |
| Adaptive filtering works causally | **NO** — the coefficient is least-squares over the whole clip, i.e. non-causal |

## 5. What a real experiment needs (prerequisites)

1. Simultaneously recorded close (lapel/headset) and room microphones, same clock, 10+ sessions.
2. Consented, speaker-labelled gold; speaker-disjoint splits; two annotators + adjudication.
3. Clock-drift correction and measured inter-channel delay per session.
4. Then: close-only vs selection vs cancellation vs no processing, scored with ASR on the same utterances,
   reporting target WER, intrusion, target loss, cards and end-to-end latency.
5. Disk ≥ 8 GiB (preferably 15–20) before any of this runs.

## 6. Exit criteria for the next stage

* Cancellation arm must beat close-only by ≥ 2 pp target WER **without** losing correct cards and without
  increasing frames of target loss above the close-only baseline.
* If it cannot, keep close-only (a better microphone is still a legitimate intervention).
* Any gate that only removes correct cards is rejected, as already measured.


## 7. End-to-end through the real ASR (post-restart, disk available)

After the restart the disk gate opened (18 GiB), so the synthetic channels were finally scored end-to-end with the
real Parakeet Q4 Metal backend. 160 mixtures (40 verses × 2 interfering sources × TIR 0/−5 dB), 4,288 reference words.

| Condition | close-mic WER | isolated WER | Δ | close intrusion /100 words | isolated intrusion /100 |
|---|---:|---:|---:|---:|---:|
| chatter −5 dB | 78.36 % | **2.15 %** | −76.2 pp | 36.75 | 1.77 |
| chatter 0 dB | 26.59 % | **2.61 %** | −24.0 pp | 11.10 | 2.24 |
| second preacher −5 dB | 93.00 % | **2.43 %** | −90.6 pp | 54.57 | 1.96 |
| second preacher 0 dB | 68.19 % | **2.99 %** | −65.2 pp | 15.76 | 2.33 |
| **aggregate (160 clips)** | **66.54 %** | **2.54 %** | **−64.0 pp** | — | — |

Card stage on the isolated channel (V3-20s, pause 900 ms): **136 QUOTE, all 136 correct, 0 wrong**, 8 review,
16 none — identical to the clean-audio baseline (34 correct / 2 review / 4 none per condition).

**This is the strongest measured signal in the whole programme, and it is still synthetic.** The cancellation is
non-causal (least-squares coefficient over the whole clip), the close mic contains no reverb or room noise, and the
interferer is a known recording. The honest conclusion is directional: *if* a real second channel is captured, the
remaining WER ceiling is dominated by capture, not by the decoder. A real 2-mic trial is the correct next step.

### Correction to the earlier "6 % is not plausible" line

On this synthetic two-channel set, **2.54 % is reached** — below the aspirational 6 %. That does **not** mean 6 %
has been reached on church audio; it means the 6 % barrier is a capture problem, not a model-size problem. The
milestones table in `ROADMAP_TO_6_PERCENT.md` refers to the single-channel mixed-noise matrix and is unchanged.
