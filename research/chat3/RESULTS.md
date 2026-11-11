# RESULTS — target-speaker isolation study (model-free stage)

**Date:** 2026-11-11 16:23–16:50 UTC · **Branch base:** `3eccb014…` (verified) · **Disk:** 662 MiB → 1.7 GiB free
**Gate applied:** below 4 GiB → **no model inference, no corpus creation, no builds**.
**Verdict: `RESEARCH_GO` / `PRODUCTION_NO_GO`.**

## 1. PASS — what was verified this round

| Item | Result |
|---|---|
| Preflight (df, APFS, swap, git, remote, model paths) | **PASS** — remote verified, HEAD `3eccb014…`, models present (Q4 475 MB, Qwen 1.4 GB, Tiny 77 MB) |
| Scorer v2 regression suite | **PASS 20/20** |
| Stable-prefix prototype suite | **PASS 20/20** |
| Target-gate evaluator (new, model-free) | **PASS 9/9** |
| 648-clip audit (conditions, provenance, licences, SNR) | **PASS** — 17 conditions, 560 target / 88 control, `data/condition_manifest.csv`, `data/audio_provenance.csv` |
| Per-condition 95 % bootstrap CIs | **PASS** — `data/baseline_ci.csv`, 56 arm×condition rows |
| Confidence-gate sweep on saved V3 output | **PASS (negative result)** — 0.7 loses 14 correct cards, 0.8 loses 33; **0 wrong removed at every threshold** |
| Source/experiment provenance record | **PASS** — `BEFORE-AFTER.md` |

## 2. NOT_RUN — every acoustic arm, with the exact blocker

| Arm | Status | Blocker |
|---|---|---|
| B0 single-mic baseline re-run | **NOT_RUN** | disk < 4 GiB; baseline reported from frozen transcripts, not re-run |
| B1 close-mic | **NOT_RUN** | no lawfully recorded close-mic audio |
| B2 two-mic | **NOT_RUN** | no simultaneously recorded 2-channel audio; synthetic duplication explicitly refused |
| B3 overlap/foreground detector | **NOT_RUN (evaluator only)** | no audio feature pass under the floor; gate evaluator shipped and measured on saved data |
| B4 separation / enrolment | **NOT_RUN** | no licensed separator, no consented enrolment audio, no disk headroom |
| B5 streaming layer | **NOT_RUN** | model-free commit engine exists; no model streaming inference permitted here |

## 3. BLOCKED

| Item | Reason |
|---|---|
| Church WER | `BLOCKED_GOLD` — no consented human-annotated speaker-labelled corpus |
| Physical card visibility | `NOT_MEASURED` — no supervised GUI session; installed app is not V3/V4 |
| 6 % target | aspirational; requires multi-mic/separation **and** in-domain adaptation |
| Disk headroom for experiments | 1.7 GiB free; needs owner cleanup/external drive (see `DISK_RECOVERY_CANDIDATES.md`) |

## 4. Deliverables

`NEXT_SPEAKER_STUDY.md` (B0–B5 design, exit criteria, manifest schema, milestones) ·
`DISK_RECOVERY_CANDIDATES.md` (read-only inventory, no deletions) · `scripts/target_gate.py` + tests ·
`data/{condition_manifest,audio_provenance,baseline_ci,gate_sweep_648,disk_candidates}.csv` ·
`BEFORE-AFTER.md` · `SHA256SUMS.txt` · `GIT_PUSH.txt`.

## 5. Next action

Owner decision on cleanup is the single unblocker for acoustic work; the scientific next step after that is
**B1/B2 capture** (close mic + simultaneous room mic), because every measured result says the residual error is
competing-speaker energy, not streaming.
