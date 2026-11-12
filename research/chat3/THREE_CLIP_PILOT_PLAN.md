# Three-clip paired pilot — prepared, NOT_RUN

**RESEARCH_GO · PRODUCTION_NO_GO. Zero models or speech clips were run in this continuation.**

## Required gates before any pilot

- Maintain at least **8 GiB free**, with **15 GiB** the target for heavyweight
  work and additional space for any proposed conversion/checkpoint. Current
  inventory was about 3.78 GiB. Do not delete owner files or caches by assumption.
- Supply an explicit provenance/consent record allowing the intended local
  research for every voice, music and distractor source; hash the actual bytes.
  The recovered 40-WAV set is still `RIGHTS_PENDING_DO_NOT_UPLOAD` and ineligible.
- Verify a compatible already approved inference runtime, loader and tokenizer
  against the precise local checkpoint. Model-folder presence is insufficient.
  No install, new model download, hosted call or conversion is approved here.
- Freeze a source/condition manifest and gold independently of decoder output.
  If no eligible source/runtime exists, report the specific blocked gate and
  retain readable plans; do not manufacture transcripts or model scores.

## Minimal three-file sanity pilot

| Clip | Content and purpose | Independent gold / controls |
| --- | --- | --- |
| P1 | Consented clean target speech, 5–15 s, close mic | Literal target-only transcript, timed expected card event, target identity |
| P2 | The exact P1 recording after deterministic MP3 encode/decode | Same spoken reference and source cluster; codec/hash/sample-count provenance, no silent trimming |
| P3 | Independently consented **target-absent** music/chatter/other-preacher quotation | Empty target reference, all audible speakers annotated, no Bible card allowed |

This interprets the requested music/chatter/no-target condition as an explicit
negative control. It is a **sanity pilot**, not a noisy-target robustness study.
A later matched noisy-target P1 mixture is an additional condition, not a result
silently attributed to P3. Report lyric/music confusion and wrong-speaker cards
separately. The earlier three-target-condition `prepare_three_clip_pilot.py`
can prepare codec/procedural variants after its own rights/disk checks; it does
not create independent real chatter, target absence, or the P3 rights record.

P1/P2 are one source cluster, not two independent samples. A three-file pilot
cannot supply meaningful church-level confidence intervals or establish <6%.
No-target insertions/cards are reported separately from target corpus WER.
Do not pool the synthetic/codec pilot into the later real church holdout.

## Owner priority and exact model arms

Run **one model at a time**, unloading it before the next; never start a parallel
sweep on the 16 GiB laptop. All arms see the same frozen P1/P2/P3 bytes.

1. Qwen 1.7B en16k **4-bit with 8-bit embedding override**, weight SHA
   `05b7fbea3adf326c59c5d5bbdd02a0eb001308e336c880fda170108c1e450e86`.
2. Parakeet v2 **Q4_K_M**, SHA
   `4853f9653f641d376e6f7de65d73c7a34a73677704a606727bf51acc83f999f3`.
3. Larger verified Parakeet v2 **Q8_0**, SHA
   `f0d0e99cebb6d3b83f1f7069b82b5d3c2e39a54545b0da039cb4bafd9c4e5caa`.
4. Qwen 1.7B en16k **BF16**, SHA
   `2336d2bc828e74d6c38c0b31f91582d8518c73ac3cab496b784819d16e7b72e7`.

The pure-Q4 Qwen variant is a separately identified alternative, not a fifth
silently substituted arm. Exact config/tokenizer hashes and byte sizes accompany
`RESEARCH_PRIORITY_AND_EVIDENCE.csv` and the tokenizer inventory. The 729,574,912
byte Q8 file is confirmed v2 in GGUF metadata; the separately labeled 1.256 GB
legacy v3/F16 file is not relabeled as a larger v2/Q8 checkpoint.

The historical Qwen WER cannot be assigned to embed8/BF16/pure-Q4 without its
original run identity. All four current-arm WER cells remain null/NOT_RUN.

## Reproducible execution record after the gates pass

1. Verify audio, checkpoint, tokenizer/config and runner hashes. Record source
   repository/revision, runtime versions and the actual decoder method. Use
   `local_files_only` or equivalent and disabled automatic downloads. A loader
   mismatch is `BLOCKED_RUNTIME`; do not silently fetch a replacement model.
2. For each arm perform one cold start and a bounded warm pass, batch 1. Use
   explicit endpointing, chunk/right-context/prefix policy and timeout. No gold,
   Bible reference, expected verse, speaker truth or held-out vocabulary is sent
   to the decoder. The proposed V2 envelope only carries observed audio and
   pinned model identities; it is offline and not integrated into Personal.
3. Preserve actual timestamped transcript/hypothesis/commit records, model/runner
   provenance, S/D/I/N per target clip, emitted words on P3, and actual matcher
   events. `cards:null` means not run; `cards:[]` means observed and no event.
   A verse spoken by another preacher is false even when the verse is correct.
4. Capture audio-arrival, ASR completion, matcher completion and physical
   `card_visible` timestamps on a shared monotonic timebase. Measure p50/p95,
   pipeline RTF, peak RSS/swap, measured energy with method/duration, battery,
   dropouts and failure logs. File decode time alone is not real-time UI latency.
5. Preserve immutable past-only commit output; perturb every future suffix and
   assert no earlier decoder input/output changes. Record any deliberate
   buffering as latency. Do not reuse the historical positive-lag aligner as a
   zero-lookahead reference. Test phrase repetition, chunk boundaries, EOS,
   handoff, silence and long-utterance reset without future sample access.
6. Score identically normalized literal transcripts. Aggregate target WER as
   `Σ(S+D+I)/ΣN`; show all clip coverage/failures. Check P3 card silence **and**
   correct P1/P2 retention. No threshold may be tuned on these frozen controls.
   Unknown matcher or physical UI measurements leave those gates unverified.

No generic executable command is supplied that would load an unverified runtime.
The existing base-decoder callback and new envelope have deterministic mock tests;
no mock callback is reported as a real Qwen/Parakeet adapter. To run actual
inference, bind that callback to the approved local loader, validate identity and
hard timeouts first, then capture genuine logs. No paid/provider provisioning is
part of this plan.

## Expansion and stop rules

Continue to 40 and then 648 only after valid pilot logs, matched rights and
coverage. Preserve a failure rather than dropping a problematic arm or clip.
For the owner goal collect **at least three consented 48 kHz same-clock dual-mic
services**, two independent target-only transcripts and adjudication, all speaker/
overlap/no-target labels and an immutable speaker/session/church-disjoint holdout.
Use close/lapel-only as the baseline, raw dual-mic next, then independently bound
speaker selection/isolation and finally model adaptation. Keep each added stage
ablatable and latency-accounted. Do not infer real church performance from the
40 synthetic KJV clips or the old 648 matrix.

Current checkpoint: **BLOCKED_DISK · BLOCKED_RUNTIME · BLOCKED_RIGHTS · BLOCKED_GOLD**.
No ordinary permission question is pending; the operator needs actual eligible
assets and sufficient headroom before the bounded run is executable. Download,
installation, paid training and product promotion remain separately gated.
