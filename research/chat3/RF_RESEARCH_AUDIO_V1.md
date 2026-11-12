# RF_RESEARCH_AUDIO_V1 — offline research exchange and collection/scoring kit

Version 1, 2026-11-12. Reference producer/consumer/scorer:
`scripts/rf_research_audio.py`; tests: `tests/test_rf_research_audio.py`.
This is a local offline contract. It is not an installed Personal integration.
Research owns these files; Personal must independently decide whether to test a
research flag. No product setting, model selection or production code is changed.

## Case array: operator/scorer side only

Each object has `schema="RF_RESEARCH_AUDIO_V1"`, anonymous `case_id`, `session_id`,
`speaker_id`, `condition`, explicit `evidence_class`, `split` (train/tune/holdout/
control), `rights_status` (verified/pending/denied), and boolean `research_allowed`.
`channels` contains close first, optionally room. Each carries `role`, relative
`path`, SHA-256, sample rate (16000 or 48000), sample count and shared `clock_id`.
Two channels require the same sample rate, length and recorder clock. Record
sync offsets, clipping/gain logs, resampler and device metadata in the operator's
provenance ledger. Keep audio outside Git. Model runners must verify actual file
bytes, headers and permission eligibility against this record before decoding.

The separate `expected` object carries boolean `has_target`, `gold_text` and
`verse_ref` (explicit empty string when inapplicable). Empty-reference controls
remain in the case list. A positive target must have scored gold words. Timed
target/other/overlap/no-target spans and adjudication hashes belong in the local
annotation ledger, never in model prompts.

`inference_request(case, model, request_id)` rejects pending/denied assets and
creates an allow-listed request containing only schema, request ID, case ID,
channel metadata and model identity. Gold, expected verse, target presence,
speaker ID, condition and split are absent. The reference producer supports
Qwen3-ASR-1.7B **base-family derivatives**, Q4 and Tiny with explicit precision
and SHA-256. It rejects R2T2 family identifiers. Model hashes must refer to the
actual local artifacts; a syntactically valid hash is not a licence or identity
verification. Real operators must reconcile the model audit first.

## Decoder / hypothesis interface

`PseudoStreamingBase` calls an injected local decoder with read-only, cumulative
mono 16 kHz PCM and an increasing request ID. The reply contains exact
`request_id`, `model_id`, and string `text`, including an explicit empty string
for no text. Model-token mode additionally requires actual tokenizer IDs and an
injected decode function whose output matches the supplied text. Word holdback
is labelled words, not BPE tokens. No backend is imported or downloaded by this
library. A real decoder adapter must separately enforce a hard timeout; arbitrary
in-process callbacks cannot be forcibly interrupted by this wrapper.

Only already received PCM is passed. Prefix release is append-only, divergent
hypotheses are surfaced rather than swallowed, and a 30-second default utterance
bound requires an explicit endpoint. EOS is checked at exact chunk boundaries as
well as partial tails. A true model-token EOS decode and all runtime benchmarks
remain unverified until an eligible real decoder is supplied.

## Result JSONL and immutable card events

For every `(case_id, model_id)` return `status="OK"`, `text`, `input_sha256`
(exact close/ASR input), and `cards`. A paired-channel experiment must additionally
return `input_channel_sha256={close:...,room:...}`. **`cards=null` means matcher
not run; `cards=[]` means matcher run and no cards.** Never substitute one for
the other. A failed model result is not silently omitted or counted as success.

Each card has kind QUOTE/REVIEW and `verse_ref`. The optional offline
`CardEventConsumer` also requires schema, stable `card_id`, SHA-256 of its
committed text snapshot, and ordered `audio_end_ms`, `asr_done_ms`,
`matcher_done_ms` from one session clock origin. `card_visible_ms` is null: this
offline contract cannot observe a display. Duplicate identical events are
idempotent; changing a previously emitted card ID is rejected. A matching text
hash proves linkage to a supplied text snapshot, **not target-speaker identity**.

Optional `timing` fields are `load_ms`, `decode_wall_ms`, `audio_duration_ms`,
`end_to_end_ms`, `peak_rss_bytes`, `energy_joules`. Use null or omit unavailable
measurements. The scorer reports p50/p95 and measured-case denominators,
aggregate decode RTF, peak reported RSS and complete energy coverage separately.
No process-RSS, latency, energy or UI measurement is inferred from model size.

## Run the ready-to-use local checks

From `research/chat3`:

```bash
for t in tests/test_*.py; do python3 -B "$t"; done
python3 -B scripts/study_base_commit.py --out /path/to/new-text-study.json
python3 -B scripts/score_research_exchange.py --cases /local/cases.json \
  --records /local/results.jsonl --models q4,qwen17b,tiny --baseline q4 \
  --out /local/paired_metrics.json
```

The scorer rejects missing/duplicate keys, input-hash disagreement, failed
inference and tune/train cases in an evaluation. WER is Σ(S+D+I)/ΣN on target
references only; controls get separate word and emitted-card counts. A no-target
quote stays wrong even when the verse string matches. If any actual card data is
missing, card metrics are null. Paired WER CIs use 2,000 resamples, seed 20261112;
real cases cluster by target speaker; augmented/procedural cases use explicit
`cluster_id` when present, otherwise case ID. All variants of a shared source
must supply the same cluster ID (the pilot preparer does this). Statistical
independence still requires a genuinely speaker/session-disjoint frozen corpus.

## Next real three-clip checkpoint

`scripts/prepare_three_clip_pilot.py` is a **prepare-only** utility. Supply one
eligible, hashed 16 kHz mono PCM16 target WAV and a separate provenance JSON with
`rights_status="verified"`, `research_allowed=true`, matching `source_sha256`,
target gold, anonymous session/speaker IDs and optional verse reference. It
requires ≥8 GiB free, an already installed ffmpeg, and a fresh output directory
outside the Git checkout. It preserves the source, makes a clean copy, an MP3
encode/decode of that exact source, and a deterministic three-tone music overlay
at 0 dB SNR with logged gain. MP3 sample-count drift fails rather than being
silently trimmed. Models, scoring and matching do not run in preparation.

```bash
python3 -B scripts/prepare_three_clip_pilot.py --source /eligible/target.wav \
  --rights-record /eligible/provenance.json --out /local-work/new-three-clip-pilot
```

Feed each prepared **identical file** to all three independently verified local
model adapters; record hashes, true precision, cold/warm loading, resources and
timestamps. Then score the complete records with the CLI above. The current
recovered KJV archive remains rights-pending; this command was not run on it.
Scale to 40 and then 648 only after this small checkpoint passes and provenance,
disk, runtime and no-target controls are available. Processed-audio comparisons
need the same transformed inputs; historical saved counts are not replacements.

## Real church acquisition and gates

Follow `OPERATOR_KIT_PBFDAF_ADDENDUM.md`: ≥3 consented services, same-clock raw
48 kHz close/room capture, lapel 15–20 cm, room 3–6 m, sync slate, gain/device logs,
two independent target-only transcribers and adjudication, other-speaker/overlap/
silence labels and frozen speaker-disjoint splits. Three nonempty speaker-disjoint
train/tune/holdout partitions require at least three distinct target speakers.
No new consented gold is created by this kit.

Keep close-only as the baseline. Product consideration requires ≥5 pp paired
real target-WER improvement, zero additional wrong cards, zero emitted no-target
cards, ≤5% lost correct cards, measured end-to-end latency and device robustness.
Correct-card retention uses matched baseline/candidate correct case opportunities
and reports its denominator; a zero denominator yields null loss, not a pass.
Raw quote counts alone cannot establish it. All gates still require explicit product
approval. No safe candidate or installation is offered by this run.

The **reference research producer and consumer** pass contract tests locally.
The actual Personal producer/consumer, its model loop and UI are `NOT_TESTED`.
`RESEARCH_GO` · `BLOCKED_GOLD` · `PRODUCTION_NO_GO`.
