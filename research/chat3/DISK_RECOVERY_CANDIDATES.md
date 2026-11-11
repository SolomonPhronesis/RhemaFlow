# DISK_RECOVERY_CANDIDATES — read-only inventory, no deletions performed

## Current state (2026-11-11 16:25 UTC)

| Metric | Value |
|---|---|
| Free on `/System/Volumes/Data` | **662 MiB** |
| APFS container | 493.7 / 494.4 GB used, 694 MB not allocated |
| Swap | 9.53 GiB of 11.26 GiB used |
| Gate | below the **4 GiB** hard floor → model-free work only |

**Nothing was deleted, moved or compressed.** The list below is a proposal requiring the owner's explicit
approval per exact path.

## Candidates (measured with `du -sm`)

| Size | Candidate | Provenance | Regenerable | Risk / action |
|---:|---|---|---|---|
| 151 MiB | `matrix_work/audio` | 648-clip matrix generated from the 40 KJV WAVs + owner-approved sources | **yes** (`scripts/build_matrix.py`, ~3 min) | no research value beyond frozen transcripts; approval needed |
| 44 MiB | `matrix_work/gitpush/audio` | Opus/MP3 encodes + decodes | **yes** (ffmpeg, ~2 min) | metrics already captured; approval needed |
| 121 MiB | `RF_CHAT3_NEXT_20261110/fixtures` | 520-clip stress corpus | **yes** (`rf-bench fixtures`) | rebuild needs the build; approval needed |
| 40 MiB | `…/fixtures_stress` | pause + continuous fixtures | **yes** | approval needed |
| 21 MiB | `…/fixtures_pause2` | held-out pause corpus | **yes** | approval needed |
| 2.39 GiB | `~/.cache/huggingface` | Qwen 0.6B / whisper-tiny / R2T2 configs | re-download | not used by V3/V4 pipeline; R2T2 parts must not be used commercially; owner decision |
| 3.9 GiB | `RF_PERSONAL1_EXEC_20261110` | **another chat's workspace** | unknown | **DO NOT TOUCH** — not this chat's data; owner decision |
| 59 GB | `~/Downloads` | owner media/archives | unknown | owner decision; no external SSD mounted |

## Arithmetic

* Chat 3 generated audio (all five rows): **~377 MiB** → free ≈ 1.0 GiB. Still below the 4 GiB floor.
* Adding the Hugging Face cache (owner approval + licence check): ≈ 3.4 GiB. Still below 4 GiB.
* Reaching the 8 GiB comfort zone or the 15–20 GiB needed for checkpoint experiments **requires the owner to move
  or delete ~5–20 GB of their own data** (Downloads or another workspace). Chat 3 cannot do that safely.

## Not proposed

Model weights (Q4, Qwen, Tiny), original recordings, Bible assets, saved raw transcripts, Git objects, macOS
swapfiles, installed apps, User/Personal workspaces.

## Recommendation

Free the 377 MiB of Chat 3 generated audio only after the current reports are pushed (they are). Then cap the
matrix re-generation to one corpus at a time and prefer `du -sm` checks before each build. Large checkpoint work
should wait for an external drive or owner-approved cleanup.
