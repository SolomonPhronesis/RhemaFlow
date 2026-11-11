# NEXT_SPEAKER_STUDY — target-speaker isolation, experiment design

## 0. The causal question

**Can competing-preacher/congregation speech be suppressed while the intended pastor's words and correct Bible
cards are preserved?** Not "can WER go down": a system that drops correct cards or silently deletes pastor speech
can lower a generic WER while making the product worse.

Five outcome classes are always reported separately:

| Class | Metric |
|---|---|
| streaming UX | time to first provisional text; stable-commit rate; revisions after commit; card delay |
| ASR recognition | S/D/I, reference words, WER (scorer v2) |
| speaker targeting | foreground (target) WER, other-speaker intrusion words, target speech lost, overlap coverage |
| Bible cards | correct / wrong / missed / review / abstain, per condition |
| resources | RTF, CPU, GPU, RAM, swap, disk, start-up |

A fall in false cards is **not** a WER improvement; a zero-wrong-card policy is **not** success if it misses correct
cards. Both statements are enforced by the tables below.

## 1. Current evidence (frozen 648-clip matrix, no model re-run this round)

| Condition | Q4 WER | cards (V3) correct/wrong/review/none |
|---|---:|---|
| clean | 1.59 % | 34 / 0 / 2 / 4 |
| music −5…+10 dB | 1.87–4.01 % | 34 / 0 / 2 / 4 each |
| chatter 0 dB | 26.59 % | 26 / 0 / 2 / 12 |
| chatter −5 dB | 79.57 % | 1 / 0 / 14 / 25 |
| overlap 0 dB | 68.19 % | 11 / 0 / 8 / 21 |
| overlap −5 dB | 93.28 % | 0 / 0 / 32 / 8 |
| triple mix 0 dB | 66.88 % | 3 / 0 / 12 / 25 |
| music-only / silence | n/a | 0 / 0 / 0 / 48 |
| chatter-only | n/a | 0 / 0 / 14 / 26 |

Heuristic attribution (machine transcripts, **not** human gold): 96.4 % of overlap errors and 90.6 % of chatter
errors at −5 dB are the other speaker's words.

## 2. Arms, in execution order

| Arm | Design | Prerequisites | Exit criteria |
|---|---|---|---|
| **B0** | existing single-mic Q4 / Qwen 1.7B / current matcher — **reported, not re-run** | saved transcripts | baseline frozen |
| **B1** | close-mic feed (lapel/headset/lectern) alone | lawfully recorded close mic | target WER lower than B0 at equal cards; no card loss |
| **B2** | two simultaneously recorded mics, clock-aligned, channels held separate; compare close-only, selection, delay+level gating | 2-channel capture; **no synthetic duplication** | target WER and intrusion improve; wrong cards do not rise |
| **B3** | foreground activity / overlap detector → review vs drop | feature extractor (energy/voice activity at minimum) | precision/recall reported; **gate rejected if it only loses correct cards** |
| **B4** | separation or enrolment (identity matching) | licensed commercial-use model + consented enrolment | identity false-match and unknown-speaker rates reported; no R2T2 weights |
| **B5** | stable-prefix layer on genuine incremental hypotheses | model streaming OR replayed chunks, labelled honestly | zero post-commit revisions; latency reported; **not counted as speaker isolation** |

## 3. Measured gate behaviour (this round, model-free)

Confidence-gate sweep on the saved 648-clip V3 output (`data/gate_sweep_648.csv`):

| threshold | correct kept | correct lost | wrong removed | recall |
|---:|---:|---:|---:|---:|
| 0.0–0.6 | 345 | 0 | 0 | 1.000 |
| 0.7 | 331 | 14 | 0 | 0.959 |
| 0.8 | 312 | 33 | 0 | 0.904 |
| 0.9 | 238 | 107 | 0 | 0.690 |

**Every threshold only destroys correct cards** because the current pipeline already has 0 wrong cards on this
corpus. Any B3 gate must be evaluated against a corpus that actually produces wrong cards (speaker confusion at
partial overlap), not this one.

## 4. Data manifest schema (frozen before any run)

```
case_id, wav_path, sha256, duration_s, target_speaker_id, other_speaker_ids, accent,
mic_model, mic_channels, sample_rate, room, distance_m, snr_db (target vs interference),
condition (clean|music|chatter|overlap|mixed|no_target), music_present, overlap_present,
gold_text_target, gold_text_other, scripture_refs, annotator_a_hash, annotator_b_hash,
adjudicated, consent_id, licence
```

Rules: two independent annotators, third-pass adjudication, speaker-disjoint splits, frozen SHA-256 manifest
before any model run, no model output used as gold.

## 5. Milestones as independent gates (same labelled matrix)

| Milestone | Meaning | Current |
|---|---|---|
| < 26.306 % | beat Q4 baseline | not yet (Qwen 24.387 % does, Q4/V3 equal) |
| < 20 % | credible improvement | no |
| < 15 % | needs separation or multi-mic | blocked |
| < 6 % | aspirational stretch | requires new acoustic capture **and** in-domain adaptation |

## 6. What cannot be done on this machine today

Two-channel capture, diarisation, separation and consented enrolment audio do not exist here; disk is 662 MiB
(below the 4 GiB floor). See `DISK_RECOVERY_CANDIDATES.md`.
