# R2T2 / Qwen base deep code audit — 2026-11-12

Research source inspection only. **No R2T2 weights, inference, generated outputs,
pseudo-labels, training or trained parameters were used.** The new wrapper is an
independent local-agreement mechanism, not an R2T2 implementation or trained LSP.

## Verified revisions and scope

GitHub's connected repository API reports R2T2 `master` at
**`72b81be7070095410b75ed2e11998e347f655218`**, unchanged from the previous audit;
Qwen `main` is **`7c6daf77a2421100f5fb066495372c00129d39ff`**. Recursive trees were
not truncated. Twenty selected text/code files were fetched at those exact
commits; every byte sequence independently reproduces its Git blob SHA-1.
SHA-256, blob, size and line count are in
`data/r2t2_qwen_20261112/upstream_source_manifest.json`; complete tree metadata is
retained alongside it. Source snapshots stay in the local scratch directory;
no upstream binary, sample recording or model weight was downloaded.

The R2T2 tree contains **48 blobs**, including prebuilt native libraries, but no
SFT/GRPO/LSP training pipeline, training corpus or `.gguf`/`.safetensors` checkpoint.
Model links exist, which is different from weights being in Git. Qwen's tree
does include `finetuning/qwen3_asr_sft.py`; that is **not** R2T2's training recipe.
The earlier audit table mixed README blob identities: root R2T2 README is
`cdba2d56…`; `4fe4920d…` belongs to `r2t2_llama/README.md`. Earlier artifacts remain
unchanged; the newly verified file manifest is authoritative for this audit.

## Paper: training targets and runtime claims

The paper is [arXiv:2611.06043v1](https://arxiv.org/html/2611.06043v1), submitted
4 November 2026; no newer version was listed. It post-trains the Qwen3-ASR-1.7B
decoder with SFT then GRPO; encoder/projector stay frozen. Token-level audio
segmentation, hindsight LSP labels and an existing-vocabulary Wait marker supply
training supervision. LSP credits the longest **whole earlier hypothesis** that
is a prefix of the final full-audio output. It is not merely the common head of
two successive hypotheses. Full-audio access belongs to offline label construction,
not online inference. Sections 5–6 describe data construction and training;
scripts/data are absent from this repository.

Sections 7–8 describe completed-window encoder/KV reuse, active-window recomputation,
Wait-terminated decoding, bounded audio/text context and provisional-suffix
verification. `U=0/1` controls unreleased model-token suffixes. Retrospective lag
uses correctly matched reference units on the audio timeline and excludes
high-error utterances, execution, queues, network and rendering. It is not
end-to-end wall time or proof of real-time throughput. These paper mechanisms
require separate implementation verification; reading the public demo is not a
reproduction of the optimized evaluation system.

## Public execution trace (pinned source references)

All R2T2 links below pin `72b81be…`; Qwen links pin `7c6daf7…`.

| Stage | Observed public code and implications |
|---|---|
| Shell entry | [`run_example.sh:36–47`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/run_example.sh#L36) defaults to 160 ms chunks, **160 ms initial extra buffering**, U=1, CUDA selector. Lines 160–169 invoke `example.py`; these are demo defaults, not measured deployment latency. |
| Model loading | [`example.py:164–181`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/example.py#L164) constructs the supplied model through `.LLM`; streaming and one-time modes use different generation limits. Lines 210–245 load/resample audio and choose the route. No decoder is trained here. |
| Chunk framing | [`example.py:100–160`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/example.py#L100) handles 16 kHz PCM, takes the first `step+lookahead` samples, then ordinary chunks, changes token generation budget and finally flushes. |
| Public state/API | [`r2t2_asr.py:226–301`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2/r2t2_asr.py#L226) builds state with context/language, rollback counts and sample-sized chunks. Class defaults are 2 s / two initial unfixed chunks / five rollback tokens; the example overrides them. |
| Hypothesis vs release | [`r2t2_asr.py:380–490`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2/r2t2_asr.py#L380) re-feeds accumulated PCM, trims tokenizer IDs, prompts with a prefix, strips the pipe marker and returns **both raw hypothesis and fixed text**. Cards must not consume the provisional hypothesis. |
| Ordinary endpoint | [`r2t2_asr.py:492–578`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2/r2t2_asr.py#L492) sends a short tail **without padding**. The previous report's padding description is not supported by this function. |
| Rolling endpoint | [`r2t2_asr.py:650–760`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2/r2t2_asr.py#L650) bounds accumulated PCM, evicts 8 s beyond 16 s and appends fixed deltas. Discard bookkeeping hardcodes 160/320 ms chunk counts; nondefault chunk sizes need a separate boundary audit. |
| Endpoint edge case | [`r2t2_asr.py:807–810`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2/r2t2_asr.py#L807) returns existing fixed text without another request on an empty tail in the no-reset route. A held-back suffix therefore needs an explicit EOS policy. This is a **static risk finding**, not an upstream inference reproduction. |
| Native backend | [`r2t2_llama/model.py:140–150`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2_llama/model.py#L140) aligns processor/config windows. [`native_ext.cpp:451`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2_llama/native_ext.cpp#L451) and [731](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2_llama/native_ext.cpp#L731) clear decoder memory on these generation paths. That does not demonstrate the paper's across-update encoder/KV reuse. Shipped CPython native artifacts are Linux x86-64, not an Apple-Silicon validation. |

The ordinary Python route visibly passes accumulated audio to vLLM on each
update. Explicit paper-style completed-window encoder caching and suffix-logit
verification were not located in those inspected functions. This finding does
not rule out internal vLLM caching; that backend was not executed or exhaustively
audited. The [upstream README's API section](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/README.md#L350)
also says the demo settings are not a complete paper reproduction recipe.

## Client/server, VAD and timing hazards

[`ws_client.py:39–54`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/ws_client.py#L39)
sends int16 frame bytes and EOS; the final short frame gets 500 ms of zeros.
There is no pacing sleep in that send loop. A frame representing 160 ms of audio
is not evidence that the client transmitted in real time. Supplied sample-rate
and channel metadata must match the server's assumptions.

[`ws_server.py:595–625`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/ws_server.py#L595)
waits for initial extra audio. **Line 623 uses `if True or use_vad`: VAD runs on
that route regardless of the requested flag.** The client default is disabled,
so flag propagation cannot be assumed. The v1 route separately handles rolling
decodes and endpoints around
[1053–1149](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/ws_server.py#L1053).
`asr_cost_ms`, `total_cost_ms` and receive-time lag are distinct fields; none
measures an actual projected scripture card. VAD detects activity, not the target
speaker, and must not erase the competing-preacher control.

## Qwen BASE API, not trained R2T2 behavior

[`qwen_asr/inference/qwen3_asr.py:584–636`](https://github.com/QwenLM/Qwen3-ASR/blob/7c6daf77a2421100f5fb066495372c00129d39ff/qwen_asr/inference/qwen3_asr.py#L584)
provides context/language and chunk/rollback settings. Streaming rejects a
non-vLLM backend at lines 625–626. Lines
[719–765](https://github.com/QwenLM/Qwen3-ASR/blob/7c6daf77a2421100f5fb066495372c00129d39ff/qwen_asr/inference/qwen3_asr.py#L719)
accumulate all audio, roll back model tokenizer IDs, regenerate, and return the
current state. This is revisable base-model decoding, not learned Wait/LSP.
The [official streaming example](https://github.com/QwenLM/Qwen3-ASR/blob/7c6daf77a2421100f5fb066495372c00129d39ff/examples/example_qwen3_asr_vllm_streaming.py#L35)
illustrates that API. An independent MLX cumulative-prefix decoder may supply
hypotheses to our wrapper, but that alternative has not run in this session.

The official [Qwen base model card](https://huggingface.co/Qwen/Qwen3-ASR-1.7B)
marks Apache-2.0. Locally found checkpoints are English-vocabulary-pruned
Qwen-derived BF16/4-bit variants with recorded hashes; they are not byte-identical
full-vocabulary official checkpoints. Safetensors is a container, not proof that
MLX-packed quantized tensors load in another backend. No MPS/Metal/CPU inference
compatibility, peak runtime memory or throughput is claimed from file inspection.

## Licence boundary and restricted-output non-transfer

[`MODEL_LICENSE:33`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/MODEL_LICENSE#L33)
is the exact **§3.4(c)** location, verified unchanged at blob `7fbd11c1…`.
Its operative excerpt is **“or any Derivative Work to improve any AI model”**.
The clause's exceptions are R2T2 itself, its derivatives and non-commercial
models. Definitions at lines 9–14 include outputs/derivatives and a broad range
of uses; the model definition also mentions final code. The
[README licence section](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/README.md#L564)
separately identifies Apache-2.0 code and the model-use agreement. Apache code
labelling does not cancel the separate restrictions. This study follows the
user's stricter boundary: **no R2T2 weights or outputs, no distillation or trained
parameter transfer**, and no R2T2 implementation copied into the new wrapper.

The [published comparison](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/README.md#L119)
uses eight English WER sets and five Chinese CER sets, equally weighted. **5.76%**
at 160 ms/U=1, base **21.01%**, and full-context **5.15%** are that upstream macro
comparison; no value is RhemaFlow church WER. Reading summary evaluation figures
is not using R2T2-generated transcripts as training/evaluation inputs here.

## Independent hypotheses and decisions

| Hypothesis | Honest measurement / present status |
|---|---|
| Two-update agreement reduces visible revisions | Mechanism confirmed on authored traces; it can freeze errors. Measure full committed WER and rejection coverage too. |
| Holding a suffix improves the accuracy/lag tradeoff | Word-budget and model-token-budget modes are separate. Authored traces show latency and error tradeoffs; real Qwen comparison is `NOT_RUN`. |
| A stable-text policy prevents wrong-speaker cards | **Rejected as a sufficient mechanism:** stable other-speaker text still commits; CTRL03 stays a known wrong-card failure. |
| Smaller chunks meet an end-to-end latency target | Requires actual load/decode/capture/matcher timing and device measurements. Paper audio-time lag cannot establish it. |
| Less decoding means less energy | Requires measured energy with a stated baseline; no joule figure exists here. Wrapper CPU microseconds are not model power. |

Only a research adapter and collection/scoring contract are offered. Personal's
live `qwen:b` route, its historical switching loop and an actual Personal consumer
were **not exercised**. Q4 default/Tiny fallback, PBFDAF integration and products
remain unchanged. `RESEARCH_GO` · `BLOCKED_GOLD` · `PRODUCTION_NO_GO`.
