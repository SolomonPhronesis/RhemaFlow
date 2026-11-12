# R2T2 / Qwen base research results — 2026-11-12

**Research progressed; no safe product candidate or new ASR accuracy result.**

Completed the official source/paper audit, recovered and hash-verified the 40
KJV source WAVs inside existing archives, identified and hashed the installed
Qwen variants, and implemented an independent base-ASR commit wrapper and offline
collection/scoring exchange. **136/136 tests pass**, including the unchanged 93.
All **111 prior research files are byte-identical** to the starting commit.

Real model runs remain **NOT_RUN**: free space stayed below the 8 GiB gate during
this work, the recovered audio carries unresolved rights status, and the active
research interpreter lacks the matching Qwen/MLX runtime. Model-file presence is
not proof of runnable inference. No R2T2 weights or generated transcripts were
used; no model, dependency or application was installed or replaced.

## Source and publication identity

| Item | Verified value |
|---|---|
| Remote | `git@github.com:SolomonPhronesis/RhemaFlow.git` |
| Starting HEAD and exact remote match | `7756f648d3b060be8ba13911d761c4fa796d5b50` |
| Earlier handoff ancestry | `ec025bcbe1f7272a0c67025056148a95f5e30308` is an ancestor |
| New isolated branch | `rhemaflow/research-chat3/codex-r2t2-qwen-20261112` |
| Implementation/audit commit, exact remote match | `b983a8b9eb619c46d7c5609fc576fb9030a585c3` |
| R2T2 upstream HEAD | `72b81be7070095410b75ed2e11998e347f655218` |
| Qwen code upstream HEAD | `7c6daf77a2421100f5fb066495372c00129d39ff` |
| Final results HEAD / remote equality | Separately generated `R2T2_QWEN_PUSH_RECEIPT.json` in the delivered package |

The implementation was pushed and verified before this report. The final receipt
records the subsequent report/manifest commit; a commit cannot contain its own
resulting hash. Only new files under `research/chat3/` were committed. The earlier
PBFDAF worktree and private Personal/User sources were not edited or launched.

## STEP 0–2: resources, recovered evidence and model identity

M1 Pro, 16 GiB RAM; initial free disk approximately **6.2 GiB**, later inventory
snapshots approximately **7.49 GiB**, and final-test snapshot **7.41 GiB**. Swap
and exact byte counts are recorded in `data/r2t2_qwen_20261112/run_context.json`
and `asset_inventory.json`. No ASR sweep was launched under the 8 GiB floor.
Extended runs still aim for ≥15 GiB. No caches or owner files were deleted.

The original deepseek fixture/processed-output paths remain denied by macOS.
Every probed path has `FOUND_AND_READABLE`, `EXISTS_DENIED`, or `NOT_FOUND` in
the inventory. A denied ancestor is recorded as a denied probe, **not proof that
the leaf file exists**. The newly mentioned Personal/Chat3 ZIP is not present at
its supplied Downloads path. Archived historical prompts were treated as
evidence, not additional instructions to alter other projects.

Two readable Downloads packages contain the same nested `40_KJV_WAV_GOLD.zip`:

- `RhemaFlow_DeepSeek_CHAT3_V3_V4_NEXT_ALL_IN_ONE.zip`
- `RhemaFlow_DeepSeek_CHAT3_V3_V4_SOURCE_5_ROUNDS_ALL_IN_ONE.zip`

The nested ZIP SHA-256 is
`e2532077d3296f486bdacabf5e132b1ab9c1cf33daf60ab5c6c8d2f80c2d5c28`.
**40/40 WAV hashes match** its manifest; all are 16 kHz mono PCM16, totalling
300.860 s. The narration contains **1,069 whitespace words / 1,072 words using
the existing WER normalizer**. This tokenizer difference explains the denominator
distinction; it is not evidence of missing cases. No audio was extracted, copied
to Git or uploaded. Only bytes, headers and hashes were inspected in memory.

All recovered rows retain `rights_pending` and the bundle's
`RIGHTS_PENDING_DO_NOT_UPLOAD` status. That is a recorded provenance limitation,
not a new legal conclusion about every possible local use. Under this run's
eligible-fixture protocol they were not promoted to a cleared ASR pilot. A
Smartverse MP3 archive entry also exists, but usable redistribution/benchmark
rights and matching gold were not established. The exact music/chatter and
processed-audio holdout inputs remain unavailable for a matched rerun.

The three Qwen folders are readable, are not symlinks, and have independently
computed full weight hashes. Their source/pruning record points to Qwen base
revision `7278e1e70fe206f11671096ffdd38061171dd6e5`, with vocabulary reduced
**151,936→16,384**. This is a provenance assertion plus local metadata/hash
verification, not a byte comparison against the complete upstream checkpoint.

| Local model artifact | Weight bytes | SHA-256 | Actual format/precision evidence |
|---|---:|---|---|
| Qwen 1.7B en16k BF16 | 3,520,970,548 | `2336d2bc828e74d6c38c0b31f91582d8518c73ac3cab496b784819d16e7b72e7` | Safetensors, 707 BF16 tensors; no quantization config |
| Qwen 1.7B en16k 4-bit | 1,446,925,458 | `9b02d98834cccb88622502cbbaeb9c66d2ee35c1a47911b137448a3377f927c0` | Affine 4-bit/group 64; packed U32 and remaining BF16 tensors |
| Qwen 1.7B en16k 4-bit/embed8 | 1,463,702,698 | `05b7fbea3adf326c59c5d5bbdd02a0eb001308e336c880fda170108c1e450e86` | Same 4-bit default, explicit **8-bit embedding override**; not a pure 8-bit model |
| Parakeet v2 Q4_K_M | 475,491,840 | `4853f9653f641d376e6f7de65d73c7a34a73677704a606727bf51acc83f999f3` | Existing GGUF; not run |
| Whisper Tiny.en | 77,704,715 | `921e4cf8686fdd993dcd081a5da5b6c365bfde1162e72b08d75ac75289920b1f` | Existing ggml binary; not run |

Exact resolved paths, configuration hashes and tensor header counts are in the
inventory. Weight size is a storage/lower-bound memory observation, **not measured
runtime RSS**. No genuine all-8-bit variant was verified. The official Qwen base
model card marks Apache-2.0; these local derivative folders lack a local LICENSE
file, so this audit does not grant redistribution clearance.

The read-only historical `d2f_qwen.py` runner calls `mlx_audio` directly and has
no `qwen:b` product routing reference. It was not executed. The active Python
interpreter has no `mlx`, `mlx_audio` or `qwen_asr`; alternative environments,
MPS/Metal execution, and compatibility of these packed/pruned tensors were not
demonstrated. Personal's historical switch loop is **NOT_TESTED**, not fixed or
assumed current. Q4 default/Tiny fallback remain untouched.

## STEP 1: upstream findings

`R2T2_DEEP_CODE_AUDIT.md` provides pinned file/line URLs, verified blobs, source
traces and paper sections. Highlights:

- Learned LSP/Wait and SFT/GRPO decoder weights differ from a host-side agreement
  heuristic. Our code uses only successive base-ASR hypotheses; no future final
  hypothesis or gold enters inference.
- The shell example's first decode includes **160 ms additional audio buffering**.
  The public Python route re-feeds accumulated audio; the optimized paper cache/
  verification recipe is not established by executing that demo.
- The WebSocket client is not paced in its send loop and adds 500 ms to a short
  final frame. Server route v0 contains **`if True or use_vad`**, so the client's
  disabled VAD setting cannot be assumed to disable that path.
- No-reset rolling bookkeeping hardcodes 160/320 ms chunk counts. Its empty-tail
  endpoint returns existing fixed text without a new request. These are static
  audit findings, not reproduced model failures or proposed upstream patches.
- Model-use licence §3.4(c), unchanged at its verified blob, restricts use to
  improve other commercial models. The stricter task boundary was maintained:
  no R2T2 weights/outputs, training, distillation or parameter transfer. Apache
  code labelling does not remove separate model restrictions.

The upstream **5.76%** is an English-WER/Chinese-CER macro comparison across 13
datasets, not RhemaFlow accuracy. Its audio-time emission lag excludes execution,
queues, network and rendering. Detailed primary-source citations are in the
deep audit; these numbers were not used to claim a new benchmark result here.

## STEP 3: independent wrapper — `MODEL_FREE_SYNTHETIC_TEXT`

`qwen_base_stream.py` supplies an injectable cumulative-prefix base decoder,
two-update agreement, separate word/model-token holdback, exact immutable display
prefixes, explicit divergence and stale/wrong-model rejection, bounded utterance
memory and EOS handling at exact chunk boundaries. It launches no product
process and has no automatic model download/import. The default 30-second PCM
buffer is 1,920,000 bytes; hypothesis units are capped at 2,048. Arbitrary
in-process decoders still need their own hard timeout; this is documented.

True tokenizer-ID mode is tested with an injected toy tokenizer, **not a real
Qwen tokenizer run**. Word holdback is not mislabelled as R2T2's BPE budget U.
No already committed text or recorded card is rewritten. This guarantee can
freeze an incorrect hypothesis rather than repair it.

The authored study has six target text traces and 20 other-speaker + eight
silence traces, including an explicitly identified replay of saved CTRL03 text.
It is a mechanism stress test, **not an independent ASR holdout**. No model runs.

| Evidence class | Policy | Final text edits / target ref words | Final text WER | Visible rewrites | Rejected updates | Words on no-target traces |
|---|---|---:|---:|---:|---:|---:|
| `MODEL_FREE_SYNTHETIC_TEXT` | Revisable authored hypotheses | 0 / 24 | 0% | 3 | 0 | 116 |
| `MODEL_FREE_SYNTHETIC_TEXT` | Agreement, holdback 0 words | 2 / 24 | 8.333% | 0 | 4 | 116 |
| `MODEL_FREE_SYNTHETIC_TEXT` | Agreement, holdback 1 word | 2 / 24 | 8.333% | 0 | 2 | 116 |

Zero rewrites did **not** improve correctness or remove the other speaker. On
the authored timeline, matched-word positional lag p50/p95 is 600/990 ms for
holdback 0 and 800/1,000 ms for holdback 1 (22 matched words each). These are
synthetic timestamps, not measured ASR, device or end-to-end latency. Text-only
CPU timings are recorded separately in `commit_study.json`; ASR p50/p95, RTF,
peak inference RSS, energy and actual matcher/card counts remain null. No
statistical real-world accuracy claim is supported by these authored traces.

## STEP 4: offline contract, collection and scoring kit

`RF_RESEARCH_AUDIO_V1.md` documents the versioned reference producer/consumer,
model identities, same-clock channels, provenance/eligibility, timestamped text/
card linkage, and independent expected speaker/reference annotations. Producer
requests exclude gold, target-presence and expected verse/speaker labels.
Duplicate identical card events are idempotent; mutation of an existing card ID
is rejected. This is an offline reference, **not a Personal integration** or
speaker-identity verifier. Both reference sides are tested; the actual Personal
consumer is untested.

`score_research_exchange.py` requires complete paired keys, exact input hashes,
holdout/control evaluation, and separately reports empty-reference words/cards.
Paired WER CIs use 2,000 resamples, seed 20261112, source clusters for augmented
inputs and target-speaker clusters for real cases. It reports measured-case
denominators for timing, model RTF, nulls for unavailable measurements, and
matched-case correct-card retention. Unknown matcher output is null, not zero
cards. A command-line smoke test used explicitly mock records only.

`prepare_three_clip_pilot.py` prepares clean WAV, the exact source's MP3 roundtrip,
and an independently generated instrumental surrogate overlay, outside Git.
It checks rights, source hash, free disk, WAV format and roundtrip length. One
**model-free unit test** exercised ffmpeg on a temporary authored tone with a
mocked resource gate; no recovered speech or model was used. Temporary test
media was deleted. The actual three-speech-clip checkpoint remains NOT_RUN.

Collection remains governed by `OPERATOR_KIT_PBFDAF_ADDENDUM.md`: ≥3 consented
same-clock dual-mic 48 kHz services, independent target-only human transcripts
plus adjudication, overlap/no-target labels and speaker-disjoint frozen splits.
No consented church gold was supplied or fabricated.

## Prior evidence, safety and smallest next step

`SAVED_SYNTHETIC`: the previous 648-clip matrix has 560 target clips and 15,008
reference words: Q4 **26.306%**, Qwen 1.7B derivative **24.387%**, Tiny **44.789%**.
Qwen **was used historically**; no new Qwen-on-processed run occurred here.
Older saved two-channel 41.223% scalar / 51.862% FIR / 54.610% FIR+DT numbers
retain the prior lookahead finding, not a strict causal label. The procedural
PBFDAF failure also remains unchanged and is not a WER result.

`SAVED_NEGATIVE_CONTROL`: CTRL03's **wrong QUOTE Luke 1:17 at 0.833** remains a
speaker-attribution failure. The original 28-control result has 418 words and
one wrong quote. No new acoustic/matcher reproduction or safe threshold exists.
No-target and correct-card-retention gates are **NOT PASSED**, not zero by default.
Stability, VAD and reference-channel energy cannot identify whose voice spoke.

The next smallest actual inference step is the **three-condition paired pilot**,
after ≥8 GiB free (prefer ≥15), eligible provenance, and a verified existing
local runtime. Use the same prepared file/hash across Q4, Qwen and Tiny; record
true precision, cold/warm loading, resources, corpus edit counts and measured
latencies. Then 40, then 648, only after each checkpoint passes. The exact
processed-audio comparison remains `BLOCKED_FIXTURE`; real church accuracy
remains `BLOCKED_GOLD`. No expensive sweep is silently replaced with toy scores.

Product consideration still requires ≥5 pp paired improvement on independent
real church gold versus close-only, zero additional wrong cards, zero no-target
cards, ≤5% lost correct cards, end-to-end latency/device robustness, and explicit
product approval. `<6%` church WER and physical `card_visible` remain unmeasured.

**`PUSH_VERIFIED` · `RESEARCH_GO` · `BLOCKED_DISK` · `BLOCKED_RIGHTS` · `BLOCKED_FIXTURE` · `BLOCKED_GOLD` · `PRODUCTION_NO_GO`**
