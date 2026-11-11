# BEFORE → AFTER

## Base

* Repository `git@github.com:SolomonPhronesis/RhemaFlow.git`, base commit `c8ad92b70c116d71cc390b09560d15b20d24e70a`.
* Branch `rhemaflow/research-chat3/scorer-speaker-lyrics-20261111`, isolated worktree, clean status at start.

## After

| Change | Detail |
|---|---|
| `scripts/wer.py` | replaced v1 with v2: correct tokenisation, explicit ids/manifest mapping, composite keys, fail-closed coverage, S/D/I, empty-ref policy, normalised/verbatim modes |
| `tests/test_wer.py` | new: 20 fixture/unit tests (all pass) |
| `scripts/cloud_contract_test.py` | v2: +6 cases (versioning, stale key, crash/resume, corrupt cache) → 15/15 |
| `scripts/lyrics_match.py` | unchanged logic; documents text-only status |
| `data/*.csv` | added scorer provenance, fixtures, Opus rescore, card policy; refreshed contract results |
| docs | SCORER_AUDIT.md, SPEAKER_PLAN.md, LYRICS_EVAL.md, REPLICATION_TESTS.md, RESULTS_NEXT.md, BEFORE-AFTER.md, SHA256SUMS.txt |
| App/engine source | **unchanged** |
| Deletions | **none** |
| Audio/weights/lyrics/secrets/binaries | **none added** |

## Why no engine change

The speaker work produced a negative result (no gate removes wrong cards without losing correct ones), and the
scorer defect was tooling. Changing the Rust engine with no validated gain would be an unverified production change.
