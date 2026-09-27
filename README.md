# RhemaFlow

> **The preacher speaks. RhemaFlow understands.**

RhemaFlow is an intelligent church presentation and sermon platform that listens to preachers in real time, understands Scripture and sermon content, automatically presents relevant information, and turns every service into a searchable, timestamped sermon record.

## Purpose

RhemaFlow is a smart church presentation and sermon intelligence platform designed to understand a preacher's spoken message in real time.

It listens during a church service, recognizes spoken Scripture references and recognizable Scripture quotations, retrieves the appropriate Bible passage, and automatically presents it to the congregation.

At the same time, it records the sermon, creates a timestamped transcription, identifies scriptures referenced during the service, and builds a searchable sermon archive.

Central principle:

> **The preacher speaks naturally. RhemaFlow understands and presents.**

Automation is balanced with control:

> **Automatic presentation when confidence is high, human control when judgment is needed.**

See the full specification in [`PRD.md`](PRD.md) (**PRD v2.1**). That document is the single
source of truth: §33 fixes the local-first architecture and technology decisions, and §34
slices delivery into gated units ordered design system → architecture → features.

PRD v1.0 is retained at [`docs/RhemaFlow - Product Requirements Document.md`](docs/RhemaFlow%20-%20Product%20Requirements%20Document.md)
for history only. It is superseded.

## Target Users

### Primary

- **Preachers and speakers** — preach naturally without learning special commands or changing speaking style.
- **Church media and AV operators** — retain visibility and control over what is detected and presented.

### Secondary

- **Church administrators** — manage church settings, users, services, and archive access.
- **Church members and viewers** — consume shared sermon recordings and searchable sermon content.
- **Ministries and larger church organizations** — operate multiple services, teams, or locations.

## Core Problem

Church media teams today must listen carefully to the preacher, identify Bible references, search for the correct passage, select the translation, prepare the presentation, and display it at the right moment.

This causes:

- Scripture appearing late due to manual lookup
- Operators splitting attention between preacher and presentation system
- Preachers moving to a new passage faster than operators can follow
- Spontaneous Scripture references being missed
- Recordings with no structured index of Scriptures used
- Sermon recordings that are difficult to search or revisit
- Pressure to replace existing presentation workflows churches already trust

RhemaFlow addresses this by allowing the presentation system to **understand the sermon rather than simply wait for manual instructions.**

## Proposed Solution

RhemaFlow acts as the church's intelligent live presentation assistant:

- **Voice-activated Scripture trigger:** understands natural expressions like “John 3:16”, “John chapter 3 verses 16 through 18”, “First Corinthians chapter 13”, “Let’s go back to verse 7”, “Turn with me to Psalm 23”. Presents automatically when confidence is sufficient; operator can override or cancel.
- **Scripture quotation recognition:** identifies likely Scripture from recognizable quotations (e.g. “For God so loved the world…”) even without a stated reference. Operator can approve, modify, or reject.
- **Natural context understanding:** resolves follow-ups like “let’s go back to that verse”, “now look at verse 7”, “compare that with Romans 8” in the context of the current service.
- **Smart presentation:** auto-generates polished slides with Scripture text, reference, translation, and adaptive formatting, plus church branding, styles, fonts, colours, and layouts.
- **Translation management:** church-selected default translation, with recognition of explicit requests (e.g. “Now let’s read it in the NIV”). Public-domain support first, with a pathway for licensed translations.
- **Confidence and operator review:** uncertain detections surface as suggestions — Approve · Correct · Dismiss — without forcing verification of every straightforward reference.
- **Live Operator Command Centre:** one workspace for live transcription, current detection, current presentation, translation, uncertain detections, suggested content, Scripture history, timeline, recording state, and presentation controls.
- **Sermon intelligence:** live transcription, timestamped Scripture index (e.g. 10:42 — John 3:16), service timeline, and suggested sermon points for presentation.
- **Service workflow support:** Full / Sermon / Bible Reading / Custom modes, flexible audio source management, service preparation (optional) and reusable templates, local + cloud recording, offline-capable live operation.
- **Archive and sharing:** every service becomes a searchable record (title, date, speaker, transcript, recording, Scripture index, timeline, tags) with post-service editing that preserves the original, and controlled sharing.
- **Accounts and scale:** role-based access (Admin, Media Operator, Speaker, Archive Viewer), multi-service and multi-location support, English-first with multilingual growth in mind.
- **Coexistence:** works as a complete presentation system **or** as an intelligent companion to existing presentation software.

Typical journey: operator starts from a template → preacher speaks naturally (“Let’s turn to John chapter 3, verse 16”) → Scripture appears → quotation or sermon point triggers a suggestion → operator approves/corrects → after service, recording + transcript + index + timeline are saved, correctable, archivable, and shareable.

## MVP Features (v1.0)

Per PRD Section 24, the first release concentrates on the central promise:

1. **Live Scripture understanding** — recognize natural spoken Scripture references.
2. **Automatic Scripture presentation** — display detected Scripture automatically.
3. **Operator override** — correct, approve, or dismiss detections.
4. **Translation selection** — church default + recognition of explicitly requested translations.
5. **Scripture quotation recognition** — recognize common quoted Scripture without explicit reference.
6. **Live transcription** — transcribe the sermon for live context and archive.
7. **Scripture timeline** — link every detected Scripture to its place in the sermon.
8. **Recording** — record the service and associate it with its sermon record.
9. **Church presentation customization** — polished default style + church customization.
10. **Operator command centre** — one central live dashboard for the media team.
11. **Local and cloud saving** — preserve sermon content per church workflow.
12. **Searchable sermon archive** — keep completed sermons useful after the live service.

Out of scope for MVP: full church management, worship/music management, general-purpose AI assistant, generic video editing. Later expansion adds more content generation, languages, multi-location workflows, integrations, and discovery — guided by **“Automation should grow as trust grows.”**

## Key Principles

1. **Preacher first** — the preacher speaks naturally.
2. **Automation first** — perform repetitive presentation work automatically.
3. **Human control always** — the media operator can always intervene.
4. **Understand context** — understand what the preacher means, not merely keywords.
5. **Beautiful by default** — auto-generated content looks professional.
6. **Useful after the service** — every sermon becomes a valuable searchable record.
7. **Church-controlled** — the church controls presentation, access, sharing, and its archive.
8. **Start focused, expand intelligently** — win through Scripture and sermon intelligence first.

## Project Status

**Specification complete. Source not yet imported into this repository.**

There **is** a working application: **RhemaFlow-D v0.801.2**, delivered as
`Desktop M1 app/RhemaFlow-D-v0.801.2.zip` (73 MB). It is a real Rust workspace with a
structural Scripture parser, offline whisper ASR, offline recording, an embedded KJV **and**
BBE, a Cathedral Dark operator UI and **64/64 green tests**.

It is not in this repository yet. The first implementation slice, **A0 — Import and verify the
baseline**, brings it in and re-verifies the suite. Until A0 completes, treat the code as
readable but un-integrated.

> **Version note.** Earlier revisions of the PRD referred to "v0.813.0" and "47 tests". The
> shipped artefact is **v0.801.2** with **64** tests. Corrected in PRD §25, Appendix A and
> Appendix C.

## Documents

| Document | What it is |
|---|---|
| [`PRD.md`](PRD.md) | **Authoritative spec (v2.1).** Product intent, features, budgets, roadmap, architecture decisions (§33), sliced plan (§34) |
| [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md) | **Code-grounded delivery plan.** Baseline reconciliation, every slice with a gate, sequencing, open decisions |
| [`docs/RhemaFlow - Product Requirements Document.md`](docs/RhemaFlow%20-%20Product%20Requirements%20Document.md) | PRD v1.0 — history only, superseded |
| `docs/RhemaFlow-PRD-v2.0.md` | Pointer to `PRD.md` — do not edit |

## Architecture at a Glance

Everything runs locally. There is no server, no hosted backend and no cloud dependency.

| Layer | Decision | Status | Detail |
|---|---|---|---|
| Framework | Rust 2021 + `egui`/`eframe` `=0.28.1`, `cpal` `=0.15.3`, `whisper-rs` `=0.13.2` | **Built** | Single native macOS binary, no webview. PRD §33 D-1 |
| Database | SQLite (`rusqlite`, bundled) + FTS5 | **To build** | Additive index over the flat-file archive. PRD §33 D-2, D-8 |
| Authentication | None at runtime — local, single-operator | **By design** | No login screen; roles modelled but not enforced until M3. PRD §33 D-3 |
| File storage | Local filesystem — `~/RhemaFlow-Services/<timestamp>/` | **Built** | `audio.wav`, `transcript.txt`, `events.jsonl`, `index.md`. PRD §33 D-4 |
| Network | Zero calls on the live path | **Built** | One sanctioned exception: the model download in `run.sh`, at install time only. PRD §33 D-6 |
| Design system | *Cathedral Dark* role tokens, three palettes | **Partial** | Tokens exist but are named by appearance and dark-only. PRD §33 D-9 |

Full rationale and the data model are in [`PRD.md`](PRD.md) §33.

## Repository Layout

```text
.
├── README.md
├── PRD.md                                    # authoritative spec (v2.1)
├── IMPLEMENTATION-PLAN.md                    # sliced delivery plan
├── Desktop M1 app/
│   └── RhemaFlow-D-v0.801.2.zip              # the shipped v0.801.2 baseline (73 MB)
└── docs/
    ├── RhemaFlow-PRD-v2.0.md                 # pointer → ../PRD.md (superseded)
    └── RhemaFlow - Product Requirements Document.md   # v1.0, history only
```

The workspace layout (`crates/rf-bible`, `rf-core`, `rf-asr`, `rf-app`) arrives with slice A0
and is documented in [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md) §0.

## Getting Started

1. **[`PRD.md`](PRD.md) §33** — the architecture and technology decisions.
2. **[`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md) §0** — the baseline reconciliation: what
   actually ships today, and where the PRD was stale.
3. **[`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md) §1, §9** — the slicing rules and the
   recommended order of work.
4. **PRD Appendix B** — the locked regression utterances that must never regress.
5. **Slice A0** — import the baseline and re-run `cargo test --workspace`.
