# BEFORE → AFTER

## Base

* `git@github.com:SolomonPhronesis/RhemaFlow.git`, base head
  `ddb36f19cb3b0e7e9d942ac3c994557044fc00bc` (`causal-dualmic-validation-20261111`), clean worktree.
* New branch `rhemaflow/research-chat3/adaptive-fir-isolation-20261111`.

## After

| Change | Detail |
|---|---|
| `ADAPTIVE_FIR_RESULTS.md` | new — frozen-split realistic-acoustics study, negative FIR result, safety failure |
| `SPLIT_AND_PROTOCOL.md` | new — frozen splits, anti-leakage rules, real two-mic checklist |
| `RESULTS.md` | replaced — this round’s DONE/BLOCKED table |
| `scripts/fir_isolation.py` | new — realistic synthesis + scalar/FIR/double-talk causal cancellers |
| `scripts/score_fir.py` | new — holdout WER, paired bootstrap, cards |
| `tests/test_fir_isolation.py` | new — 5 tests incl. strict past-only proof |
| `data/*.csv`, `data/throughput.json` | new — holdout results, CIs, tune grid, splits, cards |
| `charts/holdout_wer.svg`, `charts/holdout_signal.svg` | new |
| App / engine source | **unchanged** |
| Audio, weights, names, lyrics, secrets, binaries | **none added** |
