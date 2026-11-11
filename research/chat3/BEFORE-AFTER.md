# BEFORE → AFTER

## Base

* Repository `git@github.com:SolomonPhronesis/RhemaFlow.git`.
* Brief’s verified head `3eccb014…`; a **newer verified branch** also exists at
  `02ec12faa0ae8ad247b65d26c40eb89ac0f119ce` (`speaker-isolation-plan-20261111`), which contains `3eccb014` plus the
  previous round’s study. This round forks from **02ec12f** so that work is not lost; the ancestry is reported
  explicitly rather than silently substituting bases.
* New branch `rhemaflow/research-chat3/speaker-isolation-next-20261111`, same Chat 3 worktree (no new checkout:
  disk 3.9 GiB).

## After

| Change | Detail |
|---|---|
| `SPEAKER_ISOLATION_STUDY.md` | new — simulation model, measured SIR/retention/AUC, hard limits |
| `RESULTS.md` | replaced — PASS/NOT_RUN/NOT_AVAILABLE with the disk gate and reboot check |
| `BEFORE-AFTER.md` | replaced — this list, including the base-commit discrepancy |
| `scripts/two_channel_sim.py` | new — synthetic 2-channel generator, delay estimation, cancellation, overlap ROC |
| `tests/test_two_channel_sim.py` | new — 6 deterministic tests |
| `data/two_channel_sim.csv` | new — measured synthetic results (8 clips × 2 sources × 2 TIR) |
| App / engine source | **unchanged** |
| Audio, weights, names, lyrics, secrets, binaries | **none added** |

## Why no model runs

Disk 3.9 GiB < 4 GiB. The brief forbids model inference and corpus generation under the floor; the simulation is
memory-only (no audio written) and the tests are pure Python.
