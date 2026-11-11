# BASELINE_AND_ABLATIONS — frozen matrix, confidence intervals, what could not run

## 0. Method and provenance

* Frozen corpus: 648 clips, 560 target-speech, 88 no-target controls; 15,008 reference words (target clips).
* Transcripts: saved raw JSONL from the 2026-11-10 run (Q4 `4853f965…`, Tiny.en `921e4cf8…`, Qwen MLX
  `05b7fbea…`); **no model was re-run this round** (disk 672 MiB, hard floor 4 GiB).
* Scorer: `scripts/wer.py` v2 (validated, 20 tests; reproduces the published matrix exactly).
* Confidence intervals: 1,000-replica bootstrap over clips within each condition (seed 20261111), 95% percentile.

## 1. Baseline with 95% CIs

| Arm | Condition | n | ref words | WER % | 95% CI |
|---|---|---:|---:|---:|---|
| B0_Q4 | chatter_0 | 40 | 1072 | 26.586 | 21.56–31.49 |
| B0_Q4 | chatter_m5 | 40 | 1072 | 79.571 | 75.48–83.23 |
| B0_Q4 | chatter_p10 | 40 | 1072 | 2.612 | 1.47–4.0 |
| B0_Q4 | chatter_p5 | 40 | 1072 | 3.358 | 1.97–4.88 |
| B0_Q4 | clean | 40 | 1072 | 1.586 | 0.78–2.63 |
| B0_Q4 | mixed_0 | 40 | 1072 | 66.884 | 60.31–72.97 |
| B0_Q4 | music_0 | 40 | 1072 | 2.612 | 1.29–4.19 |
| B0_Q4 | music_m5 | 40 | 1072 | 4.011 | 2.34–6.4 |
| B0_Q4 | music_p10 | 40 | 1072 | 1.866 | 1.01–2.99 |
| B0_Q4 | music_p5 | 40 | 1072 | 2.239 | 1.16–3.44 |
| B0_Q4 | overlap_0 | 40 | 1072 | 68.19 | 61.71–74.11 |
| B0_Q4 | overlap_m5 | 40 | 1072 | 93.284 | 91.54–94.9 |
| B0_Q4 | overlap_p10 | 40 | 1072 | 2.799 | 1.64–4.27 |
| B0_Q4 | overlap_p5 | 40 | 1072 | 12.687 | 7.2–21.23 |
| B0_Q4 | chatter_0 | 40 | 1072 | 21.642 | 11.86–33.6 |
| B0_Q4 | chatter_m5 | 40 | 1072 | 82.276 | 75.44–88.12 |
| B0_Q4 | chatter_p10 | 40 | 1072 | 2.892 | 1.61–4.53 |
| B0_Q4 | chatter_p5 | 40 | 1072 | 3.451 | 1.97–5.27 |
| B0_Q4 | clean | 40 | 1072 | 1.586 | 0.52–3.1 |
| B0_Q4 | mixed_0 | 40 | 1072 | 80.877 | 74.97–86.06 |
| B0_Q4 | music_0 | 40 | 1072 | 2.332 | 1.25–3.62 |
| B0_Q4 | music_m5 | 40 | 1072 | 2.519 | 1.36–3.89 |
| B0_Q4 | music_p10 | 40 | 1072 | 1.866 | 0.9–3.11 |
| B0_Q4 | music_p5 | 40 | 1072 | 1.679 | 0.88–2.65 |
| B0_Q4 | overlap_0 | 40 | 1072 | 38.713 | 28.97–48.56 |
| B0_Q4 | overlap_m5 | 40 | 1072 | 93.47 | 91.84–95.01 |
| B0_Q4 | overlap_p10 | 40 | 1072 | 3.265 | 1.89–5.09 |
| B0_Q4 | overlap_p5 | 40 | 1072 | 4.851 | 3.11–6.94 |

Full table for all four arms: `data/baseline_ci.csv`.

**Reading:** clean is 1.586 [0.78–2.63]; music stays within 4.01 at −5 dB; chatter/overlap at 0 and −5 dB
dominate the aggregate. CIs are wide because n=40 clips per condition — a 40-verse pilot cannot prove small
differences.

## 2. Aggregate (560 clips, 15,008 words)

| Arm | WER |
|---|---:|
| Qwen 1.7B MLX | 24.387 % |
| Q4 | 26.306 % |
| V3-20s (research pipeline) | 26.306 % |
| Tiny.en | 44.789 % |

## 3. Ablations requested — status

| Ablation | Status | Exact blocker |
|---|---|---|
| A. Qwen base full-context (MLX) | **NOT_RUN** | 672 MiB free; model is real (1.4 GB) but runs need temp space above the 4 GiB floor |
| B. Qwen pseudo-streaming (160/320/640/1000 ms, U=0/1/2) | **NOT_RUN (logic only)** | commit engine implemented and tested; no model decodes under the floor |
| C. Q4 buffered windows (5/10/20 s) | **NOT_RUN** | needs window corpus + alignment (~2–3 GB temp) |
| Close pastor mic vs room mic | **NOT_AVAILABLE** | no two-channel recording exists; a mono mix cannot stand in |
| Target-speaker enrolment | **NOT_AVAILABLE** | no embedding model, no consented enrolment audio |
| Diarisation | **NOT_AVAILABLE** | `transcribe-cli --diarize` is moss/granite-only; Parakeet returns one segment |
| Speech separation / beamforming | **NOT_RUN** | no licensed separator, no space, no training data |
| Confidence abstention | **MEASURED — rejected** | keeps 340/365 correct (7 % loss), removes 0 wrong |
| Oracle overlap abstention | **MEASURED — negative** | loses 11 correct cards, removes 0 wrong |

## 4. Paired comparisons available from saved data

* Qwen vs Q4, overlap 0 dB: 38.71 % vs 68.19 % (Qwen better by 29.5 pp).
* Qwen vs Q4, triple mix 0 dB: 80.88 % vs 66.88 % (Qwen worse by 14.0 pp).
* V3 vs Q4: identical committed text on all 560 clips (0.000 pp).
* Cards (V3): 345 correct / 0 wrong / 100 review / 203 none; music-only and silence produce 0 cards.

These are paired by construction (same clips), but **not** independent human gold; no church-WER claim is made.
