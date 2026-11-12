# Chat 3 — causal PBFDAF research results

**2026-11-12 · Research only · Negative integration finding**

The causal PBFDAF is implemented and passes its mechanism checks. On a newly
frozen **procedural, wordless** holdout it gains **0.789 dB projected ΔSIR** but
**loses 1.008 dB SI-SDR versus close-only**. Target retention is −0.704 dB; an
identifiability stress case loses 9.743 dB. This is **not a validated enhancement
or speaker guard**. Do not integrate it. Keep close-only as the operational
baseline until independent real evidence supports a change.

The earlier **CTRL03 wrong Luke 1:17 card at confidence 0.833 remains a safety
failure**. Neither acoustic reproduction nor actual matcher execution was
possible. Saved detection replay preserves and counts the wrong speaker's card;
it does not claim a newly reproduced audio/ASR/matcher result.

## Source identity and preflight

| Item | Verified state |
|---|---|
| Public remote | `git@github.com:SolomonPhronesis/RhemaFlow.git` |
| Source handoff | `ec025bcbe1f7272a0c67025056148a95f5e30308`, exact `ls-remote` match |
| Older handoff | `2b35d064ac343411a2e37db1d072ba11d9c7bf4d` is an ancestor of `ec025bc…` |
| Isolated branch | `rhemaflow/research-chat3/codex-pbfdaf-20261112` |
| Frozen code/tune commit, before holdout generation | `d73ca9978ce1e81a581d34a8107f1b91acef3c26` |
| Frozen commit remote verification | `ls-remote` returned exactly `d73ca9978ce1e81a581d34a8107f1b91acef3c26` |
| Source hashes | All **90 entries** in the historical `SHA256SUMS.txt` match |
| Hardware | Apple M1 Pro, MacBookPro18,1, 16 GiB RAM, macOS 15.5 arm64 |
| Runtime | Python 3.14.5, NumPy 2.4.6; installed SciPy for signal synthesis |
| Storage / swap | Initially ~9.7 GiB free; context snapshot 8,893,997,056 free bytes; ~817 MiB swap used |

The named source ZIP was not available in the attachment/targeted Downloads and
workspace checks. The verified public repository supplied the research source.
The previous worktree and exact KJV gold/owner-source paths return macOS
`Operation not permitted`. No attempt was made to bypass those permissions.
No private Personal/User repository, model asset, recording, installation or
other worktree was opened or modified. No model was downloaded, trained or run.
No R2T2 weights or outputs were used. Prior provenance/licence assertions are
preserved, not newly verified permission for inaccessible audio.

The result commit is a descendant of the frozen commit. Its exact final HEAD and
remote equality are recorded in the separately generated **`PUSH_RECEIPT.json`**
delivered with this report; a commit cannot contain its own resulting hash.

## Tests and available evidence

The six unchanged suites pass **66/66**: causal 5, FIR 6, streaming 20, target gate
9, two-channel 6, WER 20. The new suites pass **27/27**: PBFDAF 18 and evidence/
coverage audit 9. **93/93 final total**. Before holdout generation **89/89** passed;
four downstream coverage tests were added afterward without changing the frozen
filter or study. Per-suite logs are in `data/pbfdaf_20261112/tests_before_holdout.json`
and `tests_final.json`.

New tests independently compare partitioned filtering with direct convolution;
mutate future input inside partial blocks and the initial calibration interval;
check irregular chunks, flush/truncation, causal long-echo convergence, target-only
preservation, finite impulsive/silent output, coefficient support and fixed
persistent array memory. Audit regressions preserve explicit target/other-speaker
labels, reject missing/duplicate expected IDs, and count no-target quotes as wrong
even if the quoted verse matches a text reference.

| Run or evidence | Status / limits |
|---|---|
| Original KJV/owner corpus generation and ASR rerun | `BLOCKED_FIXTURE`; source paths inaccessible |
| Saved WER arithmetic | Recomputed from stored edit counts, **not** transcripts or audio |
| Original per-clip WER bootstrap CIs | Preserved only; not independently recomputed without transcripts |
| CTRL03 audio and ASR | `BLOCKED_FIXTURE` |
| Actual original matcher | `BLOCKED_MATCHER`; executable/source not supplied in public research checkout |
| Saved CTRL03 detection and policy replay | Completed; still one wrong quote |
| New procedural DSP study | Completed; no spoken words, no ASR, no matcher |
| Qwen on processed audio | `NOT_RUN`; no approved usable fixture/model arm |
| Consented church gold / church WER | `BLOCKED_GOLD`; **no real church WER exists** |
| Physical `card_visible` / end-to-end latency | `NOT_MEASURED` |

## Earlier numbers: preserved, with a new leakage finding

Corpus WER is **Σ(S+D+I)/ΣN**, never an average of clip WERs. Empty target
references are excluded from that denominator and audited separately. Stored
S/D/I totals independently agree for close, scalar, FIR and FIR+DT. The saved
single-channel totals also reproduce Q4 26.305970%, Qwen 24.386994%, Tiny.en
44.789446%, and V3 26.305970%: **560 target clips, 15,008 words**, within a
648-clip matrix including controls. These are saved-count checks only.

| Evidence class | Historical arm | Clips / reference words | Edits | WER | Stored gain vs close, 95% CI (pp) |
|---|---|---:|---:|---:|---|
| `SAVED_SYNTHETIC` | close | 40 / 1,128 | 758 | 67.199% | — |
| `SAVED_SYNTHETIC_LOOKAHEAD` | scalar | 40 / 1,128 | 465 | 41.223% | +25.976 [17.37, 35.06] |
| `SAVED_SYNTHETIC_LOOKAHEAD` | FIR32 | 40 / 1,128 | 585 | 51.862% | +15.337 [7.57, 22.96] |
| `SAVED_SYNTHETIC_LOOKAHEAD` | FIR32+DT | 40 / 1,128 | 616 | 54.610% | +12.589 [5.21, 20.55] |

**The historical “strictly causal” label for these aligned filters fails a
stronger source-time test.** `fir_isolation.align(room, lag)` returns `room[lag:]`
for positive lag. At lag 48 it reads room sample `n+48` to form source-time output
`n`. In a deterministic counterexample, modifying room input from sample 16,079
changes scalar/FIR output starting at **16,031**, 48 samples earlier. Maximum
differences are 1.128 for scalar and 0.662 for FIR/FIR+DT. Tracking at 250 ms
chunks also fails (maximum 0.040). This is an algorithm counterexample, not a
reproduction of the recorded corpus. The historical code also estimates delay
from its first 400 ms before producing the earlier output: changing samples from
320 onward changes estimated lag 48→96 and changes output before 320 by 0.168.

The earlier tests leave a 160-sample margin, which hides the 48-sample advance;
they also do not test the calibration dependency. A system could explicitly
buffer and timestamp such alignment, but no zero-lookahead or end-to-end latency
claim follows from the saved implementation. Historical artifacts are untouched;
the arithmetic is preserved and the causal interpretation is corrected here.
The reported idealised 2.822% and oracle 2.542% remain historical, unreproduced,
non-product evidence. No R2T2 benchmark number is RhemaFlow performance.

## New PBFDAF and causal proof

`scripts/pbfdaf.py` implements constrained overlap-save adaptive filtering, 4–16
partitions and FFT 256/512 at 16 kHz. Blocks contain half the FFT length. The grid
covers 32–256 ms filter support; tune selected **FFT 256, 4 partitions, μ=0.4**,
or 512 taps / 32 ms. Longer support was available and was not selected.

For block `k`, the output is
`e_k = close_k − gain_k·IFFT(Σ_p W_k,p X_k−p)[B:2B]`. Each partition contains
`B` causal coefficients followed by `B` zero coefficients. The overlap-save
discard therefore leaves ordinary causal convolution: output sample `n` uses
room indices at most `n`. Coefficients and cancellation gain used for block `k`
were fixed by blocks before `k`. Gradient clipping, power normalisation, tap-norm
projection and all energy/coherence/double-talk decisions update only the next
block. Chunk boundaries do not reset state; flush appends only synthetic zeros
and returns exactly the remaining input length.

**Inference accepts only close and room sample arrays plus a frozen configuration.**
No target, interferer, true delay, TIR, speaker label, case ID, transcript or
future calibration sample is passed. Clean components exist only in synthesis
and offline scoring. Configuration selection sees tune positions only. There
is no room advancement or delay oracle. Learned causal taps can represent a
reference that arrives early; an unpredictable interferer that reaches the room
mic later cannot be perfectly cancelled without extra output delay. Motion and
drift must be followed by adaptation rather than silently using future samples.

Adaptation freezes for weak reference energy, insufficient room dominance,
close-energy surges or low estimated coherence. Past-error clipping and bounded
tap norm limit unstable updates. A past-block prediction-power budget controls
subsequent cancellation strength. **These are heuristic controls, not a proved
target-retention guarantee or speaker-attribution model.** The stress failure
below demonstrates that limitation.

The design uses standard partitioned overlap-save principles described by
[MathWorks](https://www.mathworks.com/help/dsp/ref/dsp.frequencydomainadaptivefilter-system-object.html).
[Valin and Collings](https://jmvalin.ca/papers/valin_icassp2007.pdf) discuss the
difficulty of double-talk control in MDF cancellation. This implementation is an
independent research mechanism, not a reproduction of their learning-rate
algorithm, and the room microphone differs from a clean far-end echo reference.

## Frozen procedural study — `MODEL_FREE_SYNTHETIC`

This new corpus contains **wordless procedural harmonic/coloured-noise signals**,
not the KJV WAVs, sermons, real people or independent church recordings. It uses
40–60-sample room lag, motion up to 12 samples, 120–200 ms diffuse reverberation,
5–7 dB target leakage attenuation, level drift, two interferer surrogates and
TIR 0/−5 dB. Each case is four seconds / 64,000 samples.

Positions 01–20 provide target-only mechanism sanity checks. Positions 21–30
provide 40 tune conditions for a fixed 12-configuration grid. The prespecified
objective is `mean ΔSIR + 2·min(0, mean retention + 1 dB)`. Code hashes, selection
and parameters were committed at `d73ca99…` **before holdout generation**.
Positions 31–40 then provide 40 conditions, scored once. Neither no-target
controls nor stress outcomes select parameters. No retuning followed the
negative holdout. The old corpus's case-number convention is reused; this does
not make the new procedural signals equivalent to those original fixtures.

All five arms have **40/40 expected keys, 100% sample coverage**, and 2,560,000
samples per arm. There are **zero reference words**; WER and transcript coverage
are **not applicable/unavailable**, not zero. The time-domain arms use causal
NLMS updates without calibration or alignment; FIR+DT uses a prior energy median.
They are newly audited variants, not reruns of the historical ASR arms.

All following results are `MODEL_FREE_SYNTHETIC`. Brackets are 95% percentile
intervals from **2,000 paired case-cluster resamples**, seed 20261112, over 10
case-position clusters containing the four source/TIR conditions. These quantify
this procedural study only, not uncertainty across real services or speakers.

| Arm | ΔSIR dB [95% CI] | Target retention dB [95% CI] | SI-SDR dB |
|---|---|---|---:|
| close | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | −1.567 |
| scalar, causal/no alignment | +0.032 [0.017, 0.049] | +0.026 [0.021, 0.032] | −1.572 |
| FIR32, causal/no alignment | +0.715 [0.625, 0.816] | −0.035 [−0.068, −0.003] | −1.247 |
| FIR32+DT, causal/no alignment | +0.587 [0.514, 0.669] | −0.034 [−0.059, −0.011] | −1.278 |
| **PBFDAF** | **+0.789 [0.704, 0.869]** | **−0.704 [−0.743, −0.666]** | **−2.575** |

PBFDAF minus FIR32 paired ΔSIR is **+0.073 [−0.023, +0.181] dB**, offering no
clear improvement on that measure. PBFDAF minus close paired SI-SDR is
**−1.008 [−1.068, −0.929] dB**; versus FIR32 it is
**−1.328 [−1.412, −1.228] dB**. Projected two-source SIR ignores unmodelled
residual distortion, so its small gain does not establish a better output. The
tune objective missed that tradeoff. A future objective change needs fresh
development fixtures and a new frozen holdout, not another pass on this one.

The 20 target-only sanity fixtures, with room target level below close level,
are preserved exactly. A separate same-input/different-speaker-label stress
case (`room=2·close`) suffers **−9.743 dB** target retention in its last second.
Without target identity information the canceller treats that correlated target
as removable material. Thus the benign clean check cannot establish safety.

## No-target-card audit

| Evidence class | Set | Findings |
|---|---|---|
| `SAVED_NEGATIVE_CONTROL` | Original 20 chatter + 8 silence | 418 ASR words, **1 wrong QUOTE**, 1 REVIEW, 26 NO_CARD; stored counts only |
| `SAVED_NEGATIVE_CONTROL` | CTRL03 stored detection | Other preacher, no target, **Luke 1:17 / 0.833**; audit still counts one wrong card |
| `MODEL_FREE` | CTRL03 confidence-rule replay | A 0.8 threshold retains the wrong card; no new threshold was fitted |
| `MODEL_FREE_SYNTHETIC` | New 20 other-signal + 8 silence controls | All 28 processed; other-signal residual RMS mean 0.069402; silence exactly zero |
| `NOT_RUN` | New controls through ASR/matcher | Word counts, emitted-card counts and correct-card retention **unknown/null** |

The frozen procedural controls are not the inaccessible original chatter clips.
The hard **zero emitted no-target cards** gate is **NOT EVALUATED / NOT PASSED**
for PBFDAF. The original failure remains failed. New correct-card retention is
unknown; the old FIR holdout's 19 correct cards cannot be credited to PBFDAF.
Neither output silence nor the absence of a matcher run is counted as safe card
behaviour. No blanket card suppression, case-specific exception or post-hoc
speaker rule was added.

## Throughput and bounded state

For a 60-second procedural stream on this M1 Pro, selected PBFDAF takes
**0.825 seconds**, RTF **0.01375**, and has **24,744 bytes** of persistent NumPy
array storage. FFT/Python temporaries and process RSS are not included in that
array count. Tests verify persistent arrays do not grow with stream length and
stay below 200 KB even for the largest tested configuration. Per-call output
storage scales with the caller's chunk; callers can use bounded chunks.

Dependency lookahead is zero. Full-block scheduling waits at most **127 samples
/ 7.9375 ms**, plus computation and host scheduling. This is **DSP buffering and
throughput only**; capture, ASR, matching, UI and end-to-end latency are unmeasured.
No live device/channel robustness claim follows from this run.

## Reproduction and next safe stage

From `research/chat3`, using already installed Python/NumPy/SciPy:

```bash
for t in tests/test_*.py; do python3 -B "$t"; done
python3 -B scripts/audit_pbfdaf_evidence.py --out /path/to/new-audit.json
python3 -B scripts/pbfdaf_study.py tune --out /path/to/new-study
python3 -B scripts/pbfdaf_study.py evaluate --out /path/to/new-study
python3 -B scripts/summarize_pbfdaf.py --run /path/to/new-study
```

Use a new directory: tune/evaluate refuse to overwrite a freeze/result, and
evaluation refuses changed frozen algorithm/study hashes. Timing is expected to
vary; deterministic signal metrics/configuration should reproduce. `run_context.json`,
the frozen configuration, detailed results, derived paired statistics, evidence
audit, tests and `REPRODUCIBILITY_MANIFEST.json` record source and evidence links.
The historical hash list and reports remain unchanged.

All remaining honest progress requiring real inputs is blocked on accessible,
eligible fixtures and consented gold. Follow `OPERATOR_KIT_PBFDAF_ADDENDUM.md`:
at least three consented, same-clock 48 kHz dual-mic services; independent human
target transcripts plus adjudication; no-target/overlap labels; genuinely
speaker-disjoint frozen evaluation. The addendum supersedes the old 2 pp
threshold with **≥5 pp paired real target-WER gain**, **zero additional wrong
cards**, **zero emitted no-target cards**, **≤5% lost correct cards**, measured
end-to-end latency and device/channel robustness. `<6%` requires frozen genuine
real-audio proof. Even a future research pass requires explicit product approval.

Only research files on this isolated branch were committed/pushed. No merge,
release, deployment, product edit, installation or model replacement occurred.

**`PUSH_VERIFIED` · `RESEARCH_GO` · `BLOCKED_FIXTURE` · `BLOCKED_GOLD` · `PRODUCTION_NO_GO`**
