# RESULTS_NEXT — scorer audit, speaker overlap, lyrics, replication

**Date:** 2026-11-11 · **Base commit:** `c8ad92b…` · **Branch:** `rhemaflow/research-chat3/scorer-speaker-lyrics-20261111`
**Disk:** 2.1 GiB free (< 3 GiB) → **no model runs, no encodes, no new corpora**; scripts and saved transcripts only.
**Verdict: `RESEARCH_GO` / `PRODUCTION_NO_GO`.**

## 1. WER scorer — defect confirmed, fixed, tests, provenance

* **Defect:** v1's `re.split(r"[^a-z0-9' ]+", s)` kept spaces inside tokens → `for god so loved the world` = 1 token.
* **Impact:** ref words 89 instead of 487, WER 13.48 % instead of 1.85 % on the same Opus transcripts.
* **Not used for published metrics:** the 648-clip numbers came from `analyse_matrix.py` (correct tokeniser) and
  reproduce **exactly** with the new scorer: Q4 26.306 %, Tiny.en 44.789 %, Qwen 24.387 %, V3 26.306 %,
  n=560, 15,008 reference words. Opus numbers reproduce exactly (1.848 / 3.285 / 3.696 %).
* **v2 adds:** explicit ids or validated manifest mapping (no filename slicing), composite `case_id,condition`
  keys, duplicate/missing/truncated fail-closed, empty-reference exclusion with false-speech reporting,
  conflict detection, normalised vs verbatim modes, coverage and S/D/I in the output.
* **Tests:** 20/20 pass, including S+D+I versus an independent two-row DP on 200 random pairs.
* **Verdicts:** `PASS` (fix + tests), old metrics `VALID` (provenance reproduced), v1 tool `INVALID`.

## 2. Speaker overlap — negative result, no gate added

Current gate: **0 wrong cards in 648 clips**; interference costs **missed cards**. Oracle abstention on
overlap ≤ 0 dB loses 11 correct cards and removes 0 wrong; chatter ≤ 0 dB loses 27; all hard cells lose 41.
Confidence 0.8 loses 7 % of correct cards and removes none. Diarisation and enrolment are **NOT_AVAILABLE**;
mic routing **NOT_TESTED** (single channel). **No source change.**

## 3. Sung lyrics — `SUNG_AUDIO_NOT_RUN`

The 100/95/75 % figures are **KJV text substitution tests**, not songs. No lawful sung audio exists. Operator-first
workflow documented; real claims require consented sung fixtures + licensed lyrics.

## 4. Compression and restore replication

* Codec findings re-verified from saved transcripts: Opus 16–24 kbps transparent for clean speech; +0.41 pp for
  speech-under-music at 24 kbps; recommend 16–20 kbps speech archives, ≥ 32 kbps (normally 48–96) for music.
* Restore contract extended to **15/15** synthetic cases (versioning, stale keys, crash/resume, tampered manifest).
  Synthetic success ≠ production reliability; no 99.999 % claim.

## 5. Statuses

| Item | Status |
|---|---|
| Scorer defect repaired and tested | **PASS** |
| Published 648-clip metrics | **VALID** (reproduced exactly) |
| Speaker-overlap gate improvement | **NONE FOUND** (negative result) |
| Sung-lyrics evaluation | **SUNG_AUDIO_NOT_RUN** |
| Church accuracy | **BLOCKED_GOLD** |
| `card_visible` | **NOT_MEASURED** |
| Production | **PRODUCTION_NO_GO** |

## 6. Commands

```bash
python3 research/chat3/tests/test_wer.py -v
python3 research/chat3/scripts/wer.py --gold gold.csv --jsonl out.jsonl --key case_id,condition --json
python3 research/chat3/scripts/cloud_contract_test.py
python3 research/chat3/scripts/lyrics_match.py
```
