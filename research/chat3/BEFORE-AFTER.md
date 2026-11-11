# BEFORE → AFTER

## Base

* Repository `git@github.com:SolomonPhronesis/RhemaFlow.git`, verified head
  `3eccb01443d4ce929998bceda562d447d7341624` (branch `rhemaflow/research-chat3/r2t2-independent-streaming-20261111`).
* Worktree clean at start; no new worktree created (disk 662 MiB, below the checkout floor).
* New branch `rhemaflow/research-chat3/speaker-isolation-plan-20261111` created from that head.

## After

| Change | Detail |
|---|---|
| `NEXT_SPEAKER_STUDY.md` | new — causal question, B0–B5 arms, prerequisites, exit criteria, manifest schema |
| `DISK_RECOVERY_CANDIDATES.md` | new — read-only inventory; **nothing deleted** |
| `RESULTS.md` | replaced with this round's PASS/NOT_RUN/BLOCKED table |
| `BEFORE-AFTER.md` | replaced with this change list |
| `scripts/target_gate.py` + `tests/test_target_gate.py` | new — model-free card/target gate evaluator, 9 tests |
| `data/condition_manifest.csv` | new — 17 conditions, ref words, provenance, licence |
| `data/audio_provenance.csv` | new — per-condition SHA-256 of the sorted clip-hash set |
| `data/baseline_ci.csv` | new — 56 bootstrap CIs |
| `data/gate_sweep_648.csv` | new — measured confidence-gate sweep |
| `data/disk_candidates.csv` | new — cleanup proposals, unbounded |
| App / engine source | **unchanged** |
| Audio, weights, lyrics, secrets, binaries | **none added** |

## Why model-free

Disk 662 MiB < 4 GiB hard floor. The brief and the safety gates forbid model inference, corpus creation and builds
under the floor; the documentation, audit and model-free tests are the safe deliverable.
