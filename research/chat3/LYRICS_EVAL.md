# LYRICS_EVAL — song ID and lyrics-following readiness

## Status: `SUNG_AUDIO_NOT_RUN`

**No lawful sung fixture exists in this workspace.** The previous 100 / 95 / 75 % top-1 results were **text
substitution tests on public-domain KJV verses**, not songs and not sung audio. They must never be quoted as
sung-lyrics accuracy. No lyrics were scraped and no worship recordings were uploaded.

## What was actually tested (text only, public-domain KJV)

| Query set | n | top-1 | accuracy |
|---|---:|---:|---:|
| exact | 40 | 40 | 100 % |
| 10 % word errors | 40 | 38 | 95 % |
| 25 % word errors | 40 | 30 | 75 % |
| unseen lines (negative) | 2 | 2 rejected | 100 % |

This validates the fingerprint/`top-k` mechanism only. It says nothing about choir, instruments, repeated
choruses or timing.

## Required before any sung-lyrics claim

1. Written consent for the singers and the recording; licensed or public-domain lyric text.
2. Fixtures: solo voice, choir, repeated chorus, instruments at −5/0/+5/+10 dB SNR, partial lines, intentional
   silence, out-of-catalog songs.
3. Metrics: top-1/top-3, false-activation rate, line-follow error (lines behind/ahead), confidence calibration,
   human correction time.
4. Keep automatic song recognition research-only; the operator selects the song manually.

## Operator-first workflow (recommended, no GUI change in this branch)

Search authorised local song → verify attribution → advance/repeat verse/chorus/bridge → projector preview →
freeze/blank → offline operation. Automatic matching is an assist, never the authority.
