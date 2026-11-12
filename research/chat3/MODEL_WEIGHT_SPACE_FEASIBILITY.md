# Model weight-space feasibility — conditional research, not a trained model

**No training, model loading, checkpoint conversion, distillation or weight change occurred.**
The <6% real church corpus-WER objective is unmeasured and not guaranteed.

## Verified identities and analytical resource bounds

The local BF16 Safetensors header contains **1,760,441,984 stored parameter
elements** in 707 BF16 tensors: audio-tower prefix 317,477,504 and language-model
prefix 1,442,964,480. This is the local English-vocabulary-pruned checkpoint,
not a claim of bit identity to the full-vocabulary official base. Its weight file
is 3,520,970,548 bytes. Config, tokenizer-file set, pruning provenance and whole
weight hashes are frozen in the inventory. Tokenizer is vocab/merges/config/template,
not a nonexistent `tokenizer.json`; all three local Qwen variants share the
verified tokenizer-set digest.

Assuming two-byte weights, two-byte gradients, four-byte master weights and two
four-byte Adam moments, full training state is `16 × parameters` =
**28,167,071,744 bytes (26.23 GiB)**, before activations, workspaces, loader, OS or
swap. Decoder-group-only state is about 23.09 GB before those additions. Ordinary
full/decoder fine-tuning is therefore not a supported promise for a 16 GiB M1.
Alternative optimizer/sharding/precision choices change this estimate; no peak
memory was measured and no optimizer was allocated.

A proposed LoRA target is the Q/K/V/O attention projections in the language
layers: **112 matrices**. For each matrix of shape `[out,in]`, adapters add
`r × (in+out)` parameters. Rank 8 totals **3,211,264** trainable parameters;
rank 16 totals **6,422,528**. The same 16-byte train-state estimate is 51,380,224
and 102,760,448 bytes respectively. Those figures exclude the frozen base,
audio encoder, activations, dequantization, caches and checkpointing. They do
**not** establish that an ASR LoRA implementation fits or runs on this Mac.
See `qwen_weight_feasibility.json` and the header-only inventory script.

## Candidate experiments in a defensible order

| Branch | Proposed intervention | Required proof before execution | Main failure risk |
| --- | --- | --- | --- |
| Unchanged weights | Normalize audio consistently; independently fix tokenizer/runtime mismatches; predeclare domain vocabulary | Same raw fixtures, baseline/adapter hashes, no gold or verse conditioning | Apparent WER gain from changing normalization or supplying evaluation answers |
| Decoder LoRA | Frozen authorized Qwen base encoder/projector, Q/K/V/O rank 8 then rank 16 | Compatible differentiable ASR loader, exact modules/parameter count, small train-only sanity run, measured memory | Fluent biblical hallucinations, catastrophic forgetting, frozen-encoder acoustic mismatch |
| Quantized-base LoRA | Frozen quantized base with trainable adapters | Actual MLX/PyTorch kernel and gradient compatibility for this pruned ASR format | Packed MLX U32 weights are not interchangeable with NF4/other quantizers or a GGUF inference engine |
| Selective encoder/projector adaptation | Unfreeze an explicit small last-block subset after decoder baseline | Module names/shapes, acoustic-only ablation, optimizer-state budget, target/other labels | Worse noise or speaker retention; unexpected memory/precision growth |
| NeMo/Parakeet adapters | Supported adapter-capable modules on a permitted original checkpoint | Check exact model/head support in pinned examples; train from an authorized differentiable checkpoint, not directly from a GGUF filename | Decoder/vocabulary changes damage general English; no demonstrated M1 training stack |
| Distillation | Only separately authorized teachers/data/outputs | Written teacher-output permission and output provenance; zero R2T2 material | Restricted-teacher contamination, synthetic-label errors and leakage |
| Robustness mixtures | Consented target speech plus lawful music/chatter/reverb/codec/channel drift | Per-source rights and consent, independent target-only annotation, source-cluster split | More quoted-distractor hallucination; evaluation/training source overlap |

[LoRA](https://arxiv.org/abs/2106.09685) and
[QLoRA](https://arxiv.org/abs/2305.14314) motivate low-rank updates to frozen bases.
Their language-model results do not validate this ASR checkpoint, its quantizer,
Apple backend, noise robustness or speaker ownership. The official Qwen
[SFT script](https://github.com/QwenLM/Qwen3-ASR/blob/7c6daf77a2421100f5fb066495372c00129d39ff/finetuning/qwen3_asr_sft.py)
is not a ready-made LoRA/QLoRA-on-pruned-MLX recipe. NeMo
[adapters](https://github.com/NVIDIA-NeMo/Speech/blob/3d381ffad4a513885c97a48a577013ed805d88da/examples/asr/asr_adapters/README.md)
are model/module dependent, not blanket support for every Parakeet.

## Dataset, license and evaluation controls

Freeze original base and tokenizer hashes, a model-free evaluation contract and
an immutable real holdout before any training. Group all augmentations with the
same source; prevent church, session and **all audible speakers** from crossing
train/tune/holdout. Gold is literal independently transcribed target speech,
not a KJV verse reconstructed by matching. No held-out Bible reference, expected
verse, target-presence label or speaker identity enters the decoder request.
Training prompts use a vocabulary chosen without inspecting evaluation gold.

Each source needs consent, provenance and suitable commercial-training rights.
Recovered 40 KJV WAVs remain rights-pending and are not admitted to this stage.
Local Qwen derivative notices/redistribution provenance still require review;
Parakeet's CC-BY-4.0 metadata does not supply missing conversion notices. No
restricted R2T2 weight, logit, output, pseudo-label or derivative is permitted.
The current training-plan validator allows no teacher at all; an authorized
teacher experiment would need an explicitly revised, independently reviewed plan.

For every experiment log base/adapter/config/tokenizer/holdout hashes, seed,
trainable modules/parameters, optimizer, accumulation, steps, precision, runtime
revision, peak RSS/swap, disk/checkpoint budget and all negative results. Evaluate
base and candidate on the same frozen recordings; preserve general-English,
accent, music/lyric, other-preacher and no-target controls. Record corpus S/D/I/N,
paired cluster CIs, correct-card-event retention, false cards and full-pipeline
latency/power/dropouts. Better WER alone cannot pass the card gate.

## Execution routes and current decision

1. **This M1:** first establish inference, then an authorized tiny differentiable
   adapter smoke test with explicit memory/timeout limits. No inference runtime
   for these Qwen packed/pruned variants was verified in the active Python;
   `mlx`, `mlx_audio`, `qwen_asr` and `nemo` are absent. No environment was installed.
2. **CPU/Metal:** native NVIDIA inference support is a separate useful route;
   it is not a training API. CPU gradient training may be slow and still exceed
   RAM. No speed or energy estimate substitutes for measurement.
3. **Hosted authorized training:** a future separately approved budget/provider,
   data processing/region/consent agreement and permitted checkpoint could move
   training off the laptop. No provider was selected/provisioned, account
   contacted, data uploaded or payment authorized in this research task.

Fresh inventory had about **3.78 GiB free**, below the hard 8 GiB pilot floor and
15 GiB heavy-work target. No destructive cleanup or model download was performed.
Checkpoint/optimizer/data budgets must fit while keeping headroom, not merely
before starting. Current state: **BLOCKED_DISK, BLOCKED_RUNTIME, BLOCKED_RIGHTS,
BLOCKED_GOLD**. The next experiment is lawful paired baseline inference, not a
weight edit. Personal model replacement still needs a separate promotion gate.
