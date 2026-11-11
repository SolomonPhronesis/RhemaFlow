# BEFORE → AFTER

## Base

* Repository `git@github.com:SolomonPhronesis/RhemaFlow.git`, base head
  `6a5fc926dbd889d8672db2791ad822c0f0c3a940` (`speaker-isolation-next-20261111`), clean worktree.
* New branch `rhemaflow/research-chat3/causal-dualmic-validation-20261111` in the same Chat 3 worktree.

## After

| Change | Detail |
|---|---|
| `ORACLE_AUDIT.md` | new — exactly which future samples the 2.54 % used |
| `CAUSAL_BASELINES.md` | new — 5 methods, CIs, cards, robustness |
| `REAL_GOLD_PROTOCOL.md` | new — acquisition/annotation protocol; `REAL_GOLD_NOT_AVAILABLE` |
| `ACCURACY_ROADMAP.md` | new — milestones, transfer, next stage |
| `RESULTS.md` | replaced — phase-by-phase DONE/BLOCKED table |
| `scripts/causal_isolation.py` | new — gated causal NLMS + clean/reverb builders |
| `scripts/score_causal.py` | new — WER, intrusion, paired bootstrap CIs |
| `tests/test_causal_isolation.py` | new — 5 tests incl. causality proof |
| `data/causal_*.csv` | new — aggregate, per-condition, CIs, robustness, cards |
| `charts/causal_wer.svg`, `charts/causal_robustness.svg` | new |
| App / engine source | **unchanged** |
| Audio, weights, names, lyrics, secrets, binaries | **none added** |
