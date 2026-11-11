# BEFORE → AFTER

## Base

* Repository: `SolomonPhronesis/RhemaFlow.git` (verified remote, SSH reachable)
* Base commit: `5e31b98916e1886d1ede2b71f022b5deb172d10b` (`fix: register service worker for full RhemaFlow app`)
* Branch created for this work: `rhemaflow/research-chat3/opus-lyrics-noise-20261111`
* Isolated worktree: separate directory, clean status before the change.

## After (this commit)

| Change | Detail |
|---|---|
| Added `research/chat3/RESULTS.md` | measured results, verdicts, reproduction |
| Added `research/chat3/BEFORE-AFTER.md` | this file |
| Added `research/chat3/data/*.csv` | aggregated metrics only (no audio, no raw transcripts) |
| Added `research/chat3/scripts/*.py`, `*.sh` | reproducible harness for Opus, lyrics, cloud contract |
| Added `research/chat3/SHA256SUMS.txt` | hashes of every committed research artifact |
| Modified app source | **none** |
| Deleted anything | **none** |
| Added binaries / models / audio / lyrics | **none** |

## Why no code changes to the app

This round is evidence work: codec, lyric-matching and restore-contract behaviour plus noise robustness numbers.
Changing the Rust engine on a 3.3 GiB-free machine, without human gold, would be an unverified production change —
explicitly out of scope.
