# Chat 3 under-6 research continuation — 2026-11-12

**Safe research stages completed. No new ASR accuracy result; owner goal unachieved.**
`RESEARCH_GO · BLOCKED_GOLD · PRODUCTION_NO_GO`.

The source-pinned idea map, model identities, weight-space feasibility, paired
pilot plan, fail-closed evaluation tools, ranked HTML report and versioned
source-only manifest are delivered. **153/153 model-free tests pass**, retaining
the unchanged 136-test baseline and adding 17. All **136 pre-existing research
files are byte-identical** to `fd48afb76abb8f11a37b6a28ae9145c810d8b7a2`.

## Deliverables and evidence

- [Readable HTML ranking, charts and evidence filter](RESEARCH_RESULTS.html)
- [R2T2 / Qwen / NVIDIA source idea map](CHAT3_R2T2_QWEN_WEIGHTS_IDEA_MAP.md)
- [Owner priority and exact checkpoint identities](RESEARCH_PRIORITY_AND_EVIDENCE.csv)
- [Three-clip sanity pilot and expansion conditions](THREE_CLIP_PILOT_PLAN.md)
- [Conditional weight-space feasibility](MODEL_WEIGHT_SPACE_FEASIBILITY.md)
- [Accuracy, card, provenance and resource gates](CHAT3_UNDER6_SAFETY_GATES.md)
- [Versioned source-only research manifest](CHAT3_UNDER6_RESEARCH_MANIFEST.json)

Exact final source HEAD, branch, remote equality and unchanged default branch
are recorded in the separately generated `CHAT3_UNDER6_PUSH_RECEIPT.json` after
publication. The work branch is
`rhemaflow/research-chat3/under6-weight-space-20261112`, on public
`SolomonPhronesis/RhemaFlow`, based on `fd48afb…`. This report cannot contain its
own final commit hash. Only `research/chat3/` additions are intended for push;
no merge, deployment, Personal/User source edit or installed release change.

## What materially changed in the research evidence

1. The larger local **Parakeet v2 Q8** is now freshly identified: **729,574,912
   bytes**, SHA-256
   `f0d0e99cebb6d3b83f1f7069b82b5d3c2e39a54545b0da039cb4bafd9c4e5caa`.
   Its GGUF header names v2 and contains 225 Q8 tensors plus F16/F32 tensors.
   It is not the separately labeled 1.256 GB legacy v3/F16 artifact.
2. Qwen embed8/Q4/BF16 whole-weight hashes were freshly rechecked, and tokenizer
   identities now hash the actual vocab/merges/config/template file set. The
   embed8 variant is mostly 4-bit with 8-bit embeddings, not a full-8-bit model.
3. Header-only analytical bounds show 1,760,441,984 BF16 parameter elements and
   about **28.17 GB** conventional full mixed-Adam state before activations.
   Decoder-attention LoRA ranks 8/16 would add 3,211,264 / 6,422,528 parameters.
   Neither formula is a measured training RSS, performance result or M1 promise.
4. Current official NVIDIA native source documents Apple/Metal support. Its
   cache-aware Nemotron English and Sortformer paths deserve a later approved
   experiment; inspected TDT v3 is full-utterance only. No runtime was installed,
   no model downloaded and no NVIDIA speed/quality result was adopted as local.
5. The new offline evaluator separates real, saved, model-free and absent
   evidence; checks paired corpus denominators, connected-group confidence
   intervals, source/split leakage, target attribution and retained card events.
   Stable other-speaker text and suppressed cards cannot produce a safety pass.
   A draft V2 envelope explicitly names Q8/tokenizer identities; V1 is unchanged.

R2T2 and Qwen upstream revisions remain unchanged; 32 source text records have
traceable hashes/URLs. The paper/model/license and current NVIDIA cards were
reviewed read-only. No R2T2 weights, logits, generated transcripts, trained
parameters or teacher outputs were used. Bark remains text-to-audio, outside the
ASR ranking. No LoRA, fine-tuning or distillation was executed.

## Findings that remain negative or unknown

Historical synthetic counts still yield Qwen-family **24.387%**, Parakeet Q4-arm
**26.306%**, Tiny **44.789%**, all over 15,008 target words / 560 target clips in
the old 648-condition matrix. Their exact equivalence to current checkpoints is
unverified; in particular the Qwen precision/hash is unresolved. These are saved
counts, not fresh inference, real church accuracy or a statistically established
trajectory toward 6%.

Saved CTRL03 still records a **wrong Luke 1:17 card at 0.833**; the original
no-target controls contain 418 ASR words. The old aligned filter gains retain
the future-sample defect. Causal procedural PBFDAF retains **−1.008 dB SI-SDR**
and **−9.743 dB target-loss stress** despite +0.789 dB interference gain. No
speaker guard or filter is promoted. Actual correct-card retention, ASR latency,
RSS, energy, battery and physical card-visible measurements remain null.

## Validation and current execution boundary

| Check | Observed result |
| --- | --- |
| Original research suite | 136 passed before changes |
| Complete research suite | **153 passed**, 0 failures/errors; MODEL_FREE only |
| New scope | 13 protocol/evidence/causality tests + 4 header/resource tests |
| Original research files | 136/136 byte-identical |
| HTML QA | Observed full report and three SVG charts in the in-app browser; filter shows only MODEL_FREE then restores all; 1280px page/viewport with no body overflow |
| Mobile/native product QA | Not performed; no product UI claim |
| Model/ASR/training runs | **0** |
| Install/download/transfer | **0** model/runtime installs, model downloads or audio/model uploads |

The host is freshly verified **Apple M1 Pro, 16 GiB physical RAM**. Initial
inventory free disk was 3.78 GiB; the final snapshot fell to **1.49 GiB**.
No heavy ASR sweep, build or model preparation was launched below the 8 GiB
floor; no owner data or cache was deleted. Lightweight source tests/report
rendering were completed. The displayed HTML intentionally labels its 3.78 GiB
value as the earlier inventory snapshot; this report records the later reading.

Recovered 40 KJV WAVs were hash/header-audited in their archives only; they remain
rights-pending and were not extracted, run or uploaded. Matching original
music/chatter inputs still have inaccessible/uncleared paths. The active Python
lacks `mlx`, `mlx_audio`, `qwen_asr` and `nemo`; other environments and exact
checkpoint loaders are not verified. No consented real church gold was supplied.

Therefore actual inference is **BLOCKED_DISK / BLOCKED_RUNTIME / BLOCKED_RIGHTS**;
real church qualification is **BLOCKED_GOLD**. The minimal next step is the
bounded, one-model-at-a-time three-file sanity pilot after rights, headroom and
runtime verification. Only then expand to noisy-target conditions and real
48 kHz dual-mic services with independent transcripts and paired safety metrics.
The operator requirements are concrete in the pilot/gate documents; no repeated
permission request or model promotion is implied.

The versioned manifest exports source/protocol/evidence hashes only and has
`promotion_approved:false`. Personal's b5ddb69 identity was read from its published
export; no private code or model transfer occurred. **PRODUCTION_NO_GO.**
