# Independent speaker-aware and causal study proposal

**Model-free analysis only; zero ASR/training runs; no candidate promoted.**

Start with physically selected preacher close/lapel audio and record room audio
on the same clock. Proximity is an intervention to measure, not a speaker-identity
certificate: another person can wear/use the lapel, voices can overlap, and an
anonymous diarizer label can swap at a handoff. Neither text stability nor a
high Bible matcher score establishes the target spoke.

| Paired ablation | Falsifiable question | Required failure controls |
| --- | --- | --- |
| Close-only baseline | Does the selected close channel retain the preacher accurately? | Target absent, room-only quotation, mic handoff, clipping, overlap |
| Raw same-clock close + room | Does the second channel add independent useful evidence? | Misalignment/drift, identical correlated inputs, music and near-zero target |
| Independently verified target binding | Can observations identify the intended preacher without using gold/speaker truth as a live label? | Unknown target, target absent, diarizer permutation, same verse by another speaker |
| Causal filtering/separation | Does interference reduction improve target words without target loss? | Future-suffix perturbation, gain/phase/delay changes, low target/interference ratio |
| Stable-prefix release | Does fixed commit policy reduce revisions at an acceptable measured lag? | Repeated phrases, stable wrong-speaker text, divergence, EOS, long utterance reset |

Freeze each stage before held-out evaluation and retain close-only/raw-dual-mic
comparisons on exactly matched bytes. A future speaker-binding experiment needs
separately authorised enrollment/reference audio and a verified compatible
classifier; none is installed or claimed here. Keep `unknown` attribution
explicit in research logs. Suppressing every card cannot pass: pair no-target
silence with correct target-card retention and abstention/latency denominators.
Even REVIEW cards on a target-absent clip are failures in the current safety gate.

The existing past-only callback and append-only host agreement heuristic remain
the independent starting point. Inspecting the pinned upstream
[R2T2 streaming state/release code](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/r2t2/r2t2_asr.py)
supports separating provisional hypotheses from irreversible released text.
That architectural observation does not reproduce its learned policy or confer
speaker correctness. Keep fixed holdback/agreement policies, actual token versus
word units, buffering, reset and EOS handling explicit. Do not tune on the pilot
or silently repair earlier committed text. Future suffixes must not affect an
already consumed PCM prefix or its previously committed output; count deliberate
buffering as latency rather than zero lookahead.

The pinned [Qwen README](https://github.com/QwenLM/Qwen3-ASR/blob/7c6daf77a2421100f5fb066495372c00129d39ff/README.md)
describes its streaming path through vLLM and automatic model-name downloads.
Neither is proof that the audited local packed/pruned MLX derivative loads on
this Mac. The current callback tests are not an installed decoder. Require the
actual approved local loader with downloads disabled before a real run.

R2T2's separate [model-use clause 3.4(c)](https://github.com/netease-youdao/Confucius4-R2T2/blob/72b81be7070095410b75ed2e11998e347f655218/MODEL_LICENSE#L33)
limits model-improvement uses. The owner's stricter rule remains: no restricted
weights, logits, transcripts, pseudo-labels, generated outputs or distillation
traces for this commercial research path. This continuation studies source text
and implements no upstream model code, learned policy or training recipe.

Preserve the negative evidence: the historical wrong Luke 1:17 card at 0.833 is
unresolved; prior aligned scalar/FIR gains included future-sample lookahead; the
causal PBFDAF study reduced SI-SDR and lost substantial target signal. These are
reasons to test held-out target retention, not evidence for enabling a filter.
Historical 24.387/26.306/44.789% counts are not new checkpoint-specific church WER.
The next real measurement is the gated three-file pilot, followed by consented
real dual-mic gold. `RESEARCH_GO · BLOCKED_GOLD · PRODUCTION_NO_GO`.
