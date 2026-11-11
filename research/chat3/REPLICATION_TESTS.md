# REPLICATION_TESTS — codec mapping, restore contract, limitations

## 1. Codec findings (re-verified from saved transcripts, no new encodes — disk < 3 GiB)

| Export | effective kbps | MB / 2 h (extrapolated) | ASR WER v2 |
|---|---:|---:|---:|
| clean PCM | 221.8 | 199.6 | 1.848 % |
| clean Opus 16 / 20 / 24 kbps | 14.6 / 18.0 / 21.5 | 13.1 / 16.2 / 19.4 | 1.848 % each |
| clean MP3 64 kbps | 56.5 | 50.8 | 1.848 % |
| mixed music-0 PCM | — | — | 3.285 % |
| mixed music-0 MP3 64 kbps | 56.5 | — | 3.285 % |
| mixed music-0 Opus 24 kbps | 21.5 | — | 3.696 % |

**Case mapping and segmentation:** v2 scores with an explicit manifest, 100 % coverage (20/20 clips), no duplicate
ids, identical denominators across variants (487 reference words), so the +0.41 pp Opus-under-music penalty is not
a mapping artefact.

**Recommendation:** speech archive Opus **16–20 kbps**; worship/music **≥ 32 kbps, normally 48–96 kbps**.
Subjective quality `NOT_MEASURED`.

## 2. Restore contract (synthetic only)

15/15 injected-failure cases pass: clean restore; corrupt replica; missing replica; chunk lost everywhere
(fails closed); single good replica; wrong pinned hash; tampered manifest; restored manifest; truncated chunk;
manifest version bump; old pin rejects new manifest; stale key id rejected; crash/resume from partial cache;
corrupt cache chunk discarded; stale-key replica skipped with peer fallback.

| Contract | Behaviour |
|---|---|
| manifest pinning | SHA-256 of canonical manifest; mismatch refuses restore |
| chunk integrity | size + SHA-256 before use |
| failover | first valid replica; per-replica error trail |
| resume | verifies partial cache, discards bad partials, continues |
| stale keys | key-id mismatch rejects the chunk |

## 3. Limitations

* Synthetic ciphertext proves the **contract**, not provider reliability; **no 99.999 % claim**.
* No provider credentials were used; no audio left the machine; no real R2/Hetzner/AWS calls.
* Codec latency and subjectively perceived quality are `NOT_MEASURED`; only ASR round-trip and size are measured.
* 2-hour sizes are **extrapolated** from 160 s / 30 s samples.
