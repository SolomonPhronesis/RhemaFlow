# RESULTS — R2T2-inspired independent streaming, Qwen/Q4, and the realistic path to 6 %

**Date:** 2026-11-11 · **Branch:** `rhemaflow/research-chat3/r2t2-independent-streaming-20261111`
**Disk:** 672 MiB free at start (hard floor 4 GiB) → **no model runs, no builds, no 648-clip rerun**.
**Verdicts: `PUSH_VERIFIED` (see GIT_PUSH.txt) · `RESEARCH_GO` · `PRODUCTION_NO_GO`.**

## 1. What was delivered

| Deliverable | Content |
|---|---|
| `R2T2_CODE_AUDIT.md` | upstream HEAD `72b81be7…`, seven files blob-verified, algorithm, licence §3.4(c), feasibility |
| `STREAMING_PROTOTYPE_DESIGN.md` + `scripts/stable_prefix.py` | model-free stable-prefix engine, sidecar validator, card de-duplicator — **20/20 tests** |
| `BASELINE_AND_ABLATIONS.md` | frozen 560-clip baseline with 95 % bootstrap CIs; every requested ablation marked `NOT_RUN`/`NOT_AVAILABLE` with the exact blocker |
| `ROADMAP_TO_6_PERCENT.md` | error decomposition and why streaming cannot reach 6 % |
| `BEFORE-AFTER.md`, `data/*.csv` | change list, feasibility matrix, test matrix, CIs |

## 2. Key findings

1. **R2T2's gain is trained, not architectural.** The repo has no training code (48 files, none for LSP/SFT/GRPO);
   README describes 1,500 h LSP training with a frozen encoder. Calling `streaming_transcribe` on base Qwen is not
   R2T2. Its weights are licence-restricted (§3.4(c)) and were not touched.
2. **5.76 % ≠ our noise result.** It is a 13-test-set English/Chinese macro average at 160 ms/U=1; our 560-clip
   mixed-noise WER is Q4 26.31 %, Qwen 24.39 %, Tiny 44.79 %.
3. **Streaming cannot fix competing speakers.** Qwen beats Q4 by 29.5 pp at overlap 0 dB and loses by 14 pp on the
   triple mix; the dominant errors are other-speaker words (96.4 % / 90.6 % at −5 dB).
4. **The commit engine is correct under adversarial input** (repeated words, partial words, silence, cutoff,
   speaker handoff, stale ids, malformed JSON, duplicate cards) — verified without any model.
5. **Reaching < 6 % requires new acoustic capture (multi-mic/separation) and in-domain adaptation**, not a streaming
   tweak. Current honest milestones: ≤26.3 % reached, ≤20 % not yet, ≤15 % blocked on data/hardware.

## 3. Status table

| Item | Status |
|---|---|
| R2T2 source audit (blob-verified) | **PASS** |
| Independent stable-prefix prototype + tests | **PASS (logic only, 20/20)** |
| Qwen / Q4 model re-runs | **NOT_RUN — disk 672 MiB** |
| 648-clip re-run | **NOT_RUN — disk** |
| Speaker ablations (2-mic, diarisation, separation) | **NOT_AVAILABLE / NOT_RUN** |
| Independent church gold | **BLOCKED_GOLD** |
| `card_visible` | **NOT_MEASURED** |
| Production | **PRODUCTION_NO_GO** |

## 4. Commands

```bash
python3 research/chat3/tests/test_streaming.py -v      # 20/20
python3 research/chat3/tests/test_wer.py -v            # 20/20
```
