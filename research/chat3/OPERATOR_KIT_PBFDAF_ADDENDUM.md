# Operator kit addendum — PBFDAF research, 2026-11-12

This addendum updates the next acquisition stage. The original `OPERATOR_KIT.md`
and `REAL_GOLD_PROTOCOL.md` are retained as historical evidence. In particular,
the old operator kit's **2 pp threshold is superseded by 5 percentage points**.
No consented gold was supplied or collected in this study. `BLOCKED_GOLD`.

1. Capture **at least three consented services**, at least 20 minutes each. For
   three nonempty, fully speaker-disjoint train/tune/holdout partitions, recruit
   **at least three distinct target speakers**; three services from one speaker
   cannot satisfy that split. Ten services remains an expansion goal. Include
   the requested accents where available and record eligibility without names.
2. Use one interface/recorder clock for raw, separate **48 kHz, 24-bit** channels:
   target lapel/headset 15–20 cm from the mouth/chin, room mic 3–6 m away. Log
   devices, placement, PA routing, fixed gain settings, peaks/clipping, room,
   music, overlap and interruptions. Keep processing/AGC disabled. Slate/clap at
   the beginning and end; retain any observed clock drift and sync offset.
3. Obtain the required speaker permissions before recording. Keep consent,
   provenance, permitted research uses, retention and withdrawal records outside
   Git, linked by anonymous IDs. An unavailable or unverified permission blocks
   that asset. Audio and participant identities stay outside the public repo.
   No cloud audio upload is authorised by this experiment.
4. Two independent humans transcribe the **target only**, independently of ASR.
   Adjudicate disagreements and retain independent versions and their hashes.
   Label `TARGET`, `OTHER`, `MUSIC`, `SILENCE`, `OVERLAP` and `SCRIPTURE_REF`, with
   timed spans and anonymous speaker IDs. Empty target references stay in the
   no-target audit and never enter the WER denominator. Do not relabel the other
   preacher's accurate quotation as target speech.
5. Freeze source hashes, transcription hashes, consent eligibility, speaker and
   session splits, scoring rules, bootstrap unit and latency budget before
   tuning. Case positions 01–20/21–30/31–40 are the synthetic protocol, not an
   automatic real-world speaker split. Freeze independent no-target and overlap
   controls too; control outcomes cannot select thresholds or filters.
6. Compare close-only, scalar, FIR32, FIR+DT and PBFDAF on identical eligible
   clips and ASR configuration, with complete expected-key and sample coverage.
   Any deliberate output delay must have source timestamps and an explicit
   latency budget. Never advance the room input silently. Score missing/truncated
   outputs as failures, never omit them. Report WER = Σ(S+D+I)/ΣN, intrusion,
   target loss, correct/wrong/missed cards, and no-target words/cards separately.
7. Use 2,000 paired bootstrap resamples at the prespecified independent unit
   (speaker/session for real data), and report uncertainty and sample sizes.
   Keep close-only as the operational baseline pending evidence. A room mic is
   not a clean echo reference and energy/coherence is not speaker identity.
8. Before any product consideration require **≥5 pp paired target-WER gain on
   independent real audio**, **zero additional wrong cards**, **zero emitted
   no-target cards**, and **≤5% lost correct cards**, with measured end-to-end
   latency and channel/device robustness. Report correct-card denominators;
   suppressing every card cannot pass. Freeze thresholds on tune data only.
9. Measure capture-to-ASR-to-matcher latency with timestamps. `card_visible`
   requires a separately authorised, attended observation of an actual candidate
   build. It is `NOT_MEASURED` here; no screenshot exists. An FFT block delay or
   DSP throughput number is not end-to-end latency.
10. `<6%` church WER requires frozen real-corpus proof. Passing research gates
    still requires explicit product-team approval before any integration, merge,
    model replacement or release. This branch performs none of those actions.

Minimum manifest fields remain those in `OPERATOR_KIT.md`; also retain span-label
hashes, permission eligibility, gain/clipping logs, channel processing settings,
drift measurement, expected-output keys and the frozen scorer configuration.

`RESEARCH_GO` · `BLOCKED_GOLD` · `PRODUCTION_NO_GO`
