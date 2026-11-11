# HANDOFF_CHAT3_FOR_CODEX — noisy-sermon / target-speaker isolation research

**Handoff date:** 2026-11-11 23:20–23:55 UTC · **From:** Chat 3 research session · **To:** new Codex Extra-High chat
**Status:** `RESEARCH_GO` · `BLOCKED_GOLD` (church accuracy) · `PRODUCTION_NO_GO`

---

## 1. Repository, worktree, branch and verified state

| Item | Value |
|---|---|
| Repository | `git@github.com:SolomonPhronesis/RhemaFlow.git` (public; verified via `git ls-remote`) |
| Research worktree | `/Users/solomonphronesis/Documents/deepseek-harness/default-workspace/chat3_scorer_wt` |
| Latest branch | `rhemaflow/research-chat3/real-speaker-validation-20261111` |
| **Verified HEAD = remote SHA** | **`2b35d064ac343411a2e37db1d072ba11d9c7bf4d`** |
| Research commit | `f609e8f1ec2604ffecf109fdb6181ddd328ebe89` |
| Base of that branch | `3f06d516342e8d0cc13633bf083f552b1f9e6c2c` |
| Worktree status at handoff | **clean** |
| Other worktrees | `Documents/RhemaFlow-Git` (main, `pwa-assessment`), `…/chat3_research_wt` (`opus-lyrics-noise-…`) — **do not touch** |

Ancestry (newest first): `2b35d06 → f609e8f → 3f06d51 → c80ae1d → 16c9952 → ddb36f1 → a8bde98 → 6a5fc92 →
c37d3dd → 8ba16ff → 0656784 → … → 5e31b98`.

Evidence ZIPs (workspace root, not Git):
`RhemaFlow_Chat3_Real_Speaker_Validation_20261111.zip` (latest) ·
`RhemaFlow_Chat3_Adaptive_FIR_Isolation_20261111.zip` ·
`RhemaFlow_Chat3_Causal_DualMic_Validation_20261111.zip` ·
`RhemaFlow_Chat3_PostRestart_Isolation_20261111.zip` ·
`RhemaFlow_Chat3_R2T2_Streaming_Research_20261111.zip` ·
`RhemaFlow_Chat3_Scorer_Speaker_Lyrics_20261111.zip` ·
`RhemaFlow_Chat3_Speaker_Isolation_Plan_20261111.zip`.

## 2. Source, data and provenance

Committed under `research/chat3/` (456 KB): 24 markdown reports, 13 scripts, 6 test files, 32 CSVs/JSON, 4 SVG charts,
`SHA256SUMS.txt`, `GIT_PUSH.txt`.

| Asset | Provenance | Licence / status | In Git? |
|---|---|---|---|
| 40 KJV WAVs + gold | owner-supplied `40_KJV_WAV_GOLD.zip`; TTS generated | KJV text public domain; research use | **no** (audio excluded) |
| Smartverse / Pewbeam recordings | owner-supplied demos | owner-approved research use | **no** |
| Synthetic 648-clip matrix | generated from the two above | derived research data | **no** (manifests + hashes only) |
| Synthetic two-channel sets | generated (`scripts/build_noise_matrix.py`, `build_twoch.py`, `causal_isolation.py`, `fir_isolation.py`) | derived | **no** |
| Parakeet v2 Q4_K_M | `~/Prosperous Projects/RF-Personal-0936/v2models/…Q4_K_M.gguf`, SHA `4853f965…` | cc-by-4.0 (model card) | **no** |
| Qwen3-ASR 1.7B MLX embed8 | `…/RF-H/out/…/qwen3-asr-1.7b-en16k-4bit-embed8` | Apache-2.0 code; checkpoint terms | **no** |
| Whisper tiny.en | `~/.rhemaflow-models/ggml-tiny.en.bin`, SHA `921e4cf8…` | MIT | **no** |
| R2T2 | upstream code only, never downloaded | code Apache-2.0; **weights NetEase, §3.4(c) restricts commercial improvement** | **no** |
| Real church gold | **does not exist** | — | — |

Unavailable: consented dual-mic church recordings, human target transcripts, diarisation/embedding model, sung
lyrics fixtures.

## 3. Reproduction commands

All paths are inside the worktree; run from `chat3_scorer_wt/research/chat3`.

```bash
# scorer + algorithm tests (no models, no audio): 66 tests
for t in tests/test_*.py; do python3 "$t"; done

# frozen 648-clip matrix (needs 40 KJV WAVs + owner sources; ~150 MB disk)
RF_BASE=/path/to/workspace python3 scripts/build_noise_matrix.py

# Q4 / Qwen / V3 / V4 on the matrix (needs transcribe-cli + Q4 + adapter; ~20 min)
RF_CHAT3_NEXT_20261110/rust/target/release/rf-bench b0 --compute metal --cli <CLI> --model <Q4> \
  --fixtures matrix_work/out/data/matrix_fixtures.csv --out raw/b0.jsonl

# scorer over saved transcripts
python3 scripts/wer.py --gold <gold.csv> --jsonl <raw.jsonl> --key case_id,condition \
  --exclude-conditions music_only,chatter_only,silence --json

# two-channel causal + FIR experiments (synthetic; CPU only)
python3 scripts/causal_isolation.py
python3 scripts/fir_isolation.py     # frozen splits + tune grid
python3 scripts/score_fir.py         # holdout WER/CIs/cards

# Opus/MP3 round-trip
bash scripts/opus_eval.sh <fixture_dir> <transcribe-cli> <model.gguf>

# pseudo-streaming with Qwen (needs the owner's sidecar)
python3 scripts/pseudo_stream.py
```

Limits: ≥8 GiB free for matrix ASR sweeps, ≥15 GiB for extended runs; ≤4 GiB swap; Qwen needs ~1.8 GB RSS.
No model downloads are authorised in this handoff.

## 4. Protocol map (every experiment)

| Experiment | Target/interferer | Channels | Causal? | n | Split | Metric | CI |
|---|---|---|---|---|---|---:|---|
| 648-clip noise matrix | TIR 0/−5 dB (target vs music/chatter/preacher), 13 conditions | single | n/a | 648 (560 target, 15,008 words) | none (frozen) | corpus WER = Σ(S+D+I)/ΣN; cards | bootstrap per condition |
| Opus/MP3 | clean + music-0 dB | single | n/a | 20 + 20 | none | WER after decode | — |
| Pause factorial | 500/650/800 ms at 45 %; 600 ms at 30/65 % | single | n/a | 128 + 80 | tune/held-out positions | WER + card p95 | — |
| Idealised 2-channel oracle | TIR 0/−5 dB | 2 (close/room, known mix) | **no (future samples)** | 160 | none | WER, SIR, cards | — |
| Causal scalar NLMS | TIR 0/−5 dB, no reverb | 2 | **yes** | 160 | none | WER + cards | paired bootstrap |
| Realistic FIR | TIR 0/−5 dB, 120–200 ms reverb, motion, drift | 2 | **yes** | 40 holdout (1,128 words) | train 01–20 / tune 21–30 / **holdout 31–40** | WER, ΔSIR, retention | paired bootstrap 2,000 |
| Delay-tracking FIR | same | 2 | **yes** | 60 tune runs | tune only | ΔSIR | — |
| Pseudo-streaming | clean | 1 | heuristic | 4 clips × 2 chunks | none | commit revisions, WER | — |
| Cloud contract | none | — | — | 15 synthetic cases | — | pass/fail | — |
| Lyrics match (text only) | none | — | — | 40 lines | holdout negatives | top-1 | — |

WER definition everywhere: word-level Levenshtein on normalised tokens (lowercase, punctuation→space, apostrophes
kept), `WER = (S+D+I)/N`; empty-reference clips excluded and reported separately; scorer v2 with explicit ids and
100 % coverage checks (`SCORER_AUDIT.md`).

## 5. Evidence classification — what may be claimed

| Class | Results | Claim allowed |
|---|---|---|
| `REAL_CHURCH` | **none** | nothing |
| `SYNTHETIC_CAUSAL` | scalar 41.223 % (realistic, holdout), 2.822 % (idealised), FIR 51.862 %, FIR+DT 54.610 % | “in a synthetic two-channel simulation with these acoustics…” |
| `SYNTHETIC_ORACLE` | 2.542 % (non-causal, known interferer) | ceiling only, **never** a product claim |
| `MODEL_FREE` | stable-prefix 20 tests, cloud contract 15/15, lyrics text-only 100/95/75 %, scorer 20 tests | mechanism claims only |
| `NOT_RUN` | Qwen on processed audio, PBFDAF, sung lyrics, real dual-mic, `card_visible` | must stay `NOT_RUN` |
| `BLOCKED_GOLD` | church WER | no number exists |

Never mix these classes in one table without the label; never quote R2T2's 5.76 % as our noise result.

## 6. CTRL03 forensic case (hard safety target)

* Clip `CTRL03`, condition chatter-only (no target), processed by the 32-tap FIR.
* ASR transcribed the **other preacher** quoting Luke 1:17; matcher correctly returned `QUOTE Luke 1:17`,
  confidence **0.833**. 418 words total on 28 no-target clips.
* Failure stage: **speaker attribution**, not parsing. Full detail: `FORENSIC_WRONG_CARD.md`.
* Negative guard experiments: close/room energy ratio ranges overlap (holdout −5.83…−2.03 dB vs control
  −6.01…−6.02 dB); output/room coherence failed (ρ mean −0.055). No guard added — suppressing all cards is not a fix.
* **Zero wrong cards is a hard gate and is NOT achieved** by the proposed front-end.

## 7. R2T2 audit and non-transfer

* Upstream HEAD `72b81be7070095410b75ed2e11998e347f655218`; 7 files blob-verified (`r2t2_asr.py` `9967217b…`,
  `MODEL_LICENSE` `7fbd11c1…`, `LICENSE` Apache-2.0).
* No training code in the repo (48 files); the published gain needs LSP/SFT/GRPO weights that are not available.
* `MODEL_LICENSE` §3.4(c): no use of R2T2 or derivatives to improve other commercial AI models — **no weights, no
  outputs, no distillation**.
* 5.76 % is the 160 ms/U=1 macro average over 13 English/Chinese test sets (base 21.01 %, full-context 5.15 %).
* Independent stable-prefix engine: `scripts/stable_prefix.py`, **20/20 tests**, past-only proofs — model-free only.

## 8. Roadmap (priority order)

1. **Real preacher lapel mic, close-only baseline** — the simple operator baseline; measure target WER.
2. **Simultaneous room mic**, same clock, sync pulse, per-session delay calibration.
3. **Human annotation** (two annotators, adjudication, span labels) and frozen speaker-disjoint splits.
4. **Multi-channel causal separation**: partitioned frequency-domain adaptive filter (PBFDAF), double-talk robust
   control, target-preservation checks. Delay tracking as implemented was negative (`FILTER_ADVANCE.md`).
5. Keep the baseline even if enhancement fails; enhancement ships only with a measured win.
6. Sung lyrics: only with authorised fixtures and lyrics; operator/manual selection stays.

## 9. Decision gates

* ≥ **5 pp paired target-WER improvement on independent real audio** vs close-only.
* **No additional wrong cards**; no more than 5 % loss of correct cards.
* Realistic latency measured end-to-end (not just block size); `card_visible` only if observed.
* Independent church gold; `<6 %` only if proven on a frozen genuine corpus.
* Until then: `PRODUCTION_NO_GO`.

## 10. Next Codex work order

1. Verify remote SHA and this handoff (read-only).
2. Run the 66 model-free tests; confirm green.
3. Rebuild the synthetic realistic corpus and confirm the holdout numbers (41.2 % scalar, 51.9 % FIR).
4. Implement **PBFDAF** (4–16 partitions, FFT 256–512) with a double-talk gate; tune on the tune split only.
5. Re-run the no-target controls through the new filter; the gate is **0 wrong cards**.
6. If disk/time allow, add Qwen as a second ASR arm on the same processed holdout.
7. When real recordings arrive: run the operator checklist, then the same pipeline on real holdout.

Operator acquisition checklist (≥3 sessions): same-clock dual capture, lapel 15–20 cm, room mic 3–6 m, 48 kHz raw
WAV, clap slate, gain log, written consent, two annotators + adjudication, hashed manifests, speaker-disjoint
splits. Full detail: `OPERATOR_KIT.md`.

## 11. Reproduction manifest, hashes, blockers

* `SHA256SUMS.txt` in this directory covers every committed research artifact.
* `GIT_PUSH.txt` records the verified branch/commit/remote SHA chain.
* Blockers: `BLOCKED_GOLD` (real church corpus), `NOT_MEASURED` (`card_visible`), `NOT_IMPLEMENTED` (PBFDAF),
  `NOT_RUN` (Qwen-on-processed, sung lyrics).
* No raw audio, model weights, lyrics, names, credentials or binaries are committed.
