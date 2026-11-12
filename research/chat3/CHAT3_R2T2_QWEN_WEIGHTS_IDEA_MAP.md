# Chat 3 — R2T2, Qwen and lawful weight-space idea map

**RESEARCH_GO · PRODUCTION_NO_GO. No new ASR inference, speaker-isolation result or <6% claim.**

## What this continuation verified

The starting research HEAD and its remote still match
`fd48afb76abb8f11a37b6a28ae9145c810d8b7a2`. Work uses the fresh isolated branch
`rhemaflow/research-chat3/under6-weight-space-20261112`. The unchanged baseline has
136 passing tests. Original research files are retained; new files add evaluation,
model-header analysis and research reports. No Personal/User/application code is
changed, no product is merged or deployed, and no model/audio is transferred.

R2T2 `master` still pins `72b81be7070095410b75ed2e11998e347f655218`; Qwen source
still pins `7c6daf77a2421100f5fb066495372c00129d39ff`. Twenty previously cached
text blobs were rehashed against their Git identities after confirming those
revisions. Twelve additional full/selected text records cover fine-tuning,
current NVIDIA native runtime documentation and GGML types. Exact URLs, hashes,
line counts and scope are in `data/under6_20261112/source_audit.json`. The earlier
`R2T2_DEEP_CODE_AUDIT.md` remains the detailed inherited execution trace; this is
an extension of that unchanged audit, not a claim of executing upstream models.

## Six separate mechanisms

| Mechanism | Source-backed idea | Plausible benefit | What it cannot establish | Next falsifiable test |
| --- | --- | --- | --- | --- |
| Streaming token stability | Commit only a stable prefix; track provisional suffix separately | Fewer visible revisions and repeated downstream work | Correct word, correct speaker or <6% WER | Frozen base-model hypotheses, committed WER + revision rate + lag |
| Noise robustness | Close-mic baseline, lawful augmentation and independently tested filtering | Lower target-speech corruption under room interference | Speaker ownership from energy/coherence alone | Paired target-only gold, music/chatter controls and retention |
| Diarization / target selection | Independently bind a diarized speaker to the enrolled/physically selected target | Reject other-preacher quotations | An anonymous speaker index is not the preacher's identity | Target absent, overlap, speaker handoff and remapping controls |
| ASR acoustics | Authorized base-model adaptation and matched preprocessing | Domain/accent/acoustic recognition improvements | Training cannot repair unobserved attribution by itself | Held-out church/speaker/session groups, unchanged normalization |
| Runtime efficiency | Cache completed work, bound contexts, measure batch-1 streaming | Lower repeated computation and resident memory | Chunk duration or vendor lag is not end-to-end M1 latency | Cold/warm decode, queue/capture/render timestamps, RTF/RSS/energy |
| Weight-space adaptation | LoRA/QLoRA or selective modules on permitted bases | Fewer trainable parameters; possible domain gains | A lower parameter count is not measured quality or peak memory | Freeze holdout first; rank/module ablation with regression gates |

## R2T2 architecture and execution boundaries

The [paper, sections 4–7](https://arxiv.org/html/2611.06043v1) describes a Qwen3-ASR
backbone retaining the audio encoder/projector while adapting the decoder with
stable-prefix supervision and a Wait action. The learned policy differs from a
host-side agreement heuristic. Its 5.76% aggregate mixes English WER and Chinese
CER; it is neither church WER nor an interchangeable accuracy target.

Pinned source trace:

- [Initial framing, `example.py:100`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/example.py#L100)
  and [`run_example.sh:36`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/run_example.sh#L36):
  the example adds initial audio buffering. Its nominal chunk size does not
  account for all delay.
- [State and prefix handling, `r2t2_asr.py:226`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2/r2t2_asr.py#L226)
  and [release logic at 380](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2/r2t2_asr.py#L380):
  accumulated audio, raw hypotheses and fixed text are distinct. Only fixed text
  belongs in an irreversible consumer.
- [Rolling context at 650](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2/r2t2_asr.py#L650)
  and [empty tail at 807](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2/r2t2_asr.py#L807):
  audit nondefault chunk bookkeeping and final suffix release independently.
- [`ws_server.py:623`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/ws_server.py#L623)
  unconditionally enters that VAD branch; [`ws_client.py:39`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/ws_client.py#L39)
  has an unpaced send loop. VAD detects activity, not target identity.
- [Processor/native bridge, `model.py:140`](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2_llama/model.py#L140)
  aligns processor windows. Decoder reset behavior is not proof of the paper's
  optimized cross-update cache policy or a demonstrated Apple runtime.

The independent existing `qwen_base_stream.py` uses a frozen base decoder
callback and past-only cumulative PCM. Its immutable prefix can freeze a wrong
word and commit another preacher. New adversarial suffix tests strengthen the
past-only boundary without claiming actual acoustic inference. No R2T2 weights,
logits, transcripts, generated pseudo-labels or trained parameters were obtained
or used. No R2T2 code was copied into the new evaluation/header tools.

The pinned [model-use clause 3.4(c)](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/MODEL_LICENSE#L33)
is a separate boundary from the code's Apache-2.0 license. This project follows
the owner's stricter exclusion of R2T2 weights/outputs as a commercial improvement
source. Independent written legal clearance would be needed to reconsider it;
this document provides no such clearance. Static algorithm study is not model
or output permission.

## Current NVIDIA source and runtime audit

NeMo Speech source pins `3d381ffad4a513885c97a48a577013ed805d88da`.
The official native [NeMo-Speech.cpp](https://github.com/NVIDIA/NeMo-Speech.cpp/blob/536b17a41bef62d2a67a40ed3df61df26a4389fe/README.md)
pins `536b17a41bef62d2a67a40ed3df61df26a4389fe`. Its
[build guide](https://github.com/NVIDIA/NeMo-Speech.cpp/blob/536b17a41bef62d2a67a40ed3df61df26a4389fe/docs/build.md#L68)
and [installer documentation](https://github.com/NVIDIA/NeMo-Speech.cpp/blob/536b17a41bef62d2a67a40ed3df61df26a4389fe/docs/install.md#L46)
explicitly describe Apple Silicon/Metal. This is source-documented platform
support, **not** an installed or measured M1 Pro result. No installer, build,
model pull, NIM or hosted API was run.

| Candidate | English suitability / mechanism | Current license evidence | M1 and adaptation limits |
| --- | --- | --- | --- |
| [Parakeet unified en 0.6B](https://huggingface.co/nvidia/parakeet-unified-en-0.6b) | English, unified offline/streaming RNNT; card describes buffered context recomputation | NVIDIA Open Model License; HF API metadata uses `other` | Native runtime's inspected supported-model list does not establish this exact checkpoint. Card says unified training pipeline not yet provided; no ready M1 fine-tuning claim |
| [TDT 0.6B v2](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2) | English; verified local Q4/Q8 GGUFs | CC-BY-4.0 card + embedded metadata | Existing model files, no current inference. Native v3 support is not automatic legacy-v2 loader compatibility |
| [TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) | Multilingual, includes English | CC-BY-4.0 card | Native [v3 route is full-utterance only](https://github.com/NVIDIA/NeMo-Speech.cpp/blob/536b17a41bef62d2a67a40ed3df61df26a4389fe/docs/asr/models.md#L52), rejects streaming requests; do not relabel an overlapping wrapper as cache-aware streaming |
| [CTC 1.1B](https://huggingface.co/nvidia/parakeet-ctc-1.1b) | English, CTC; native offline/buffered streaming | CC-BY-4.0 card | Native Apple/Metal route is a research candidate. CTC word boosting differs from acoustic fine-tuning; weights/decoder/LM still require separate permission and measurement |
| [Nemotron Speech Streaming en 0.6B](https://huggingface.co/nvidia/nemotron-speech-streaming-en-0.6b) | English, cache-aware RNNT | NVIDIA Open Model License | Native supported model; stronger next runtime candidate than assuming TDT v3 is streaming. No current installation, speed, RSS or power result |
| [Multitalker Parakeet streaming](https://huggingface.co/nvidia/multitalker-parakeet-streaming-0.6b-v1) | Uses external diarization activity and a model instance per speaker | NVIDIA Open Model License | Extra diarizer + per-speaker compute can exceed practical M1 budget. No enrollment requirement does not identify the owner-selected preacher |
| [Streaming Sortformer 4spk v2](https://huggingface.co/nvidia/diar_streaming_sortformer_4spk-v2) | Anonymous speaker activity/diarization, not transcription | CC-BY-4.0 card | Native runtime supports diarization, but target binding, right context and combined ASR latency need measurement. Card points to a newer 8-speaker model; it was not downloaded |

Exact model-card revisions and license metadata are recorded in
`official_model_card_pins.json`. Commercial and derivative use under the
[NVIDIA agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/)
remains subject to its terms, notices and separate components; source-code
Apache licensing does not replace checkpoint terms. This is a provenance audit,
not blanket legal approval. GPU/Linux NeMo/NIM instructions are distinct from
the native Apple route. No NVIDIA speed claim is an M1 measurement here.

NeMo has pinned [ASR adapter training examples](https://github.com/NVIDIA-NeMo/Speech/blob/3d381ffad4a513885c97a48a577013ed805d88da/examples/asr/asr_adapters/README.md)
and [fine-tuning code](https://github.com/NVIDIA-NeMo/Speech/blob/3d381ffad4a513885c97a48a577013ed805d88da/examples/asr/speech_to_text_finetune.py).
They do not prove every listed checkpoint supports every adapter, or that the
training stack works on this Mac. Qwen's pinned
[SFT script](https://github.com/QwenLM/Qwen3-ASR/blob/7c6daf77a2421100f5fb066495372c00129d39ff/finetuning/qwen3_asr_sft.py#L203)
loads an authorized base and exposes ordinary training arguments; the inspected
script has no built-in LoRA/QLoRA CLI or verified loader for these local pruned
packed MLX tensors.

## Bark and microphone-first comparison

[Bark at `f4f32d4…`](https://github.com/suno-ai/bark/blob/f4f32d4cd480dfec1c245d258174bc9bde3c2148/README.md#L19)
is text-to-audio generation, **not ASR or speaker separation**. A future approved
synthetic distractor experiment would need its checkpoint/license, prompts, seed,
output hashes and a synthetic label. It has not been installed or used, and it is
excluded from the ASR priority/accuracy ranking.

The first real comparison stays physical: preacher close/lapel-only, then raw
same-clock close+room, then independently enrolled/verified routing, then causal
separation/filtering, then ASR/model adaptation. Keep every stage's added delay,
wrong-speaker cards and target loss visible. Diarizer speaker 0 can change identity
at handoff; neither proximity, stable text nor a high scripture score proves the
preacher spoke. No new abstention rule was added because matched independent
retention evidence does not yet exist.

The old aligned scalar/FIR WER gains retain their future-sample defect. The truly
causal procedural PBFDAF study retained a negative SI-SDR result and a −9.743 dB
target-loss stress case. Neither is a deployable baseline improvement. The saved
CTRL03 Luke 1:17 card at confidence 0.833 remains a failed attribution gate.
