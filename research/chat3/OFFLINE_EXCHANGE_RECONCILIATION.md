# Offline exchange reconciliation — research only

The public definitions, not a private Personal checkout, are the source for this
comparison. `RF_RESEARCH_AUDIO_V1.md`, `rf_research_audio.py`, the V2 draft in
`under6_evaluation.py`, and all prior artifacts remain unchanged. No installed
Personal producer, model loop, matcher or display was inspected or modified.
Its earlier exported commit identity is historical metadata, not current access.

| Boundary | Published V1 | New strict V1 research profile | Existing V2 draft |
| --- | --- | --- | --- |
| Model families | Base Qwen, Parakeet v2 Q4, Tiny; explicit precision/hash | Same V1 family validation, further limited to current pilot pins | Adds v2 Q8 and tokenizer hash; not an installed protocol |
| Gold/condition/speaker labels | Operator/scorer side | Removed from decoder envelope, including nested extras | Operator/scorer side |
| Nested model/channel dictionaries | Reference producer forwards model extras and channel objects | Explicit primitive-field copies; source objects cannot mutate the emitted channel dictionaries | Explicit model/channel field selection |
| Case/model/clock identifiers | Supplied labels | Hashed case/clock IDs and canonical family/precision/hash model ID; local crosswalk required | Hashed request ID; different fields |
| Audio paths | Safe relative paths | Requires opaque `audio/<32–64 hex>.wav` names | Relative local paths |
| Wrong-speaker safety | Legacy paired scorer is not per-card speaker attribution proof | Intake does not classify speakers or emit cards | Offline trial scorer requires per-card target/other/unknown attribution and gold event IDs |
| Compatibility | Reference code tested | New opt-in profile; no installed consumer verified | Draft only; never silently downgrade Q8 to Q4/V1 |

Source inspection found a concrete metadata boundary risk: V1's top-level
allow-list does not strip unknown fields inside `model` or each channel. The
new `scripts/offline_exchange_guard.py::strict_request` filters those objects,
checks the public pilot pin, canonicalizes labels and requires opaque filenames.
Fourteen new model-free tests exercise nested label/credential-field removal,
copy isolation, wrong pins, restricted family/Q8 rejection, byte/header/annotation
checks, rights/access separation, pairing, symlinks and truncation. This does not
change the original V1 behavior, create a Personal patch or fix speaker identity.
A trusted decoder adapter must still prevent prompt/filename leakage and enforce
its own actual artifact identity, audio-arrival boundary and hard timeout.

The strict profile uses the same V1 top-level shape, but **is not a drop-in
Personal integration**: keep a private crosswalk from integer request ID and
hashed emitted case/clock IDs to the original offline case/parent/cluster/clock IDs. Restore
that mapping consistently before scoring. Never send the crosswalk, gold,
speaker truth, expected verse, rights ledger or filenames containing answers to
the decoder. Q8 requires a separately reviewed V2-capable adapter; matching the
Q8 file's expected hash does not make a V1 consumer support it.

**Owner export procedure.** The Personal owner chooses an already authorised,
rights-cleared recording source and a separate local export directory. Export
only eligible opaque WAVs, case metadata, rights/consent references and independent
annotation sidecars. Keep names, credentials, application databases, source code,
model weights, restricted R2T2 material and unrelated services outside the bundle.
No automatic upload or live Personal connection is part of this exchange.

Use exactly three V1 cases with extra `pilot_role` values `clean_target`,
`codec_target`, `no_target`. Retain the existing required V1 fields, including
explicit evidence class, rights state, split, expected target-only text and
channel hashes/rates/counts/shared clock. P2 declares `parent_case_id`,
`parent_source_sha256` and the same nonempty `cluster_id`/gold as P1. P3 must have
its own target-absent audio and empty target gold; a target-containing music
mixture is not this control. The earlier preparer's three target-containing
variants do not automatically supply this new P3.

Each case supplies `gold_provenance.annotation_path` and `annotation_sha256`.
The hashed UTF-8 JSON sidecar records `origin="human"`,
`independent_of_asr=true`, `adjudicated=true`, at least two distinct anonymous
`transcriber_ids`, `source_sha256`, `has_target` and exact `gold_text`. P2 links to
P1's original source digest; P3 links to its own source. These are declarations
requiring owner review, not machine proof of human identity, consent or truth.

From the research checkout, after the owner explicitly supplies the export:

```sh
python3 -B research/chat3/scripts/offline_exchange_guard.py \
  --root /approved/offline-export --cases /approved/offline-export/cases.json
```

This command reads only the supplied bundle. It hashes actual audio, inspects
mono PCM16 WAV headers/payloads and 5–15 s duration, rejects escape/truncation,
checks annotation bytes/linkage, and distinguishes `FOUND_READABLE`, `DENIED`,
`NOT_FOUND`, `RIGHTS_PENDING` and `BLOCKED_GOLD`. A readable file does not confer
rights. Even complete declarations leave human rights/gold/codec-lineage review
required, actual model/runtime identity unverified, execution `NOT_RUN`, real
WER null, `asr_execution_authorized:false` and `PRODUCTION_NO_GO`.

No eligible owner export was supplied in this continuation, so the tool was
exercised only on temporary procedural containers/metadata in tests. These tests
are not independent human gold, speech recognition or a rights approval.
