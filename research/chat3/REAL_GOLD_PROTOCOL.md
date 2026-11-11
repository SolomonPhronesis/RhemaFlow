# REAL_GOLD_PROTOCOL — status `REAL_GOLD_NOT_AVAILABLE`

No consented, dual-channel, human-transcribed church recordings exist on this machine. Nothing here replaces that.

## Minimal acquisition protocol (operator)

1. **Consent**: written per speaker (pastor + any identifiable congregation voice), research use and anonymised
   quotation; store `consent_id` only.
2. **Sessions**: ≥ 10 services, ≥ 2 pastors (Nigerian and Ghanaian English where available), close lapel/headset
   **and** a room mic recorded simultaneously on the same clock.
3. **Capture**: 48 kHz where possible; keep originals; note device, distance, PA, room, music, second speaker.
4. **Annotation**: two independent annotators transcribe **the target preacher only**; third-pass adjudication;
   span labels `TARGET/OTHER/MUSIC/SILENCE/OVERLAP/SCRIPTURE_REF`; freeze SHA-256 manifests.
5. **Splits**: speaker-disjoint train/dev/test; sessions disjoint within speaker.
6. **Metrics**: target WER, intrusion words, target speech lost, cards correct/wrong/missed, end-to-end latency,
   and physical `card_visible` if observed.

## Why synthetic cannot substitute

The synthetic pair has known components, no reverb, fixed delay and no drift; a real room has all four. The
reverb/drift check above already shows the scalar canceller collapses there — real data is the only way to know
whether an adaptive FIR recovers the gain.
