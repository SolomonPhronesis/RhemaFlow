# RhemaFlow — Implementation Plan

> **Companion to [`PRD.md`](PRD.md) (v2.1).** The PRD says *what* and *why*; this document says
> *in what order, in what units, and gated on what*.
>
> Baseline for every slice below: **RhemaFlow-D v0.801.2**
> (`Desktop M1 app/RhemaFlow-D-v0.801.2.zip`).

---

## §0. Baseline Reconciliation — read this first

The plan is only as good as its starting point, so here is the honest starting point.

### 0.1 What actually exists in v0.801.2

| Fact | Value |
|---|---|
| Version | **v0.801.2** (workspace version, `theme.rs`, README all agree) |
| Layout | Cargo workspace, 4 crates: `rf-bible`, `rf-core`, `rf-asr`, `rf-app` |
| Binary | `rhemaflow-d` |
| UI | `egui`/`eframe` **`=0.28.1`** (pinned) |
| Audio | `cpal` **`=0.15.3`** (pinned) |
| ASR | `whisper-rs` **`=0.13.2`** (`default-features = false`) → whisper.cpp |
| Model | `models/ggml-tiny.en.bin`, **77 MB**, English-only |
| Other deps | `hound` 3.5, `crossbeam-channel` 0.5, `serde`, `serde_json`, `anyhow` |
| Edition / licence | 2021 / MIT |
| **Tests** | **64 green** — rf-core 43, rf-bible 9, rf-asr 8, tts 4 |
| Bible text | `kjv.json` (31,102 verses) + `bbe.json`, both embedded, build-validated |
| Fonts | `LiberationSerif-Regular.ttf`, `LiberationSerif-Bold.ttf` |
| Recording | 16 kHz mono WAV, **~115 MB/h** |
| Storage | `~/RhemaFlow-Services/<timestamp>/` → `audio.wav`, `transcript.txt`, `events.jsonl`, `index.md` |
| Settings | `~/.rhemaflow/settings.json` |
| Installer | `./run.sh` — installs toolchain, **downloads the model**, builds, launches |

### 0.2 Where the PRD is stale — corrections applied in this plan

| PRD claim | Reality in v0.801.2 | Action |
|---|---|---|
| §25 "M0 — shipped (this is **v0.813.0** today)" | Version is **v0.801.2** | Corrected here; **slice X4** makes version-sync mechanical |
| Appendix A "**47/47** regression tests green" | **64/64** (README and `ACCURACY.md` both say 64; only `TESTING.md` still says 47) | Corrected here; **A0** re-runs the suite and records the number |
| Appendix A code evidence: `src/engine.rs`, `src/session.rs`, `src/asr.rs`, `src/rec.rs` | **Those paths do not exist.** Real paths are `crates/rf-core/src/parser.rs`, `crates/rf-core/src/commands.rs`, `crates/rf-app/src/actions.rs`, `crates/rf-asr/src/*.rs`, `crates/rf-app/src/recorder.rs` | Corrected here; **A0** rewrites Appendix A with verified paths |
| §6.2 Quotation recognition — "planned" | **Shipped** (leading n-gram match → confirm queue) | Promoted to shipped |
| §6.3 Context understanding — "partially shipped" | **Shipped** — bare "verse 17" *and* "that verse" resolve | Promoted to shipped |
| §6.4 Translation — "KJV shipped; dropdown in M1" | **Shipped** — KJV + **BBE**, plus a `from_translation()` framework API | Promoted to shipped |
| §7.4 "Three things" — "planned" | **Shipped** — enumerated pattern → operator-approved stage card | Promoted to shipped |
| §8 Operator command centre — "partial" | **Shipped** — transcript, stage preview, review queue, index, metrics on one screen | Promoted to shipped |
| §11 Recording "~300 MB/h" | **~115 MB/h** — comfortably inside budget | Corrected here |
| §23 installer "≤ 100 MB zip" | Zip is **73 MB** — passes | Held |

### 0.3 Features that ship today but appear nowhere in the PRD

These need PRD sections written, or they will be lost in the next refactor.

| Feature | Where it lives | PRD gap |
|---|---|---|
| **TTS read-aloud** — voice picker (★ natural, gender), rate, auto-read, "Read it" / "Stop reading" | `rf-app/src/tts.rs` (4 tests) | **No PRD section at all** |
| **Voice command grammar** — nav, zoom, fullscreen, clear, last scripture, read/stop | `rf-core/src/commands.rs` (11 tests) | §6.3 covers only references |
| **Scripture-vs-command guard** — "next is John 3" stages John 3 | `commands.rs` | §6.3 |
| **Simulator** — typed utterances through the real pipeline | `rf-app` | Not mentioned |
| **`--demo` / `--no-asr` / `--voices` / `--church`** CLI modes | `main.rs` | Not mentioned |
| **HEARD → RESULT strip** | `ui.rs` | Not mentioned |
| **Stage zoom** (A−/A+/1:1 + voice + persisted) | `ui.rs`, `stage.rs` | Not mentioned |
| **BBE translation** + `from_translation()` framework | `rf-bible/src/lib.rs` (9 tests) | §6.4 undersells it |
| **`index.md`** human-readable sermon index | `actions.rs` | §7.2 mentions only events |
| **`run.sh`** one-command bootstrap | repo root | Not mentioned |
| **Pluggable ASR engine trait** | `rf-asr/src/engines.rs` | Not mentioned |

### 0.4 The one architectural gap

**There is no database.** Settings are a JSON file; the scripture index is JSONL + Markdown.
This is not a defect — the flat-file artefacts are already church-portable and human-readable,
which is exactly what §21 wants. But it means the **SQLite + FTS5 decision (PRD §33 D-2) is
additive, not a replacement**, and it needs a real migration slice (**B2**) rather than an
assumption.

**Rule for B2:** SQLite becomes the *query and archive* store. The flat-file artefacts stay.
`events.jsonl` / `index.md` / `transcript.txt` / `audio.wav` remain the durable, portable,
inspectable record — a church can still read its archive with the app uninstalled.

---

## §1. How to Read a Slice

A **slice** is the smallest unit of work that can be finished, demonstrated and gated alone.

1. **Every slice ships something visible or measurable.** No slice is "refactoring".
2. **Every slice has an exit gate.** No gate = not a slice.
3. **No slice breaks a PRD §23 budget.** A slice that does is a failed slice even if it works.
4. **No slice regresses Appendix B or the 64 locked tests.** Any regression is **GATE: RED**.
5. **Dependencies are stated.** No slice assumes unfinished work.

**Ordering principle: design system → architecture → features.** Visual language before
components; data, identity and storage contracts before features that depend on them.

**Status legend:** `DONE` · `PARTIAL` · `TODO`

---

## §2. Architecture Decisions (as they stand)

Full rationale in PRD §33. Summary of what the plan builds on:

| # | Decision | Status in v0.801.2 |
|---|---|---|
| D-1 | Rust 2021 + egui/eframe 0.28.1 + cpal 0.15.3 + whisper-rs | **DONE** — pinned exactly as specified |
| D-2 | SQLite (`rusqlite`, bundled) + FTS5 | **TODO** — no database exists yet |
| D-3 | No authentication at runtime | **DONE by omission** — no login, no accounts |
| D-4 | Local filesystem only | **DONE** — `~/RhemaFlow-Services/` |
| D-5 | Signed/notarized `.app`, Apple Silicon | **TODO** — `run.sh` only |
| D-6 | Zero network in M0–M2 | **DONE with one exception** — `run.sh` downloads the model on first run. Install-time only, never service-time. Must be documented as the single sanctioned exception |
| D-7 | Rust for all core logic | **DONE** — whisper.cpp is the one C++ core, reached via bindings and documented deliberately in `README.md` |

**Added by this plan:**

| # | Decision | Rationale |
|---|---|---|
| D-8 | **Flat-file artefacts stay authoritative; SQLite is a queryable index over them** | Preserves §21 portability and the existing `index.md` / `events.jsonl` value. A church must be able to read its archive without the app. |
| D-9 | **Design tokens are named by role, not appearance** | `theme.rs` currently uses `GOLD` / `GREEN` / `RED`. Roles (`accent`, `status.ok`, `stage.verse_text`) are what let a light theme and stage presets exist without touching components. |

---

## §3. Phase A — Foundations

### A0 · Import and verify the v0.801.2 baseline — `TODO`

**Goal.** Make this repository the single source of truth and replace the PRD's guessed
inventory with verified fact.

**Deliverables**
* Import `Cargo.toml`, `Cargo.lock`, `crates/`, `data`→`crates/rf-bible/assets/`, `models/`,
  `run.sh`, `TESTING.md`, and the `docs/` set into the repo.
  `models/*.bin` and `target/` stay untracked (already in `.gitignore`).
* Re-run `cargo test --workspace` on the M1 and **record the real count** (expect 64).
* Rewrite **Appendix A** of `PRD.md` with verified paths — every row gets a real file path
  or is downgraded to "unverified".
* Add the §0.3 features to the PRD as proper sections.
* Fix the version string: one version everywhere (currently v0.801.2 in code, v0.813.0 in PRD).

**Gate.** `cargo test --workspace` green on a clean clone; every Appendix A row evidenced by a
path that exists; `grep -r` for the version returns one value.

**Depends on.** Nothing. **This slice unblocks everything else.**

### A1 · Design system — role tokens and the light theme — `PARTIAL`

**What exists.** `rf-app/src/theme.rs` is a real, deliberate design system: *Cathedral Dark*,
11 colour constants, an `apply()` that configures egui's `Style`, and a `stage_font_size()`
auto-fit function. `docs/UIUX-PROCESS.md` documents the reasoning and
`docs/DESIGN.html` records the alternatives considered.

**What is missing**
* Colours are named by **appearance** (`GOLD`, `GREEN`, `RED`, `BLUE`), not **role**. A second
  theme is impossible without editing every call site.
* **Dark only.** `UIUX-PROCESS.md` §4 already lists "stage theme presets (light
  projector-max for bright sanctuaries)" as next design work — bright sanctuaries are a real
  installation class, not a nicety.
* Spacing and radius are set inline (`Rounding::same(6.0)`, `Vec2::new(8.0, 6.0)`) rather than
  expressed as a scale.

**Deliverables**
* Rename to role tokens: `accent`, `stage.background`, `stage.verse_text`, `stage.reference`,
  `operator.surface`, `operator.surface_raised`, `status.ok`, `status.warn`, `status.error`,
  `status.listening`, `text.primary`, `text.muted`, `border`. Keep the existing hex values as
  the dark palette so **nothing looks different** after the rename.
* Add a **light** operator palette and a **projector-max** stage palette.
* Extract spacing/radius into named scales.
* Keep `stage_font_size()` — it is good; add tests for its boundaries.

**Gate.** A token reference screen renders every role in all three palettes; no component
references a raw hex or a colour-by-appearance name; the dark palette is pixel-identical to
v0.801.2.

**Depends on.** A0.

### A2 · Design system — components and accessibility — `TODO`

**What exists.** The three-zone operator layout, the review queue, the HEARD → RESULT strip,
the stage preview, the index table and the transport row are all real and documented.

**Deliverables**
* Extract the ad-hoc widgets in `ui.rs` (41 KB) into named components:
  `StageView`, `TranscriptFeed`, `CandidateCard`, `ScriptureIndexRow`, `StatusRail`,
  `RecordingIndicator`, `InterpretationStrip`, `TransportBar`.
* **Accessibility pass** — already listed as `IDEAS-100` #99: contrast audit against WCAG AA,
  reduced-motion mode for the 350 ms fades, VoiceOver labels.
  `UIUX-PROCESS.md` §4 lists it too.
* Formalise the **keyboard map** (N/P/M/B/R/F/H/Esc) as a tested table, not scattered handlers.

**Gate.** Every component renders in all three palettes at three window sizes; contrast
ratios recorded; reduced-motion honoured; `StatusRail` alone answers the PRD §8 ten-second
question.

**Depends on.** A1.

---

## §4. Phase B — Architecture

### B1 · Workspace boundaries — `DONE` (formalise)

**What exists.** The workspace is already correct and the key rule is already honoured:
`rf-core` is pure logic with **no I/O**, depending only on `rf-bible`. `rf-asr` owns capture.
`rf-app` owns UI. `docs/ACCURACY.md` §4 maps changes to code sites by crate.

**Deliverables**
* Write the boundary rule down in the repo (it currently lives only in `lib.rs` doc comments).
* Add a CI check that `rf-core` gains no dependency beyond `rf-bible` + `std`.

**Gate.** A dependency change to `rf-core` fails CI.

**Depends on.** A0. **Effort: small — this is mostly already done.**

### B2 · Persistence — SQLite + FTS5 over the flat-file record — `TODO`

**Goal.** Implement D-2 and D-8: add a queryable archive store **without** displacing the
portable artefacts.

**Deliverables**
* `rusqlite` with `bundled`; WAL mode; foreign keys on.
* Migration runner over `schema_migrations`; forward-only and additive.
* **Import path:** on first run (and on demand), index every existing
  `~/RhemaFlow-Services/<timestamp>/` folder into SQLite by reading its `events.jsonl` and
  `manifest` data. Existing archives become searchable without being rewritten.
* Tables per PRD §33.3 — `sermons`, `sermon_events`, `scripture_index`,
  `transcript_segments`, `edits`, `settings`, `translations`, `styles`, `templates`.
* FTS5 over `scripture_index`, `transcript_segments` and sermon metadata.
* **Artefacts remain authoritative** (D-8). If the DB is deleted, it rebuilds from the folders.
  This is the acceptance test.
* Settings migrate from `~/.rhemaflow/settings.json` into `settings`, with the JSON kept as a
  fallback for one release.

**Gate.** Delete `rhemaflow.db` → full rebuild from the service folders with no data loss and
identical search results. A pre-existing v0.801.2 archive indexes correctly on first launch.

**Depends on.** A0. **This is the highest-risk slice in the plan.**

### B3 · Local identity and roles — `TODO`

**Goal.** Implement D-3 without building an account system.

**Deliverables**
* **No login.** The app still opens straight into the command centre.
* A **role enum** (`Administrator`, `Operator`, `Speaker`, `Viewer`) in config and the UI
  permission model, **not enforced** in M0–M2. Defining it now means M3 adds enforcement, not
  redesign.
* **Optional local passcode** for church-wide settings (retention, deletion, sharing defaults) —
  salted hash, never plaintext.
* macOS Keychain reserved for future secrets; no secret in the DB.
* On the settings surface: *"RhemaFlow runs entirely on this machine. Nothing about your
  services leaves it."*

**Gate.** No network code exists; no credential stored outside the Keychain path; the role
model is unit-tested as data even though it is not enforced.

**Depends on.** B2.

### B4 · Storage layer consolidation — `PARTIAL`

**What exists.** `~/RhemaFlow-Services/<timestamp>/` with `audio.wav`, `transcript.txt`,
`events.jsonl`, `index.md`; settings at `~/.rhemaflow/settings.json`; `recorder.rs` writes WAV.
Paths are constructed in more than one place.

**Deliverables**
* One `storage` module as the **sole** owner of path construction. No ad-hoc `PathBuf` joins.
* **User-selectable library root** so an archive can live on an external drive — currently
  hard-coded to `$HOME`.
* **Retention policy** with a dry-run preview before anything is deleted.
* **Free-space pre-check at recording start.** At 115 MB/h a 2-hour service is ~230 MB; a full
  disk must produce an honest stop, not a truncated file.
* Startup check that the configured root is reachable — *before* the service, never during.

**Gate.** Recording survives a simulated full disk with an honest error; retention dry-run
matches actual deletion; moving the library root migrates cleanly or refuses clearly.

**Depends on.** A0.

### B5 · Session state machine and canonical event log — `PARTIAL`

**What exists.** `state.rs` holds `StageContent`, `TranscriptLine`, `ScriptureIndexEntry`,
`ServiceEvent`, `QueuedDetection`, `QueuedError`. `events.jsonl` is already written per event.
`ScriptureIndexEntry.source` already records provenance (`voice | confirm | manual | nav |
quotation`) — which is exactly what PRD §7.2's acceptance criterion needs.

**Deliverables**
* An explicit session state machine: `Idle → Armed → Listening → Staged → Recording → Ended`.
  Today the lifecycle is implicit in `app.rs`.
* Promote `events.jsonl` to the **canonical** log; the DB is a projection of it (B2).
* **Deterministic replay:** a recorded session replays through the parser offline and
  reproduces every decision. This is how parser regressions get diagnosed.
* All PRD §24 metrics derive from this log.

**Gate.** Replaying a captured session reproduces the same stage sequence and the same §7.2
index, timestamp for timestamp.

**Depends on.** B2.

### B6 · Translation registry with licence gates — `PARTIAL`

**What exists.** KJV + BBE embedded; `from_translation()` validates any public-domain
translation in the same schema; `TRANSLATIONS` is exported from `rf-core`; licensed requests
(NIV/AMPC) are recorded honestly and fall back to KJV. Parsing stays KJV-canonical so BBE's
versification differences cannot break detection — a genuinely subtle call, already made right.

**Deliverables**
* A `translations` table where a translation **cannot be enabled** unless `license` and
  `license_reviewed_at` are populated. KJV and BBE ship enabled.
* Move `TRANSLATIONS` out of `rf-core` into the registry, so adding a translation is a **data**
  task, not a code change.
* Per-service override and explicit-request routing through the registry.

**Gate.** A translation with an empty licence record cannot be enabled — enforced in code. The
attempt produces an operator-readable refusal.

**Depends on.** B2.

### B7 · Metrics instrumentation (PRD §24) — `PARTIAL`

**What exists.** `IDEAS-100` #100 — a live latency + confidence HUD with average ms and
% auto-staged — is marked shipped, and `UIUX-PROCESS.md` §2.8 requires instrumenting.

**Deliverables**
* Persist the on-screen numbers to the session log so §24 is measurable **across** services,
  not just watched live.
* Instrument: auto-stage rate, recognition precision, silent-failure count, honest-miss
  quality, reference latency p95, operator touches, archive lookup time.
* **Latency measured from speech-end detection**, not parse start, so the §23 ≤ 2.5 s budget is
  honest end-to-end.
* A local metrics view — the church sees its own numbers. No upload, ever (§21).

**Gate.** A 20-minute test service produces all §24 metrics without manual counting; the
silent-failure count is computable and is provably zero or a release blocker.

**Depends on.** B5.

### B8 · Test harness, golden corpus and CI gates — `PARTIAL`

**What exists.** 64 locked tests, including every PRD §6 acceptance utterance. `TESTING.md`
documents the manual test plan. `examples/e2e.rs` replays a WAV through the ASR engine.

**Deliverables**
* Run the suite in CI on every commit; make an Appendix B regression fail the build.
* **Parser fuzz corpus** for filler tolerance — the parser must not depend on a word list.
* **Latency harness** on M1 asserting the §23 budgets; **memory harness** asserting ≤ 350 MB
  RSS across a simulated 60-minute service.
* Reconcile the count: `TESTING.md` says 47, `README.md` and `ACCURACY.md` say 64. One number.
* Process rule: every real mishear becomes a locked test **in the same release** it is fixed in.

**Gate.** CI fails on an Appendix B regression; the corpus runs offline; latency and memory
harnesses produce numbers, not impressions.

**Depends on.** A0, B5.

---

## §5. Phase C — M1 / v0.9 Train

Sourced from `docs/ACCURACY.md` §2 (items 15–20) and `docs/IDEAS-100.md` `[NEXT]` items.

| Slice | Scope | Source | Exit gate |
|---|---|---|---|
| **C1 · ASR upgrade — base.en + Metal** | Auto-detect `base.en`, fall back to `tiny.en`; Metal acceleration. Auto-detect code already ships | ACCURACY #3, #18; IDEAS #32, #47 | p95 latency still ≤ 2.5 s with base.en on M1; WER measurably better on the C5 eval set |
| **C2 · Per-segment ASR confidence** | Surface avg log-prob in the operator UI; combine parser × ASR confidence into one auto-stage gate | ACCURACY #15, #16; IDEAS #33, #34 | A low-ASR-confidence utterance is **not** auto-staged even when the parser is confident |
| **C3 · Room noise calibration** | 30 s routine tuning VAD thresholds per sanctuary | ACCURACY #17; IDEAS #36 | Calibrated profile measurably reduces false triggers in a reverberant test room |
| **C4 · Self-learning correction table** | Operator corrections persist locally and pre-correct future transcripts | ACCURACY #16; IDEAS #35 | A corrected mishear stops recurring in the same installation |
| **C5 · Eval harness** | 200 recorded utterances (100 references weighted by preaching frequency, 50 commands, 50 quotations), 3 mic profiles, 2 rooms; `cargo run -p rf-app -- eval <folder>` scorecard | ACCURACY §5; IDEAS #39 | Scorecard prints WER + correct-action-rate + p50/p95; every accuracy change ships before/after numbers |
| **C6 · Translation expansion** | ASV and WEB as built-ins; parallel two-translation view | IDEAS #81, #82 | Both pass `from_translation()` validation; parsing still KJV-canonical; licence records populated |
| **C7 · Stage themes** | Light "projector-max" and high-contrast stage presets | IDEAS #60; UIUX §4 | A bright-sanctuary preset is legible at 60% projector brightness; tokens from A1 only |
| **C8 · Command palette + onboarding** | ⌘K palette; first-run tour (mic permission → voice test → 10-second demo) | IDEAS #95, #97; UIUX §4 | A first-time operator completes setup unaided; every action reachable from the palette |
| **C9 · Accessibility** | VoiceOver labels, contrast audit, reduced-motion | IDEAS #99; UIUX §4 | Audit recorded; reduced-motion honoured on all stage transitions |
| **C10 · Sermon export** | Auto chapter markers for podcast export from `events.jsonl`; verse-clip export | IDEAS #72, #74 | A service exports chapter-marked audio with correct timestamps |
| **C11 · Regression expansion** | Every real mishear and correction collected during M1 becomes a locked utterance | PRD §23; IDEAS #105 | Corpus grows monotonically; no locked utterance is ever removed |

---

## §6. Phase D — M2 Archive and Polish

| Slice | Scope | PRD | Exit gate |
|---|---|---|---|
| **D1 · Sermon archive browser + search** | Over B2's FTS. `IDEAS-100` #73 | §12 | A referenced verse is findable in a past sermon in ≤ 30 s by scripture, speaker, date, series, topic or tag |
| **D2 · Post-service editing** | Corrections to transcript, references, titles, metadata, tags — through the `edits` table | §13 | No correction destroys the original; the original is retrievable after any number of edits |
| **D3 · Timeline view** | Chronological view over `sermon_events`; selecting an entry seeks the recording | §7.3 | Every event kind in §7.3 is represented and seekable |
| **D4 · Service modes** | Full Service · Sermon · Bible Reading · Custom | §9 | A mode change provably suppresses triggers in excluded portions without restarting |
| **D5 · Service templates** | Save / apply / export templates | §20 | A template round-trips between installations and applies cleanly; preparation stays optional |
| **D6 · Branding and styles editor** | Style editor over A1 tokens, exported as one portable file | §6.7 | A style imported into a different installation renders identically |
| **D7 · Command centre polish** | The three-zone layout exists; unify remaining surfaces (history, timeline, suggestions) into it | §8 | A first-time operator answers "what is on stage, what is it hearing, is it recording" in ten seconds |
| **D8 · Cloud sync to user-owned storage** | iCloud Drive folder copy or S3 with **user-supplied keys**. `IDEAS-100` #71 | §15 | Sync never runs on the live path; local stays authoritative; the user owns the credentials |
| **D9 · Transcript polishing pass** | Re-decode with context so transcripts read well, not just index well. `IDEAS-100` #75 | §7.1 | Polished transcript is human-readable without changing the timestamps used by the index |
| **D10 · Translation download manager** | User picks translations, validated and cached. `IDEAS-100` #84 | §6.4, §18 | Keeps the binary small; every downloaded text passes the licence gate |

---

## §7. Phase E — M3 (deferred)

**Not to be started until M2 is trusted in real services.** This is where the local-first
boundary is deliberately widened — and only here.

* **E1 · Accounts and roles (§16)** — the B3 role enum becomes enforced. Adds `users`,
  `churches`, `roles`, `sessions` **additively**; no M0–M2 table is reshaped.
* **E2 · Multi-service and multi-location (§17)** — service and location scoping on `sermons`.
* **E3 · Sharing (§14)** — explicit, opt-in, never on the live path.
* **E4 · Language expansion (§18)** — additional spoken languages and Bible-language pairs.
  `IDEAS-100` #17 (multilingual command sets) and #111 (multilingual UI) gate this.
* **E5 · Integrations** — ProPresenter / Planning Center import (`IDEAS-100` #113).
* **E6 · Adoption metrics (§24)** — measurable only once accounts exist, and only with explicit
  church consent (§21).

---

## §8. Phase X — Cross-Cutting (runs alongside every phase)

* **X1 · Packaging and signing** — signed, notarized `.app`/`.dmg` so a volunteer installs by
  dragging, no terminal. `IDEAS-100` #107. Gate: installer ≤ 100 MB (§23), model bundled once,
  no build artifacts shipped. **Today only `run.sh` exists.**
* **X2 · Model delivery** — the single sanctioned network call (D-6 exception). Must stay
  install-time only, checksum-verified, and never on the live path.
* **X3 · Performance budget gate** — latency, parse time, memory and installer size asserted in
  CI against §23. A release that breaks a budget is a failed release.
* **X4 · Version-sync discipline** — `IDEAS-100` #106 claims this shipped, but the PRD says
  v0.813.0 while the code says v0.801.2, and the test count is quoted as both 47 and 64. Make it
  a release-time audit script: one version string, one test count, everywhere.
* **X5 · Documentation upkeep** — README, PRD, this plan and the code stay in agreement. §0 of
  this document is the first instance of that discipline, not the last.

---

## §9. Suggested Order of Work

```text
A0  import + verify baseline        ← unblocks everything
A1  design tokens (role-named)
A2  components + accessibility
B1  workspace boundaries (small)
B2  SQLite + FTS5 over flat files   ← highest risk
B4  storage consolidation
B3  local identity (no login)
B5  session state machine + event log
B6  translation registry
B7  metrics
B8  test harness + CI gates
--- v0.9 ---
C5  eval harness                    ← measure before tuning
C1  base.en + Metal
C2  ASR confidence gating
C3  room calibration
C4  self-learning corrections
C6  translations · C7 stage themes · C8 palette+onboarding · C9 a11y · C10 export
C11 regression expansion
--- M2 ---
D1…D10
```

**Rationale for the two swaps:** **B2 before B3/B5** because the session log's canonical form
depends on where it is stored. **C5 before C1–C4** because `ACCURACY.md` §5 is explicit that no
accuracy change ships without before/after numbers — you cannot tune what you cannot measure.

---

## §10. Open Decisions

| # | Question | Why it matters |
|---|---|---|
| 1 | **Do the flat-file artefacts stay the source of truth, or does SQLite take over?** This plan recommends keeping artefacts authoritative (D-8) so §21 portability survives. | Reverses the meaning of B2's gate |
| 2 | **When does the `run.sh` model download become a bundled model?** `IDEAS-100` #102 marks it shipped, but the zip is 73 MB *with* the model — a signed `.app` may exceed the 100 MB §23 budget. | Blocks X1 |
| 3 | **Does TTS read-aloud belong in the PRD as a first-class feature?** It ships, has 4 tests, and has no PRD section. | It is currently unowned |
| 4 | **Is v0.801.2 the M0 baseline, or does a later v0.813.0 exist elsewhere?** `PRD-v2-review.md` flags the drift; the zip is v0.801.2. | Determines what A0 imports |
| 5 | **Are `docs/IDEAS-100.md` and `docs/ACCURACY.md` folded into the PRD, or kept as separate living backlogs?** They are currently more current than §25. | Avoids three competing roadmaps |

---

*Every slice above has a gate. A slice without a gate is not a slice.*
