# OPERATOR_KIT — consented dual-mic church capture (≥3 services)

## 1. Hardware and capture

| Item | Requirement |
|---|---|
| Mic A | preacher lavalier or headset, clipped 15–20 cm below the chin |
| Mic B | room/ambient mic on a stand, 3–6 m from the pulpit, aimed at the congregation |
| Interface | **both mics into the same recorder/interface**, same clock; raw channels kept separate (no mixdown) |
| Rate | 48 kHz, 24-bit WAV, no processing, no AGC, no noise suppression |
| Sync | clap/slate at the start of each service (and at the end if long) |
| Gains | set once, recorded in the log; avoid clipping on the pastor channel |
| Log | device, firmware, sample rate, distance, room, PA, music, second speaker, service length |

## 2. Consent and governance

* Written consent per speaker (pastor and any identifiable voice), research use, anonymised quotation.
* Retention policy stated at recording; withdrawal and deletion path.
* Store only `speaker_id`, `session_id`, `consent_id` with the data; no names in Git; audio stays local.
* No cloud upload without separate approval.

## 3. Annotation

1. Two independent annotators transcribe **the target preacher only** for the same 10-minute sample per service.
2. Third-pass adjudication; record inter-annotator WER.
3. Span labels: `TARGET`, `OTHER`, `MUSIC`, `SILENCE`, `OVERLAP`, `SCRIPTURE_REF`.
4. Freeze `sha256` manifests before any model runs; splits by speaker and session (train/tune/holdout).

## 4. Minimum manifest schema

```
case_id, session_id, speaker_id, consent_id, wav_A, wav_B, sha256_A, sha256_B, rate, device,
room, distance_m, pa, music, second_speaker, duration_s, sync_offset_samples, split,
gold_text_target, gold_text_other, scripture_refs, annotator_a_hash, annotator_b_hash, adjudicated
```

## 5. Operator baseline — the one that matters

**Use the preacher microphone only.** That is the simple, low-risk baseline. The second microphone is justified only
if it demonstrably improves target WER **and** card recall on the frozen holdout, without adding wrong cards. Every
candidate chain must be compared against this baseline on identical utterances.

## 6. Acceptance criteria for the next stage

* ≥ 3 services, ≥ 2 speakers (Nigerian/Ghanaian English where available), ≥ 20 minutes each.
* Close mic target WER measured; second-mic chain must beat it by **≥ 2 pp** with **0 wrong cards** and no more than
  a 5 % loss of correct cards.
* End-to-end latency p95 measured; `card_visible` observed separately if a candidate build exists.
