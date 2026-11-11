# R2T2_CODE_AUDIT — sources, algorithm, licences, feasibility

Audit time 2026-11-11, read-only. Every file below was fetched from the public GitHub repository and its
**git blob id recomputed locally** (`sha1("blob <len>\0"+content)`) so the revision is verifiable, not assumed.

## 1. Repository state (verified)

| Item | Value |
|---|---|
| Repository | `https://github.com/netease-youdao/Confucius4-R2T2` |
| Default branch | `master` |
| HEAD commit | **`72b81be7070095410b75ed2e11998e347f655218`** (2026-11-06, "Technical report published") |
| Files | 48 blobs at HEAD |
| Code licence | `LICENSE` = **Apache-2.0** (blob `6343ce6d9bb3…`) |
| Model licence | `MODEL_LICENSE` = NetEase Youdao Model Use License (blob `7fbd11c16918…`), §3.4(c) restriction |

## 2. Files actually retrieved and verified

| Path | Lines | Blob SHA-1 (computed) | What was read |
|---|---:|---|---|
| `r2t2/r2t2_asr.py` | 880 | `9967217b2627…` | `ASRStreamingState`, `streaming_transcribe`, chunk/rollback/prefix logic, flush |
| `example.py` | 244 | `d7568d76090c…` | public entry point, backend selection, arguments |
| `MODEL_LICENSE` | 61 | `7fbd11c16918…` | §3.4(c) commercial-improvement restriction |
| `LICENSE` | 193 | `6343ce6d9bb3…` | Apache-2.0 |
| `README.md` | 579 | `4fe4920d6a5f…` | LSP training description, backends, published numbers |
| `r2t2_llama/README.md` | 137 | `d7568d76…` | llama.cpp/GGUF route |
| `run_example.sh` | 169 | `82540f13ec62…` | invocation example |

`r2t2/r2t2_asr.py` is **byte-identical** to the version audited in the previous round (same blob id), so the
algorithm notes below are unchanged and re-verified.

## 3. Algorithm summary (observed in code, not claimed as ours)

* `ASRStreamingState`: `chunk_size_sec` (default 2.0), `unfixed_chunk_num` (default 2), `unfixed_token_num`
  (default 5), `chunk_id`, buffered PCM, `last_fixed_text`.
* Each update re-feeds **accumulated audio** (`state.prompt_raw + prefix`) — the model is not cache-aware; the
  "streaming" is repeated full-context decoding with a prompt.
* Prefix rollback: for `chunk_id < unfixed_chunk_num` the prefix is empty; afterwards the previous text is decoded,
  the last `unfixed_token_num` tokens are dropped, and the remainder becomes the prompt. Committed text never
  reverts.
* End of stream: remaining buffer padded to a chunk and decoded once more (`flush`).
* `example.py` selects a backend; the Python streaming path is **vLLM-only**. A separate llama.cpp/GGUF route exists
  (README + `r2t2_llama`), but no Apple-Silicon result is reported upstream and none was run here.
* **Training code is not in the repository.** The 48 files contain no `train*`, `lsp*`, `sft*` or `grpo*` script.
  README §33 describes LSP training on 1,500 h with SFT + GRPO on the language decoder, audio encoder and projector
  frozen — i.e. the published gain depends on **trained weights we do not have and may not use commercially**.

## 4. The 5.76 % number — what it is, and what it is not

README §35 (verified text): at 160 ms with one provisional token R2T2 reaches **5.76 %**, versus **21.01 %** for the
base Qwen3-ASR at the same streaming setting and **5.15 %** full-context; the average is over **13 English and
Chinese test sets** (8 English WER + 5 Chinese CER, equal weight, macro). It is **not** the WER of our 648-clip
music/chatter set (Q4 26.306 %, Qwen MLX 24.387 %, Tiny.en 44.789 %) and must never be plotted as if comparable.

## 5. Licence gate

* Code: Apache-2.0 → reading and independent re-implementation of general ideas is permitted.
* Model: NetEase agreement, §3.4(c): *"You may not Use the … R2T2 or any Derivative Work to improve any AI model,
  except for the R2T2 itself, its Derivative Works, or non-commercial AI models."*
* Consequence for RhemaFlow: **no download, no inference, no distillation, no teaching on its outputs, no parameter
  transfer**. Nothing in this round touches R2T2 weights or outputs.
* This is an engineering reading, **not a legal opinion**; commercial use needs counsel.

## 6. Feasibility matrix

| Approach | Feasible now? | Why |
|---|---|---|
| R2T2 inference on M1 | **No / prohibited** | licence §3.4(c); weights not present; no vLLM on macOS |
| R2T2-style **heuristic** stable prefix (independent code) | **Yes** | implemented and tested in `scripts/stable_prefix.py` (20 tests) |
| Heuristic pseudo-streaming with **Qwen 1.7B MLX** | **Blocked by disk** (672 MiB free) | needs repeated full-context decodes; model is real (1.4 GB) |
| Q4 buffered windows (5/10/20 s) | **Blocked by disk** | window corpora + temp WAVs exceed the floor |
| Multi-mic / separation / diarisation | **Not available** | single-channel corpus, no separator, `--diarize` unsupported for Parakeet |
