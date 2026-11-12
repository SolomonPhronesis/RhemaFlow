# R2T2 / Qwen checkpoint ledger — 2026-11-12

Exact local paths and full hashes are in `data/r2t2_qwen_20261112/asset_inventory.json`.
Resource byte counts, CPU/RAM/swap and active interpreter are in `run_context.json`
and `runtime_model_audit.json`. Null means unavailable, not a zero-error run.

| STEP | Accessible evidence / work | Clips and models actually run | WER numerator / denominator | ASR p50/p95, RTF, wrong/correct cards | Outcome and smallest next step |
|---|---|---|---|---|---|
| 0 | Verified `7756f648…`, isolated new branch, original 93 tests | 0 speech clips; no model | null / null | all null | Resource audit: initial ~6.2 GiB free, below 8 GiB floor; proceed model-free |
| 1 | Official R2T2/Qwen trees + paper; 20 text blobs hash-verified | 0; no R2T2 weights or generated outputs | null / null | all null | Deep source audit completed; no training recipe/checkpoints in R2T2 Git; inspect local assets |
| 2 | Two ZIPs yield one identical 40-WAV source set; 40/40 hashes; 3 Qwen variants plus Q4/Tiny hashed | 0 inference clips; **40 source clips audited** | Actual ASR null / null; source gold 1,072 normalized words | all null | Audio readable but rights-pending; disk/runtime gates block three-clip ASR pilot |
| 3 | Independent wrapper, 34 authored text traces × 3 policies | 0 model runs; 6 target + 28 control text traces/policy | Text mechanism only: baseline 0/24; each agreement policy 2/24 | Real-ASR values all null; authored lag reported separately | No rewrites but other-speaker text remains; no safe candidate |
| 4 | Offline producer/consumer and scorer CLI; temporary procedural media roundtrip | 0 model runs; one 0.4 s tone generates 3 temporary variants in unit test | Speech ASR null / null | all null; actual Personal consumer NOT_TESTED | 136/136 tests; collection/scoring kit ready; temporary media deleted |
| 5 | Research-only source/evidence published at `b983a8b9…`; report/manifest follow | 0 model runs | null / null | all null | Exact final HEAD/remote proof in delivered push receipt; resume only eligible three-clip pilot |

Historical model matrix (saved evidence only): Q4 26.306%, Qwen 24.387%, Tiny
44.789%, 560 target clips / 15,008 words. No current value replaces those numbers.
The processed-audio Qwen arm is NOT_RUN. CPU is M1 Pro; RAM 16 GiB; final-test
free space ~7.41 GiB. ASR CPU load, peak model RSS and energy were not measured.

`PUSH_VERIFIED` · `RESEARCH_GO` · `BLOCKED_GOLD` · `PRODUCTION_NO_GO`.
