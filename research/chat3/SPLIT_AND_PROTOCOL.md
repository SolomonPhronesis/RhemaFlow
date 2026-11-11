# SPLIT_AND_PROTOCOL — frozen partitions and the real two-mic checklist

## 1. Frozen splits (`data/split_manifest.csv`)

| Split | Case ids | Rule |
|---|---|---|
| train | 0001–0020 | not used for fitting anything |
| tune | 0021–0030 | only place parameters were chosen |
| holdout | 0031–0040 | scored once, after selection |

Tuning used a signal-level objective (ΔSIR on tune), never holdout ASR. The mixing coefficients, delay, leak and
drift are random per clip and are never passed to the algorithm.

## 2. Anti-leakage rules applied

* algorithm inputs are the two channels only (unit test enforces the signature);
* delay estimated on the first 400 ms, then frozen;
* no target/interference/gold used in processing or parameter choice;
* scorer v2 with explicit ids and coverage; no clip dropped.

## 3. Real two-mic checklist (operator)

1. **Consent** per speaker (pastor; any identifiable voice), research use, anonymised quotations, withdrawal right.
2. **≥ 3 sessions** initially, target 10; **close mic** (lapel/headset) + **room mic** on the same recorder or
   word-clock-locked devices; slate/clap at start for alignment.
3. Record 48 kHz where possible, keep originals, log device, distance, PA, room, music, second speaker.
4. **Synchronise**: measure inter-channel delay per session from the slate; log clock drift over the session.
5. **Annotate**: two independent transcribers for the target preacher, third-pass adjudication, span labels
   `TARGET/OTHER/MUSIC/SILENCE/OVERLAP/SCRIPTURE_REF`, frozen SHA-256 manifest.
6. **Evaluate**: close-only vs scalar vs FIR vs no processing, same utterances, scorer v2, cards, latency, and
   `card_visible` only if observed.
7. **Data governance**: store only speaker IDs and consent IDs in Git; audio stays local; no cloud upload without
   separate approval.
