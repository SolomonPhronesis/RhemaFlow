# BEFORE → AFTER

## Base

* `git@github.com:SolomonPhronesis/RhemaFlow.git`, base head
  `3f06d516342e8d0cc13633bf083f552b1f9e6c2c` (`adaptive-fir-isolation-20261111`), clean worktree.
* New branch `rhemaflow/research-chat3/real-speaker-validation-20261111`.

## After

| Change | Detail |
|---|---|
| `FORENSIC_WRONG_CARD.md` | new — exact wrong-card case, stage analysis, rejected guard |
| `FILTER_ADVANCE.md` | new — delay tracking implemented and measured; PBFDAF backlog |
| `OPERATOR_KIT.md` | new — consented dual-mic capture/annotation kit |
| `RESULTS.md` | replaced — phase status table |
| `scripts/fir_isolation.py` | `fir_tracking()` added (causal per-chunk delay update) |
| `tests/test_fir_isolation.py` | unchanged tests still pass (5/5); tracking covered by shared causality proof |
| `data/holdout_sdi.csv` | new — S/D/I per condition |
| `data/tracking_tune.csv` | new — tracking measured negative result |
| `data/gate_forensics.csv`, `data/guard_ratios.csv` | new — wrong-card forensics and guard feasibility |
| App / engine source | **unchanged** |
| Audio, weights, names, lyrics, secrets, binaries | **none added** |
