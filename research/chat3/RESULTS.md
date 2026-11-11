# RESULTS — real dual-mic validation: causal isolation vs oracle

**Date:** 2026-11-11 18:05–21:40 UTC · **Disk:** 11 GiB → 9.5 GiB · **Swap:** 1.5 GiB
**Verdict: `RESEARCH_GO` / `PRODUCTION_NO_GO`.**

## Phase 0 — preflight

| Check | Result |
|---|---|
| Branch / head | `speaker-isolation-next-20261111` @ `6a5fc92…`, clean worktree |
| Remote | verified; all research branches present |
| Q4 hash | `4853f965…` (unchanged) |
| Qwen 1.7B MLX | 1.4 GB directory present, `05b7fbea…` |
| Scorer | `wer.py` v2, 20/20 tests |

## Phase 1 — oracle audit (`ORACLE_AUDIT.md`)

The 2.54 % used **whole-clip** cross-correlation for delay and **whole-clip** least squares for α — both read future
samples — on a synthetic pair with known components, fixed 3 ms delay, fixed −6 dB leak, no reverb and no drift.
It is an **oracle ceiling**, not a deployable result. Reproduced from frozen transcripts: 109 edits / 4,288 words
= **2.542 %**.

## Phase 2 — causal baselines (`CAUSAL_BASELINES.md`)

160 mixtures, 4,288 words, real Q4 Metal, frozen scorer:

| Method | Causal | WER | Intrusion /100 |
|---|---|---:|---:|
| close mic only | — | **66.535 %** | 29.55 |
| room mic only | — | 94.263 % | 58.84 |
| naïve mix | yes | 90.065 % | 52.99 |
| **causal NLMS (gated)** | **yes** | **2.822 %** | **2.38** |
| oracle LS | no | 2.542 % | 2.08 |

* Paired bootstrap: close − causal = **+58.88 to +68.47 pp** (2,000 draws).
* Cards on the causal output: **134 QUOTE, 134 correct, 0 wrong**, 8 review, 18 none.
* No-target controls through the same chain: **28/28 NO_CARD**, 0 wrong, 1 word total.
* Clean-audio degradation: **1.586 %**, identical to baseline — the interference-dominance gate prevents the
  canceller from subtracting the pastor.
* **Robustness failure:** with 120 ms reverb and ±1 dB drift, causal WER is **68.097 %** vs close 68.19 % — no real
  gain. A scalar gain cannot handle a reverberant room.

## Phase 3 — real corpus: `REAL_GOLD_NOT_AVAILABLE`

No consented dual-channel church recordings or human target transcripts exist. The acquisition protocol is in
`REAL_GOLD_PROTOCOL.md`; synthetic results are not presented as church results.

## Phase 4 — roadmap (`ACCURACY_ROADMAP.md`)

Single-channel: Q4 26.306 %, Qwen 24.387 %, V3/V4 26.306 % — **no single-mic method reached <20 %**, let alone
<6 %. **<6 % is reached only on synthetic two-channel isolation** (2.54 % oracle, 2.82 % causal). The binding
constraint is capture. Real deployment needs an adaptive FIR + real reverb/drift data.

## Status table

| Requirement | Status | Evidence |
|---|---|---|
| Oracle audit and reproduction | **DONE** | `ORACLE_AUDIT.md`, 2.542 % reproduced |
| Causal baselines without oracle leakage | **DONE** | `CAUSAL_BASELINES.md`, 5 methods |
| Causality proof (past-only) | **DONE** | `tests/test_causal_isolation.py::test_only_past_samples_are_used` |
| Clean degradation check | **DONE** | 1.586 %, no loss |
| No-speech / no-target card check | **DONE** | 28/28 NO_CARD, 0 wrong |
| Reverb/drift robustness | **DONE (negative)** | 68.097 % — scalar canceller fails |
| Real dual-channel church gold | **BLOCKED** | `REAL_GOLD_NOT_AVAILABLE`; protocol provided |
| Multi-mic hardware validation | **NOT_RUN** | no recordings, no devices |
| Sung lyrics | **NOT_RUN** | no authorised sung fixtures |
| Production integration | **NO-GO** | research only |

## Reproduction

```bash
python3 research/chat3/scripts/causal_isolation.py          # builds 720 synthetic channels
python3 research/chat3/scripts/score_causal.py              # WER, CIs, robustness
python3 research/chat3/tests/test_wer.py -v                 # 20/20
python3 research/chat3/tests/test_causal_isolation.py -v    # 5/5
```
