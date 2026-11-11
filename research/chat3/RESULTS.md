# RESULTS — post-restart speaker isolation (synthetic, model-free)

**Date:** 2026-11-11 17:07–17:40 UTC · **Disk:** 3.9 GiB free (below the 4 GiB floor) · **Swap:** 8.97 GiB
**Reboot check:** **NOT rebooted** — `uptime` 6 days 10 h, boot 2026-11-05 06:55.
**Verdict: `RESEARCH_GO` / `PRODUCTION_NO_GO`.**

## 1. Gate and scope

At 3.9 GiB the brief allows read-only inventory and light pure-Python evaluation only. No model runs, no corpus
generation, no builds. This round therefore delivers a **synthetic two-channel simulation** (known components),
model-free tests and documentation — clearly labelled `SYNTHETIC_SIMULATION`.

## 2. PASS

| Item | Result |
|---|---|
| Preflight (disk, APFS, swap, git, remote, processes, models) | **PASS** — remote verified, HEAD `02ec12f…`, models present, no stray model/build processes |
| Reboot verification | **PASS** — machine was not rebooted (reported as such, not assumed) |
| Two-channel simulation harness + tests | **PASS** — 6/6 tests |
| Full model-free suite | **PASS 55/55** (scorer 20, streaming 20, gate 9, two-channel 6) |
| Synthetic isolation measurement | **PASS** — ΔSIR +11.9 to +22.6 dB; target retention −2.5 to −3.1 dB; 5–7 % frames with >6 dB target loss; overlap AUC 0.956–0.999 |

## 3. NOT_RUN / NOT_AVAILABLE

| Item | Status | Reason |
|---|---|---|
| Real close-mic / two-channel capture | **NOT_AVAILABLE** | no such recordings exist; synthetic duplication refused |
| ASR WER after cancellation | **NOT_RUN** | disk < 4 GiB; audio-level SIR is not WER |
| Q4 / Qwen / Tiny model runs | **NOT_RUN** | disk gate |
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
