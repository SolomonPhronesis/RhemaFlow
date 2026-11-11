# RESULTS — reverberant isolation forensics, delay tracking and the operator kit

**Date:** 2026-11-11 23:04–00:10 UTC · **Disk:** 10 GiB at start · **Branch:** `real-speaker-validation-20261111`
**Verdict: `RESEARCH_GO` · `BLOCKED_GOLD` (church accuracy) · `PRODUCTION_NO_GO`.**

## 1. Phase 0 — preflight

| Check | Result |
|---|---|
| Repository / head | `SolomonPhronesis/RhemaFlow`, base `3f06d51…`, clean worktree |
| Remote | `PASS` — base branch present, all prior research branches intact |
| Model artifacts | Q4 `4853f965…`; Qwen 1.4 GB directory; Tiny present |
| Scorer | v2, 20/20 tests, unchanged |
| Disk / swap | 10 GiB free / 0.4 GiB swap |

## 2. Phase 1 — forensic analysis

* **Wrong card:** `CTRL03` (chatter-only), `QUOTE` → **Luke 1:17**, confidence 0.833, text is the other preacher
  quoting that verse. Failure stage = **speaker attribution**, not matching or tokenisation. Details:
  `FORENSIC_WRONG_CARD.md`.
* **418 no-target words:** the FIR did not remove the competing speaker; ASR transcribed it.
* **Candidate guard (close/room energy ratio) rejected:** holdout range −5.83…−2.03 dB overlaps the control range
  −6.01…−6.02 dB; a threshold that blocks the control also blocks correct holdout cards, and tuning on controls
  would be evaluation-set leakage. Output/room coherence also failed to separate (ρ mean −0.055).
* **S/D/I per condition** on the holdout: `data/holdout_sdi.csv`.

## 3. Phase 2 — filter advance

| Method | ΔSIR (tune) | Holdout WER |
|---|---:|---:|
| fixed-delay FIR 32 taps (previous best) | **+3.39 dB** | **51.862 %** |
| FIR with 2 s delay tracking (new) | **+0.48 dB** | not run — signal-level result already worse |
| scalar gated NLMS | +6.32 dB (holdout) | **41.223 %** |

Delay tracking **degraded** the FIR: per-chunk re-alignment breaks the filter state and lag estimates are noisy under
reverb. Reported as a negative result. The partitioned frequency-domain filter is `NOT_IMPLEMENTED` this round and is
the top backlog item.

## 4. Phase 3 — operator kit

`OPERATOR_KIT.md`: same-clock dual capture, sync pulse, gain log, consent/retention, two independent annotators,
target-speaker spans, frozen splits and hashes, and the explicit operator baseline **“just use the preacher mic”**.

## 5. Phase 4 — status

| Requirement | Status | Evidence |
|---|---|---|
| Lineage + new branch | **DONE** | base `3f06d51…` |
| Code/leakage audit | **DONE** | past-only unit tests; algorithm signature excludes target/leak/delay; tune-only selection |
| Wrong-card forensic + minimal case | **DONE** | `FORENSIC_WRONG_CARD.md`, `data/gate_forensics.csv`, `data/guard_ratios.csv` |
| Guard that removes the wrong card without losing correct ones | **NOT FOUND** | measured overlap; no guard added |
| Delay-tracking causal FIR | **DONE (negative)** | `data/tracking_tune.csv` |
| Partitioned frequency-domain filter | **NOT_IMPLEMENTED** | stated, backlog |
| Q4 on bounded holdout | **DONE** | 41.2 % scalar / 51.9 % FIR / 67.2 % close |
| Qwen on processed audio | **NOT_RUN** | Q4 result sufficient; no resource need |
| Operator kit ≥3 services | **DONE (protocol)** | `OPERATOR_KIT.md`; recordings `BLOCKED_GOLD` |
| Real church gold | **BLOCKED** | no consented recordings |
| Production | **NO-GO** | safety failure unresolved |

## 6. Toward <6 %

* Synthetic oracle: **2.54 %** (non-causal, not deployable).
* Synthetic causal, idealised room: **2.82 %** (does not survive reverb).
* Synthetic causal, realistic reverb/motion: **41.2 %** best (scalar); FIR 51.9 %.
* Real church human gold: **`BLOCKED_GOLD`** — no number exists.

The 6 % target remains unreached on any deployable or real condition. The binding blocker is capture + speaker
attribution, not streaming or decoder size.

## 7. Commands

```bash
python3 research/chat3/tests/test_fir_isolation.py -v     # 5/5
python3 research/chat3/scripts/fir_isolation.py           # rebuild frozen corpus
python3 research/chat3/scripts/score_fir.py               # holdout WER/CIs/cards
```
