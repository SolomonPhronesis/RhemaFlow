# RESULTS — post-restart speaker isolation (synthetic, model-free)

**Date:** 2026-11-11 17:07–17:55 UTC · **Restart:** **confirmed** (`uptime` 9 min, boot 17:10:03)
**Disk:** 18 GiB after restart · **Swap:** reset to 0 at boot
**Verdict: `RESEARCH_GO` / `PRODUCTION_NO_GO`.**

## 1. Gate and scope

The machine restarted at 17:10 and disk rose from 3.9 GiB to **18 GiB**, opening the ≥8 GiB gate. This round
therefore has two parts: the synthetic signal-level study written pre-restart, and **real post-restart model
runs** on the frozen 648-clip matrix plus an end-to-end synthetic two-channel experiment.

## 1b. Phase 1 — real post-restart baseline (frozen 648 clips, 560 target, 15,008 words)

| Arm | S | D | I | WER |
|---|---:|---:|---:|---:|
| B0 Parakeet Q4 Metal | 1,988 | 1,862 | 98 | **26.306 %** |
| Qwen3-ASR 1.7B MLX | 2,526 | 1,017 | 117 | **24.387 %** |
| V3-20s pause 900 | 1,983 | 1,867 | 98 | **26.306 %** |
| V4-20s review-only | 1,983 | 1,867 | 98 | **26.306 %** |

Exactly reproduces the pre-restart numbers — the corrected scorer and matrix are stable across a reboot.
Cards (V3/V4): 345 QUOTE, 100 REVIEW, 203 NO_CARD; card p50 **222.5 ms**, p95 **304.7 ms** (V3), p95 321.3 ms (V4,
70 verifier calls). Decode p50: Q4 122.5 ms, Qwen 455 ms, V3 560.9 ms.

## 1c. Phase 2 — end-to-end synthetic two-channel isolation

160 mixtures, 4,288 words; real Q4 ASR on close-mic vs isolated channel:

| Condition | close WER | isolated WER | Δ |
|---|---:|---:|---:|
| chatter −5 dB | 78.36 % | **2.15 %** | −76.2 pp |
| chatter 0 dB | 26.59 % | **2.61 %** | −24.0 pp |
| second preacher −5 dB | 93.00 % | **2.43 %** | −90.6 pp |
| second preacher 0 dB | 68.19 % | **2.99 %** | −65.2 pp |
| **aggregate** | **66.54 %** | **2.54 %** | **−64.0 pp** |

V3 card stage on the isolated channel: **136/136 QUOTE correct, 0 wrong** — clean-level card recall restored.
Labelled `SYNTHETIC_2CH_SIMULATION`: non-causal least-squares cancellation, no reverb/room noise, known interferer.
It shows the 6 % barrier is a **capture** problem, not a model-size problem; it is not a church result.

## 2. PASS

| Item | Result |
|---|---|
| Preflight (disk, APFS, swap, git, remote, processes, models) | **PASS** — remote verified, HEAD `02ec12f…`, models present, no stray model/build processes |
| Reboot verification | **PASS** — machine was not rebooted (reported as such, not assumed) |
| Two-channel simulation harness + tests | **PASS** — 6/6 tests |
| Real post-restart baseline (Q4/Qwen/V3/V4, 648 clips) | **PASS** — exact reproduction |
| Synthetic two-channel end-to-end (real ASR) | **PASS** — 66.54 % → 2.54 % aggregate |
| Full model-free suite | **PASS 55/55** (scorer 20, streaming 20, gate 9, two-channel 6) |
| Synthetic isolation measurement | **PASS** — ΔSIR +11.9 to +22.6 dB; target retention −2.5 to −3.1 dB; 5–7 % frames with >6 dB target loss; overlap AUC 0.956–0.999 |

## 2b. Phase 3 — heuristic pseudo-streaming with real Qwen (R2T2-inspired, licence-safe)

4 clean clips × 2 chunk sizes, cumulative audio fed to the real Qwen 1.7B MLX sidecar, committed through the
independent stable-prefix engine (holdback 1, lookahead 1):

| chunk | updates/clip | first commit | committed vs full-context edits | WER vs gold | decode p50 |
|---|---:|---:|---:|---:|---:|
| 640 ms | 4–13 | 1.28–1.92 s | **0** | 0.0 % | 296–561 ms |
| 1000 ms | 3–9 | 2.00 s | **0** | 0.0 % | 281–522 ms |

Committed text never required revision, and matched full-context output exactly on these clips. This is a
**heuristic** pseudo-stream (re-decoding cumulative audio), not R2T2, not LSP, not vLLM, not 160 ms.

## 3. NOT_RUN / NOT_AVAILABLE

| Item | Status | Reason |
|---|---|---|
| Real close-mic / two-channel capture | **NOT_AVAILABLE** | no such recordings exist; synthetic duplication refused |
| ASR WER after cancellation | **PASS (synthetic)** — 2.54 % aggregate; real two-channel capture still `NOT_AVAILABLE` |
| Q4 / Qwen / V3 / V4 model runs | **PASS** — full 648-clip matrix re-run post-restart |
| Heuristic pseudo-streaming (Qwen, cumulative audio) | **PASS** — 8 runs, 0 revisions, 0 edits vs full-context |
| Card recall after isolation | **NOT_RUN** | needs ASR + matcher |
| Church WER | **BLOCKED_GOLD** | no consented human-annotated corpus |
| `card_visible` | **NOT_MEASURED** | no supervised GUI session |

## 4. What the synthetic result implies

A real two-channel capture is the only studied intervention with an effect large enough to matter
(+12–23 dB SIR). It also demonstrates the risk: naive least-squares cancellation costs ~3 dB of target and loses
5–7 % of frames. Any real implementation must be adaptive/causal and must be scored on target WER **and** card
recall, not on SIR alone.

## 5. Next action

1. Owner: free disk to ≥ 8 GiB (generated Chat 3 audio 377 MiB; larger gains require owner data decisions).
2. Record 10+ sessions with a close mic **and** a simultaneous room mic, consented.
3. Run B1/B2 with the existing frozen scorer and card metrics.
4. Only then evaluate separation/diarisation models.

## 6. Reproduction

```bash
python3 research/chat3/scripts/two_channel_sim.py "$PWD"     # writes data/two_channel_sim.csv
python3 research/chat3/tests/test_two_channel_sim.py -v      # 6/6
```
