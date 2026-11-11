# FORENSIC_WRONG_CARD — the one wrong card and the 418 no-target words

## 1. The event

| Field | Value |
|---|---|
| Clip | `CTRL03`, condition `chatter_only` (no target speaker) |
| Card | `QUOTE` → **Luke 1:17**, confidence **0.833** |
| ASR text | *"the children and the disobedient to the what the wisdom of the just that's what i'm trying to describe to you"* |
| Front-end | 32-tap gated FIR on the synthetic two-channel pair |
| Corpus | 20 chatter-only + 8 silence clips through the FIR; **418 words** emitted in total |

## 2. Stage-by-stage failure

1. **Source**: the chatter recording is another preacher quoting Luke 1:17 ("…turn the heart of the fathers to the
   children, and the disobedient to the wisdom of the just"). The ASR heard and transcribed that speaker.
2. **Cancellation**: the causal FIR did **not** remove the competing speaker (holdout ΔSIR only +3.4 dB; on this
   control the room channel is 2× the close channel and the gate adapts, but reverb/motion defeat a 32-tap filter).
3. **Matcher**: given the transcript, Luke 1:17 is the **correct** verse — the matcher is not at fault.
4. **Attribution**: nothing in the pipeline knows *whose* voice produced the words. That is the failure.

**The wrong card is a speaker-attribution failure, not a matcher or tokenisation failure.** Suppressing all cards
would hide it; that is explicitly not what this project wants.

## 3. Candidate guard — measured and rejected

A deployable guard must be a signal available at inference time. The cheapest is the **close/room energy ratio**
(target near the close mic ⇒ close louder):

| Set | n | close/room ratio (dB) | outcome |
|---|---:|---|---|
| holdout target clips | 40 | −5.83 … −2.03 | 19 correct cards |
| no-target controls | 20 | −6.01 … −6.02 | 1 wrong card |

The ranges **overlap**: a threshold at −5.9 dB would block CTRL03 but also block the holdout clips below −5.9 dB.
Tuning the threshold on the controls would be tuning on the evaluation set (leakage). **No such guard is added.**

Coherence between the FIR output and the room channel did not separate either (holdout mean ρ = −0.055, p10 −0.153,
p90 0.039).

## 4. What actually fixes it

1. Better cancellation (longer/partitioned filter or delay tracking) so the competing speaker is attenuated before
   ASR — measured as the ΔSIR lever, not a card patch.
2. A speaker-attribution model (diarisation/embedding) — `NOT_AVAILABLE` on this machine.
3. Real dual-mic data to calibrate any threshold on **tune**, never on holdout or controls.

Until one of those exists, the honest position is: **the card stage cannot be made zero-wrong on no-target audio
under heavy interference by a post-hoc rule**, and the pipeline must not be shipped in this configuration.
