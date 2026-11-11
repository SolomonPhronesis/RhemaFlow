# BEFORE → AFTER

## Base

* Repository `git@github.com:SolomonPhronesis/RhemaFlow.git`, verified head
  `0656784b92176826c3690bad23ba9e0a320d1f2d` (previous research branch).
* New branch `rhemaflow/research-chat3/r2t2-independent-streaming-20261111`, created from that head in the
  existing Chat 3 research worktree (no new checkout: disk 672 MiB is below the floor).

## After

| Change | Detail |
|---|---|
| `R2T2_CODE_AUDIT.md` | new — blob-verified upstream audit, licence, feasibility |
| `STREAMING_PROTOTYPE_DESIGN.md` | new — algorithm and test matrix |
| `scripts/stable_prefix.py` | new — model-free commit engine, reply validator, card gate |
| `tests/test_streaming.py` | new — 20 tests, all pass |
| `BASELINE_AND_ABLATIONS.md` | new — baseline with bootstrap CIs, ablations marked blocked |
| `ROADMAP_TO_6_PERCENT.md` | new — honest route to the aspirational target |
| `data/baseline_ci.csv` | new — 56 arm×condition CIs |
| `data/feasibility.csv`, `data/streaming_tests.csv` | new — matrices |
| App / engine source | **unchanged** |
| Deletions, audio, weights, lyrics, secrets, binaries | **none** |

## Why no model experiments

Disk 672 MiB < 4 GiB hard floor. The brief forbids model runs, builds, corpus expansion and worktree checkouts
under the floor; the safe work is source audit, saved-transcript analysis and model-free prototype code.
