# CODEX_CHAT3_START_HERE — first message for the new research chat

You are continuing **RhemaFlow Chat 3 research** (noisy-sermon / target-speaker isolation). Read
`HANDOFF_CHAT3_FOR_CODEX.md` in this directory first. Research only: no merges, installs, releases, model
replacements, or edits to User/Personal sources.

## State you can trust (verify, don't assume)

* Repository `git@github.com:SolomonPhronesis/RhemaFlow.git`, branch
  `rhemaflow/research-chat3/real-speaker-validation-20261111`, HEAD **`2b35d064ac343411a2e37db1d072ba11d9c7bf4d`**
  (= remote), research commit `f609e8f`.
* Worktree `chat3_scorer_wt` was clean at handoff.
* Model-free suite: **66 tests** (scorer 20, streaming 20, target-gate 9, two-channel 6, causal 5, FIR 6).
* Frozen single-channel baseline (648 clips, 560 target, 15,008 words): Q4 **26.306 %**, Qwen 1.7B **24.387 %**,
  Tiny.en **44.789 %**, V3/V4 **26.306 %**.
* Realistic two-channel holdout (40 clips, 1,128 words, reverb/motion/drift): close **67.199 %**, scalar
  **41.223 %**, FIR **51.862 %**, FIR+double-talk **54.610 %**. Idealised causal 2.822 %, oracle 2.542 % —
  **neither is deployable**.
* Hard safety failure: `CTRL03` no-target clip produced a wrong `QUOTE Luke 1:17` (confidence 0.833). Zero wrong
  cards is **not** achieved.

## Model routing

| Work | Model tier | Why |
|---|---|---|
| Filter design (PBFDAF, double-talk), leakage audits, safety-gate decisions, interpreting contradictory results | **Extra High** | hard algorithm and judgement calls |
| Routine metric runs, test execution, data wrangling, plot/CSV generation, doc updates | **Medium/High** | mechanical, well-specified |
| Any production/merge/deploy request | **stop** | out of scope for research |

## First five actions (do these now)

1. `git -C <worktree> status --porcelain=v1` and `git ls-remote --heads origin`; confirm the HEAD above.
2. `cd research/chat3 && for t in tests/test_*.py; do python3 "$t"; done` — expect 66/66.
3. Re-read `RESULTS.md`, `FORENSIC_WRONG_CARD.md`, `ADAPTIVE_FIR_RESULTS.md`, `FILTER_ADVANCE.md`.
4. Rebuild the realistic corpus (`python3 scripts/fir_isolation.py`, needs the 40 KJV WAVs + owner sources) and
   confirm the holdout table with `python3 scripts/score_fir.py`.
5. Open a new branch `rhemaflow/research-chat3/codex-<topic>-20261112` from the verified HEAD; never reuse another
   chat's worktree.

## Your actual goal

Decide whether a **practical causal, real-time, target-speaker enhancement** can beat the **close-mic-only**
baseline on **independent real church audio**. Until real recordings exist you may only do model-free work and
synthetic studies — and must label them `SYNTHETIC_*`.

Concrete backlog, in order:

1. **PBFDAF** (4–16 partitions, FFT 256–512) with a double-talk gate, tuned on the tune split (21–30) only.
2. Re-run 20 chatter-only + 8 silence controls through it; **acceptance = 0 wrong cards, 0 emitted cards**.
3. Compare to scalar NLMS and close-only on the frozen holdout with paired bootstrap CIs.
4. Only then, with real dual-mic audio: lapel-only baseline, then room-mic variants.
5. Keep `card_visible` and church WER `NOT_MEASURED` / `BLOCKED_GOLD` until actually observed.

## Decision gates (non-negotiable)

* ≥ 5 pp paired target-WER improvement **on independent real audio** vs close-only.
* No additional wrong cards; ≤ 5 % loss of correct cards.
* Measured end-to-end latency; no GUI/visible-card claim without observation.
* `<6 %` only if proven on a frozen genuine corpus; never from the oracle or idealised synthetic result.
* R2T2 weights/outputs must not be used (licence §3.4(c)); its 5.76 % is a different bilingual benchmark.

## What to ask the user for

1. Three consented services with simultaneous lapel + room mics on one clock (see `OPERATOR_KIT.md`).
2. Two independent human transcribers for the target preacher, plus adjudication.
3. A supervised session for physical `card_visible`, if a candidate build exists.
4. Disk headroom confirmation (≥ 8 GiB, ideally 15–20 GiB) before any sweep.

Report `PUSH_VERIFIED` / `BLOCKED_PUSH`, `RESEARCH_GO` / `BLOCKED_GOLD`, and always `PRODUCTION_NO_GO` until the
real-audio gates pass. Never invent a real-recording result.
