# Chat 3 research — music/chatter, Opus export, lyrics matching, cloud contract

**Date:** 2026-11-11 · **Machine:** M1 Pro, 16 GB · **Disk at run time:** 3.3 GiB free, 8.0 GiB swap
**Scope:** research only. No install, release, merge, model replacement or settings change.
**Verdict: `RESEARCH_GO` / `PRODUCTION_NO_GO`.**

---

## 0. What this commit contains, and what it deliberately does not

Committed: harness scripts, test definitions, aggregated CSV/MD reports, frozen small text fixtures (public-domain
KJV verses), SHA-256 manifest. **Not committed:** audio, model weights, raw per-clip transcripts, names, lyrics,
keys, binaries, or anything from the User/Personal chats.

Disk rule applied: below 3.3 GiB free this round ran **light scripts and small batch decodes only** (no 648-clip
model sweeps, no new corpora, no builds).

## 1. Frozen noise matrix (measured 2026-11-10, reused here)

648 clips: clean 40 · music at −5/0/+5/+10 dB 160 · chatter at those SNRs 160 · competing preacher 160 · triple
mix 40 · music-only 40 / chatter-only 40 / silence 8. SNR is **target relative to interference**.

| Arm | WER (560 target clips) | cards correct | cards wrong | false words on no-target |
|---|---:|---:|---:|---:|
| Parakeet v2 Q4 (Metal) | 26.31 % | n/a | n/a | 804 |
| Whisper tiny.en | 44.79 % | n/a | n/a | 975 |
| Qwen3-ASR 1.7B MLX (standalone) | 24.39 % | n/a | n/a | 839 |
| V3-20s research pipeline | 26.31 % | **345** | **0** | 842 |

Music is comparatively benign (≤4.01 % WER for Q4/V3/Qwen down to −5 dB); competing speakers dominate the error
(26.6–93.3 % at ≤0 dB). Tiny.en is not a viable noisy-audio fallback (29–99 % in interference).
**Independent human church gold remains `BLOCKED_GOLD`; no church-accuracy claim is made.**

## 2. Opus / MP3 export evaluation

Speech: 20 clean KJV clips (160 s total). Music: 30 s owner-approved music bed. Mixed: 20 clips with music at 0 dB
SNR. Round-trip quality proxy = **ASR WER of the decoded file against the original transcript** (a codec that
destroys speech raises WER). Subjective listening is **NOT_MEASURED**.

| Export | effective kbps | MB / 2 h (extrapolated) | ASR WER after round-trip |
|---|---:|---:|---:|
| PCM 16-bit 16 kHz (reference) | 221.8 | 199.6 | 1.85 % |
| Opus 16 kbps | 14.6 | **13.1** | 1.85 % |
| Opus 20 kbps | 18.0 | 16.2 | 1.85 % |
| Opus 24 kbps | 21.5 | 19.4 | 1.85 % |
| MP3 64 kbps | 56.5 | 50.8 | 1.85 % |
| music Opus 48 kbps | 48.7 | 43.8 | n/a (no target speech) |
| music Opus 64 kbps | 64.7 | 58.3 | n/a |
| music Opus 96 kbps | 96.7 | 87.1 | n/a |
| music MP3 96 kbps | 96.5 | 86.8 | n/a |
| music PCM (reference) | 256.0 | 230.4 | n/a |

**Mixed music-0 dB clips:** PCM 3.29 %, MP3 64 kbps 3.29 %, Opus 24 kbps **3.70 %** — a +0.41 pp penalty, i.e.
Opus at 24 kbps is transparent for clean speech but not quite for speech-under-music.

**Conclusions:** Opus 16–24 kbps is 10–15× smaller than PCM with **no measurable ASR loss on clean speech**; for
speech-under-music, 24 kbps costs ~0.4 pp and should be raised (≥32 kbps) if the service records worship sets.
All 2-hour figures are **extrapolated** from 160 s / 30 s measurements and labelled as such.

## 3. Lyrics / song identification (public-domain text only)

40 KJV verses used as stand-in lyric lines; 4-gram fingerprint index; queries corrupted by random word
substitutions. No scraping, no copyrighted lyrics.

| Query set | n | top-1 correct | accuracy |
|---|---:|---:|---:|
| exact | 40 | 40 | 100 % |
| 10 % word errors | 40 | 38 | 95 % |
| 25 % word errors | 40 | 30 | 75 % |
| unseen lines (negative control) | 2 | 2 rejected | 100 % |

Song ID from authorised lyrics is therefore workable at moderate lyric noise; the **operator fallback** (manual
selection) must remain because 25 % corruption already loses one in four matches. Lyrics-following with real sung
audio is **NOT_RUN** — no authorised sung recording exists in this workspace.

## 4. RhemaCloud manifest / checksum / redundant-restore contract

Synthetic ciphertext (random 64 KiB chunks), three simulated replicas (`eu-r2`, `fi-hetzner`, `aws-archive`), no
network and no credentials. Nine injected-failure cases, **9/9 pass**:

| Case | Expected | Result |
|---|---|---|
| clean restore | ok | ok |
| one replica corrupted | restore from peer | ok |
| one replica missing | restore from peer | ok |
| chunk lost in all replicas | fail closed | failed with explicit error |
| single good replica left | ok | ok |
| wrong pinned manifest hash | fail closed | manifest mismatch |
| manifest tampered on disk | fail closed | manifest mismatch |
| manifest restored | ok | ok |
| truncated chunk | fall back to peer | ok |

The contract (pin the manifest hash, verify every chunk checksum before use, prefer a peer replica, fail closed)
is testable offline and should be the minimum bar before any real provider is connected. **No provider credentials
were used and no audio left the machine.**

## 5. Status of the release gates

| Gate | Status |
|---|---|
| Independent human church gold | **BLOCKED_GOLD** |
| Physical card visibility (`card_visible`) | **NOT_MEASURED** |
| Subjective codec listening test | **NOT_MEASURED** |
| Sung-lyrics following | **NOT_RUN** (no authorised sung audio) |
| R2T2 comparison | **NOT_RUN** (licence §3.4(c)); its 5.76 % is a 13-dataset bilingual 160 ms average, not noise WER |
| Production install / merge | **NO-GO** |

## 6. Reproduction

```bash
python3 research/chat3/scripts/lyrics_match.py          # writes out/lyrics_match.json
python3 research/chat3/scripts/cloud_contract_test.py   # writes out/cloud_contract.json
bash research/chat3/scripts/opus_eval.sh <fixture_dir> <transcribe-cli> <model.gguf>
```

`data/*.csv` are the aggregated results of this run; every number above is regenerated by those scripts.
