# Under-6 research accuracy and safety gates

**The owner goal has not been met or measured. PRODUCTION_NO_GO remains in effect.**

## Evidence classification and the current decision

| Evidence class | What may be reported | Current evidence |
| --- | --- | --- |
| `HISTORICAL_SYNTHETIC` | Saved counts/metrics, original denominators and limitations | 648-clip matrix, 560 target clips / 15,008 target words; exact Qwen precision/hash unresolved |
| `NEW_REAL_INFERENCE` | Actual pinned-model logs on eligible real recordings | **0 runs**; no current WER, real-time, RSS, power or card-retention measurement |
| `MODEL_FREE` | Source/header audit, analytic resource estimates, protocol/causality tests | New fail-closed scoring, split and request tests; no acoustic benchmark |
| `NOT_RUN` | Explicit unknown/null metrics | All four priority model arms, full Personal consumer, actual new matcher/UI run |
| `BLOCKED` | Exact missing evidence/resources, not a zero-error score | Disk, matching runtime, rights and independent real gold |

Test pass rates never become accuracy/progress percentages. There is no green
accuracy badge or projected curve toward 6%. R2T2's mixed-language aggregate is
not placed on the RhemaFlow church-WER chart. Charts display saved denominators;
missing CIs stay absent. They do not imply a new independently reproduced run.

## Required owner-goal observations

1. **Real corpus WER <6%.** Score literal independent target-only gold; accumulate
   S/D/I over target words, not a mean of clip percentages. Empty references are
   excluded from that denominator and audited separately for words/cards. Do
   not replace spoken language with a KJV matcher result to manufacture gold.
2. **Paired gain ≥5 percentage points over close/lapel-only.** Identical frozen
   services/conditions, complete case coverage, preserved failures and pinned
   model/adapter identities. Report a paired cluster 95% interval, seed and
   resample count; no gain claim from an unmatched denominator.
3. **Zero wrong no-target Bible cards, zero extra false cards.** Count QUOTE and
   REVIEW on target-absent windows. Other-preacher verse quotations are false
   target attributions even when the reference is lexically correct. Independently
   annotate target/other/unknown; diarizer index or match confidence is not truth.
4. **≤5% correct-card-event loss.** Match independently annotated true target
   events, not just a raw card count. Candidate retention is the paired retained
   baseline event set divided by the baseline-correct set. If that set is empty
   or matcher observations are missing, retention is undefined and cannot pass.
   Blanket silence fails this gate. No new product abstention guard was added.
5. **Real-time operation on the M1 Pro 16 GiB.** Capture p50/p95 end-to-end latency,
   p95 pipeline RTF, peak RSS/swap, measured energy/battery and dropouts. The
   research auditor uses observed p95 RTF≤1 as an operational throughput check;
   it does not invent an owner-approved millisecond latency SLO. Report temporal
   and safety regressions even if a point WER improves. Native platform support,
   file size and audio-time emission lag are not measurements.

At least three consented same-clock 48 kHz dual-mic services, two independent
human transcribers and adjudication are prerequisites. The real holdout must
be disjoint from training/tuning by church, session, every audible speaker and
source/augmentation lineage. No restricted or unapproved data is uploaded.
Three services alone do not guarantee enough independent statistical clusters.

## Statistical contract

`under6_evaluation.py` computes corpus counts and paired gains, resampling
**connected church/speaker/session groups** (2,000 resamples, seed 20261112).
Repeated recordings from one shared church or preacher are not treated as
independent clusters. If there is fewer than two connected clusters, the CI is
null and the interval gate remains unmet. With few clusters, intervals can be
unstable: report group counts and do not generalize to all churches. Both model
arms retain the same sampled groups/denominators in every bootstrap draw.

The numeric owner thresholds use point estimates; the interval is reported
separately, not secretly substituted for a different acceptance threshold. A
`RESEARCH_GATES_MET` return is only a protocol result on supplied evidence. It
never approves a product, validates consent from a Boolean alone or authenticates
an operator's logs. Provenance, actual physical UI observation, identities and
source documents still require independent review; final promotion is explicit.

## Current failures that must remain visible

- Saved **CTRL03**: other preacher, chatter-only, **Luke 1:17**, confidence **0.833**.
  Saved controls contain 418 ASR words across 28 no-target cases and one wrong
  quote. The original audio/matcher was not reproduced here; the failure remains
  unresolved, not a new rate or a passed speaker guard.
- Saved aligned scalar/FIR/FIR+DT WER gains contain a future-sample/lookahead
  dependency. Preserve their arithmetic, retire zero-lookahead gain claims.
- Genuinely causal procedural PBFDAF: ΔSIR +0.789 dB, but ΔSI-SDR **−1.008 dB**
  versus close-only and **−9.743 dB** target-loss stress case. Procedural signals
  have no ASR words, so they cannot supply a WER improvement or card result.
- Independent stable-prefix output can be stable and wrong. It cannot establish
  speaker ownership, unseen accent/noise accuracy, or safe irreversible cards.

## Implemented model-free protections and interface limits

The new offline scorer refuses incomplete pairs, mismatched channel provenance,
unknown matcher outputs as zero, cross-split group/source leakage, and missing
independent gold/runtime observations. A matching verse from an independently
labeled other speaker is not counted as retained target evidence. Future-suffix
perturbation tests exercise the existing decoder's past-only input boundary.

Inference requests contain only allow-listed audio descriptors and a base model's
weight/tokenizer identity. Gold, expected verse/card events, split and speaker
truth are excluded. LoRA/training plan checks require frozen base/tokenizer/
holdout/config identities, disjoint groups and explicit commercial training
rights, and reject every teacher in the present plan. No trainer is implemented
or executed by that validator.

`RF_RESEARCH_AUDIO_V1.md` and its original implementation are unchanged. New
`RF_RESEARCH_TRIAL_V2_DRAFT` envelopes describe the explicit Q8 arm/tokenizer
identity without pretending an existing V1 consumer supports it. Personal's
published report identifies `b5ddb69e77501ec00662db047ed53f7eb84db969`; only that
read-only export/interface was consulted. No private Personal source, cache,
installed release or runtime route was modified or integrated.

## Promotion boundary

Source-only research manifests export hashes, evidence classes, limitations,
protocols and optional scripts. They carry `promotion_approved:false`, no audio,
weights, adapters, teacher outputs or automatic consumer action. Personal must
independently review a candidate, verify actual measured accuracy and card gates,
then pass its own install/release approval. No source push authorizes merge,
deployment, model replacement, automatic card suppression or data transfer.

Current state: **RESEARCH_GO / BLOCKED_GOLD / PRODUCTION_NO_GO**.
