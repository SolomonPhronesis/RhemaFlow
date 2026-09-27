# **RhemaFlow**

## **Product Requirements Document — Version 2.1**

> **Supersedes v2.0, which superseded v1.0.** Nothing from earlier versions was removed —
> it was sharpened. New in v2.0: numbered success metrics, MoSCoW priorities, a phased
> roadmap, technical budgets, risks with mitigations, per-feature acceptance criteria, and
> an honest map of what already ships today. The voice of v1.0 ("should", short sentences,
> one idea per paragraph) is retained deliberately.
>
> **New in v2.1:** §33 fixes the local-first architecture and technology decisions
> (framework, database, authentication, file storage); §34 slices the delivery into
> gated, manageable units ordered **design system → architecture → features**; Appendix C
> records the folder review and the resulting documentation debt. A v2.1 note is also
> added to §23.

---

### **1. Product Overview**

**RhemaFlow** is a smart church presentation and sermon intelligence platform designed to understand a preacher's spoken message in real time.

RhemaFlow listens during a church service, recognizes spoken Scripture references and recognizable Scripture quotations, retrieves the appropriate Bible passage, and automatically presents it to the congregation.

At the same time, RhemaFlow records the sermon, creates a timestamped transcription, identifies scriptures referenced during the service, and builds a searchable sermon archive.

The product is designed around one central principle:

> **The preacher speaks naturally. RhemaFlow understands and presents.**

RhemaFlow should automate as much of the live presentation experience as possible while ensuring the church's media team always retains meaningful control.

**Live-path rule:** everything needed for a live service — listening, parsing,
displaying, recording — must work with the network cable pulled. Cloud features are
convenience, never dependency.

---

### **2. Problem**

Church media teams often have to listen carefully to a preacher, identify Bible references, search for the correct passage, select the appropriate translation, prepare the presentation, and display the result at the right moment.

This creates several problems:

* Scripture can appear late because someone has to find it manually.
* The media operator must divide attention between the preacher and presentation system.
* A preacher can move to a new passage faster than the media operator can prepare it.
* Spontaneous Scripture references can be missed.
* Recordings do not automatically contain a structured index of the Scriptures used.
* Sermon recordings can become difficult to search or revisit later.
* Churches may already have presentation workflows they do not want to replace.

RhemaFlow addresses these problems by allowing the presentation system to understand the sermon rather than simply wait for manual instructions.

**Silent failure is a product defect.** When RhemaFlow cannot resolve what it heard,
it must say so in operator-readable language and offer the best alternative — never
quietly display the wrong verse. A wrong verse in front of a congregation is worse
than no verse.

---

### **3. Product Vision**

RhemaFlow should become the church's intelligent live presentation assistant.

It should eventually understand:

* What Scripture the preacher is referring to.
* What translation the preacher wants.
* When a Scripture should appear.
* When the preacher refers back to an earlier passage.
* What important sermon statements may be useful as presentation content.
* What happened during the service.
* Where important moments occurred in the recording.

The system should remain helpful without becoming intrusive.

---

### **4. Target Users**

### **Primary Users**

**Preachers and speakers**

They should be able to preach naturally without learning special commands or changing their speaking style.

**Church media and AV operators**

They should have visibility and control over what RhemaFlow detects and presents.

### **Secondary Users**

**Church administrators**

They manage church settings, users, services and archive access.

**Church members and viewers**

They may consume shared sermon recordings and searchable sermon content.

**Ministries and larger church organizations**

They may operate multiple services, teams or locations.

---

### **5. Core Product Promise**

RhemaFlow should provide:

> **Automatic presentation when confidence is high, human control when judgment is needed.**

The preacher should not have to operate the software.

The media operator should not have to manually perform tasks that RhemaFlow can safely perform itself.

---

# **6. Core Features**

*Priority labels: **M** = Must (MVP), **S** = Should (M1), **C** = Could (M2+).
Each feature carries acceptance criteria. Status names the v0.813.0 reality.*

## **6.1 Voice-Activated Scripture Trigger** — **M** · status: **shipped (structural parser)**

RhemaFlow continuously interprets the selected live service audio and identifies Scripture references.

It should understand natural expressions such as:

* "John 3:16."
* "John chapter 3 verse 16."
* "John chapter 3 verses 16 through 18."
* "First Corinthians chapter 13."
* "Let's go back to verse 7."
* "Turn with me to Psalm 23."

Parsing must be **structural, not a word-whitelist**: any number of filler words is
tolerated between the numbers of a reference, because no word list can cover natural
speech. When a spoken verse does not exist in the target book, the product says so
honestly and suggests the closest real candidates (for example: "1 Corinthians 5 has
only 13 verses (no verse 17) — did you mean 2 Corinthians 5:17?").

**Acceptance criteria**

* Given the transcript "let's go to john three sixteen", when it is processed, then
  John 3:16 is staged with its full verse text.
* Given "1st Corinthians five, for seventeen", then the product reports the honest
  out-of-range message and offers suggestions — it must not stage verse 1 silently.
* Given the bare phrase "verse 17" while a chapter is on stage, then the on-stage
  reference jumps within that chapter.
* Given a chapter-only mention ("First Corinthians chapter 13"), then verse 1 of that
  chapter is staged and the operator sees that it is chapter-only.

## **6.2 Scripture Quotation Recognition** — **S** · status: **planned**

RhemaFlow should also recognize recognizable quotations of Scripture even when the preacher does not state the reference.

> "For God so loved the world…"

RhemaFlow should be able to identify the likely Scripture and make it available for presentation.

The operator must retain the ability to approve, modify or reject uncertain detections.

**Acceptance criterion:** given a quotation whose first eight words match a unique
KJV verse, then the candidate appears in the confirm queue labeled as a quotation
match, never auto-staged above the operator's confidence setting.

## **6.3 Natural Context Understanding** — **S** · status: **partially shipped (bare "verse N" jumps; "that verse" planned)**

RhemaFlow should understand references in context rather than treating every statement independently.

> "Let's go back to that verse." · "Now look at verse 7." · "Compare that with Romans 8."

Context should help RhemaFlow understand what the preacher is referring to during the current service. Bare verse numbers already resolve relative to the chapter on stage; deictic phrases ("that verse", "the same passage") should resolve against stage history.

## **6.4 Translation Management** — **S** · status: **KJV shipped; dropdown ported from the v0.812 branch in M1**

RhemaFlow should support a church-selected default translation.

It should also recognize when the preacher explicitly asks for another translation. The product should support public-domain Bible translations directly while providing a pathway for churches to use appropriately licensed translations.

**Constraint:** initially only translations whose license permits redistribution
(KJV public domain; WEB; others reviewed per text). No bundled text without a license
check recorded next to it.

## **6.5 Confidence and Operator Review** — **M** · status: **shipped (confirm queue + confidence floor)**

When RhemaFlow is uncertain, it should not silently make an unreliable decision.

Instead, the operator should receive a useful suggestion.

**Possible Scripture detected** — John 3:15 · John 3:16 — **Approve · Correct · Dismiss**

The system should make uncertainty visible without making the operator manually verify every straightforward Scripture reference.

**Acceptance criteria**

* Given a reference scoring below the auto-stage threshold, then it appears in the
  confirm queue with alternatives, and the stage is unchanged until an operator acts.
* Given a non-speech transcript ("[BLANK_AUDIO]", "[MUSIC]"), then no candidate is
  produced and no error status is raised.

## **6.6 Smart Scripture Presentation** — **M** · status: **shipped (congregation stage, adjustable size/colors; layout adaptation M2)**

When Scripture is displayed, RhemaFlow should automatically create a polished presentation containing the Scripture text, reference, translation and appropriate formatting.

The layout should adapt to the amount of content. Short passages should remain prominent and readable. Longer passages should remain easy to follow.

## **6.7 Church Branding and Presentation Styles** — **C** · status: **planned (M2)**

RhemaFlow should provide a polished default presentation style. Churches should be able to customize branding, logo, visual style, fonts, colours, backgrounds and layouts, and save multiple styles for different services or events.

**Acceptance criterion:** a style is a single exported file that a different
installation can import and render identically.

# **7. Sermon Intelligence**

## **7.1 Live Transcription** — **M** · status: **shipped (offline ASR)**

RhemaFlow should create a live transcription of the sermon. The transcript should provide context for the live service and become part of the sermon archive. Transcription is local; no audio leaves the machine.

## **7.2 Scripture Index** — **M** · status: **shipped (timestamped scripture events written with the recording)**

Every detected Scripture reference should become part of the sermon record with its time within the service.

**Sunday Service** — 10:42 John 3:16 · 17:15 Romans 8:28 · 31:07 Psalm 23:1–6

Selecting an entry should take the user to that point in the sermon.

**Acceptance criterion:** every staged reference produces exactly one index entry
whose timestamp is within one second of the stage event, whether the reference came
from voice, the confirm queue, or manual entry.

## **7.3 Sermon Timeline** — **S** · status: **partial (events recorded; timeline view M2)**

The service should have a chronological timeline containing scripture references, translation changes, suggested content and important sermon moments. This timeline becomes part of the completed sermon archive.

## **7.4 Suggested Sermon Content ("three things" detection)** — **C** · status: **planned**

> "There are three things I want you to remember: Faith, Obedience and Perseverance."

RhemaFlow could suggest **Faith / Obedience / Perseverance** as presentation content. The operator can approve, edit or reject. This is enumerated-list detection first, semantics later — a strict pattern ("there are N things…") ships before any open-ended suggestion.

**Acceptance criterion:** given the enumerated pattern with N between 2 and 5 and a
list of short items, then one suggestion card is raised listing all N items; nothing
is staged without operator approval.

# **8. Live Operator Command Centre** — **M** · status: **partial (status, transcript feed, confirm queue, stage controls shipped; consolidated dashboard M2)**

The media operator should have one central workspace showing the state of the service: live transcription, current detected Scripture, current presentation, translation, uncertain detections, suggested content, Scripture history, service timeline, recording state and presentation controls.

The goal is not to give the operator more work. The goal is to give the operator **one place to understand what RhemaFlow is doing**.

**Acceptance criterion:** from a cold start, an operator who has never seen RhemaFlow can answer "what is on stage, what is it hearing, and is it recording?" within ten seconds.

# **9. Service Modes** — **C** · status: **planned (M2)**

**Full Service Mode** · **Sermon Mode** · **Bible Reading Mode** · **Custom Service Mode**

This prevents unwanted triggers during unrelated parts of the service.

# **10. Audio Source Management** — **S** · status: **partial (default input shipped; picker M1)**

RhemaFlow should work with an appropriate preacher/audio source while allowing the operator to change or select the source when necessary. The operator should never be locked into a single workflow.

**Acceptance criterion:** changing the input device takes effect within two seconds
without restarting the app, and the active device is always visible.

# **11. Recording** — **M** · status: **shipped (offline recording, scripture events embedded)**

RhemaFlow should create a high-quality sermon recording and associate it with the generated sermon record. The recording should remain connected to: transcript, scripture index, timeline, presentation events and sermon metadata.

**Constraints:** local storage first; a 60-minute service should not exceed
approximately 300 MB on disk (WAV/lossless acceptable in MVP; compressed container
M1); recording state must be visible at all times.

# **12. Sermon Archive** — **S** · status: **planned (local-first M2; cloud M3)**

Every completed service should become a searchable sermon record: title, date, speaker, service, transcript, recording, scripture index, translation information, timeline, presentation events, tags. Searching should work by scripture, speaker, date, series, topic and tag.

# **13. Post-Service Editing** — **S** · status: **planned**

Church users should be able to correct transcription errors, incorrectly identified references, sermon names, metadata, translation information and categories. Corrections should not destroy the underlying original record.

# **14. Sharing** — **C** · status: **later (M3, requires accounts)**

Churches should be able to share completed sermons with control over what is publicly shared. Downloading should remain available where permitted by the church.

# **15. Offline and Online Operation** — **M** · status: **shipped (fully offline live path)**

RhemaFlow should continue providing essential live functionality even when internet access is interrupted. When connectivity is restored, appropriate cloud information should synchronize. This is especially important for live worship environments where service continuity matters.

# **16. Church Accounts and Roles** — **C** · status: **later (M3)**

Roles: Church Administrator · Media Operator · Speaker/Preacher · Archive Viewer.

# **17. Multi-Service and Multi-Location Support** — **C** · status: **later (M3)**

Sunday Morning · Sunday Evening · Wednesday Bible Study · Youth Service · Main Campus · North Campus · Online Service. Each service retains its own sermon record.

# **18. Translation Expansion** — **S** (architecture M1, languages later)

The initial product prioritizes excellent English-language support. RhemaFlow should then expand to additional spoken languages and Bible-language combinations without weakening the initial experience.

# **19. Existing Presentation Software** — **S** · status: **companion mode shipped (standalone stage window)**

RhemaFlow should operate as a complete presentation system **or** as an intelligent companion to an existing presentation system. Churches that invested in current workflows should never be forced to abandon them.

# **20. Service Preparation and Reusable Templates** — **C** · status: **planned (M2)**

Before a service, a church may optionally prepare service information, speaker, sermon title, expected scriptures, preferred translation, presentation style. During the service, RhemaFlow continues responding to new or unexpected material. Preparation should make RhemaFlow better informed, not mandatory. Common arrangements should be savable as templates.

# **21. Privacy and Data Ownership** — **M** · status: **shipped (local-first, no telemetry)**

Churches should have clear control over their sermon information: what is recorded, how long content is retained, who can access it, what is shared, what is deleted. Privacy and trust should be treated as core product requirements rather than secondary settings. The live path sends nothing anywhere.

# **22. Core User Journey**

**Before the service** — the operator opens RhemaFlow, selects or starts a service, optionally applies a template. The default translation and presentation style load. *(Template selection: M2.)*

**During the service** — the preacher says "Let's turn to John chapter 3, verse 16." RhemaFlow identifies the reference. The Scripture appears on screen. The operator can override it. Later the preacher quotes "For God so loved the world…" and the candidate appears for approval. The service continues without the preacher touching software. *(Quotation candidates: M1.)*

**During an uncertain moment** — RhemaFlow raises a suggestion; the operator approves, corrects or dismisses; the service continues. *(Shipped.)*

**After the service** — recording, transcript, scripture index and timeline are saved; corrections can be made; the sermon joins the archive and may be shared. *(Archive and editing: M2.)*

# **23. Technical Constraints and Budgets**

These are commitments, not aspirations. A release that breaks a budget is a failed release even if its features work.

| Constraint | Budget |
|---|---|
| Platform | macOS on Apple Silicon (aarch64-apple-darwin), M1 baseline |
| Live connectivity | Fully offline: ASR, parsing, display, recording |
| ASR | Local whisper (English) bundled once; no download at service time |
| Reference → on screen | ≤ 2.5 s end-to-end on M1 for a clear utterance |
| Parse + stage work | < 50 ms CPU per transcript (excluding ASR decode) |
| Memory | ≤ 350 MB RSS during a live service |
| Installer | ≤ 100 MB zip; the ASR model is the dominant term and ships once |
| Bible text | Full KJV (31,102 verses) embedded and validated against verse counts at build |
| UI stack | egui/eframe 0.28.1; audio capture via cpal 0.15.3 |
| Tests | Regression suite green before any release; every user-reported failure becomes a locked test |

**v2.1 note.** This section fixes the *platform* and the *UI/audio libraries*. It
deliberately said nothing about where data lives, who a user is, or how bytes reach disk —
the three questions an implementer hits first. §33 now answers those. Where the two
sections could be read as conflicting, **§33 is authoritative on storage, identity and
file handling; §23 remains authoritative on platform, latency, memory and installer size.**

# **24. Success Metrics**

The product succeeds when it meaningfully reduces the amount of manual work required from the church media team. §27 of v1.0 asked questions; v2.0 answers them with thresholds.

| Metric | Definition | Threshold | Measured by |
|---|---|---|---|
| Auto-stage rate | Chapter-qualified references staged with zero operator action | ≥ 90% per 20-min sermon | Session log |
| Recognition precision | Staged references that the operator did not correct | ≥ 97% | Operator corrections |
| Silent-failure rate | Wrong verse displayed with no warning | 0 — any occurrence is a release blocker | Session log audit |
| Honest-miss quality | Unresolvable requests answered with a useful suggestion | ≥ 80% of misses carry a correct suggestion | Sampled review |
| Reference latency | Speech end → verse on screen | ≤ 2.5 s (p95) | Timestamped events |
| Operator touches | Manual interactions per 20-min sermon | ≤ 3 for a typical sermon | Session log |
| Preacher friction | Behaviour changes the preacher must make | 0 by design | Review |
| Archive usefulness | Time to find a referenced verse in a past sermon | ≤ 30 s | Timed test |
| Adoption | Churches active after 4 weeks of trial | ≥ 60% | (M3, once accounts exist) |

# **25. Phased Roadmap**

**M0 — shipped (this is v0.801.2 today)**

Offline whisper ASR · structural reference parser (filler-tolerant, digit-split,
fuzzy book match) · honest out-of-range messages with suggestions · bare "verse N"
jumps relative to the stage · next/previous navigation with chapter rollover · voice
fullscreen enter/exit · confirm queue with confidence floor · offline recording with
timestamped scripture events · full KJV embedded · **64/64 regression tests green**.

> **v2.1 correction.** This line previously read "v0.813.0" and "47/47". The shipped
> artefact is **v0.801.2** with **64** green tests (`README.md` and `docs/ACCURACY.md`
> both state 64; only `docs/TESTING.md` still said 47). Version strings had drifted across
> branches — see slice **X4** in `IMPLEMENTATION-PLAN.md`. The M0 feature list above is
> also incomplete: see §25a.

**M1 — next release train**

Port the v0.812-branch features (translation dropdown, auto-gain, italics) ·
audio input picker · ASR accuracy pass (initial-prompt biasing with the 66 book
names, post-ASR fuzzy correction against the book list) · quotation recognition
(6.2) behind the confirm queue · context commands "back to that verse" · locked
regression utterances from every real mishear.

**M2 — archive and polish**

Local sermon archive with search (12) · post-service editing (13) · sermon timeline
view (7.3) · service modes (9) · templates (20) · branding/styles (6.7) ·
consolidated operator dashboard (8) · suggested "three things" content (7.4).

**M3 — cloud, accounts, teams**

Accounts and roles (16) · multi-service/multi-location (17) · cloud sync and sharing
(14) · adoption metrics (24) · additional languages (18).

> **Automation should grow as trust grows.** Each phase earns the next.

# **25a. Shipped but Undocumented** *(new in v2.1)*

These capabilities ship in v0.801.2 and are relied on by operators, but had **no PRD section**.
Left unlisted they would be lost in the next refactor. Each needs a home section in the next
revision.

| Capability | What it does | Code |
|---|---|---|
| **Scripture read-aloud (TTS)** | Reads the on-stage verse aloud with a macOS system voice. Voice picker with natural-quality (★) and gender labels, rate slider, auto-read toggle, "Read it" / "Stop reading" voice control | `crates/rf-app/src/tts.rs` (4 tests) |
| **Voice command grammar** | Bare-word and fuzzy commands: next / previous / next chapter / back a chapter / last scripture / again / zoom in / zoom out / reset zoom / full screen / normal screen / clear the screen | `crates/rf-core/src/commands.rs` (11 tests) |
| **Scripture-vs-command guard** | "next is John 3" stages John 3 rather than advancing — commands never eat references | `commands.rs` |
| **Voice cannot stop listening or recording** | Lifecycle controls are operator-only by design; a misheard "stop recording" must never be able to end a service recording | `commands.rs` |
| **Utterance simulator** | Type an utterance and run it through the identical pipeline — demo insurance and operator training | `crates/rf-app` |
| **CLI modes** | `--demo` (built-in ASR, no model), `--no-asr`, `--model PATH`, `--church NAME`, `--voices`, `--yes` | `crates/rf-app/src/main.rs` |
| **HEARD → RESULT strip** | Shows exactly what the app heard and what it did with it | `crates/rf-app/src/ui.rs` |
| **Stage zoom** | A− / A+ / 1:1 via buttons, keys and voice; persisted | `ui.rs`, `stage.rs` |
| **BBE as a second translation** | Embedded and build-validated; proves the multi-translation architecture end to end | `crates/rf-bible/src/lib.rs` (9 tests) |
| **`from_translation()` framework** | Any public-domain translation in the same schema validates and plugs in — adding one is a *data* task, not an engineering task | `crates/rf-bible/src/lib.rs` |
| **Human-readable `index.md`** | Timestamped sermon Scripture index written at service end | `crates/rf-app/src/actions.rs` |
| **Pluggable ASR engine trait** | No vendor lock-in; a better local engine plugs in behind the same interface | `crates/rf-asr/src/engines.rs` |
| **One-command bootstrap** | `./run.sh` installs the toolchain, verifies the model checksum, builds and launches | `run.sh` |
| **On-screen metrics** | Average latency and % auto-staged, visible in the corner | `ui.rs` |

> **Note on §6.3 and §6.4.** "Voice fullscreen enter/exit" was the only voice command the PRD
> acknowledged. The command grammar is now considerably broader than §6.3 describes, and
> read-aloud is a congregation-facing feature with no PRD section at all. Both need sections
> before M1.

# **26. Risks and Mitigations**

| Risk | Impact | Mitigation |
|---|---|---|
| ASR mishears book names and numbers ("Perverse seventeen" for "verse seventeen") | Wrong or missing verse | Structural parser + suffix correction + fuzzy book match with preaching-frequency tie-break; every real mishear becomes a locked regression |
| Verse does not exist (1 Corinthians 5:17) | Wrong verse silently displayed | Verse-count-validated parsing; honest out-of-range message with "did you mean" suggestions; silent-failure metric is 0 by policy |
| Operator trust erodes after one visible mistake | Product abandoned mid-service | Confirm queue below confidence threshold; override always one key away; mistakes corrected in the next build, never explained away |
| Model size dominates installer | 72+ MB deliverables | Bundle the model once, exclude build artifacts, document expected size; download-on-demand alternative for constrained sites |
| Mic permissions on macOS block first run | App appears broken | One-time guided permission step with a visible state indicator |
| Translation licensing | Legal exposure | Public-domain texts only until each license is reviewed and recorded next to the text |
| Recording disk usage surprises a church mid-service | Lost recording | Visible recording state, free-space check at start, documented ~300 MB/hour |

# **27. MVP Definition (revised)**

v1.0 listed twelve "essential" capabilities. That is a v1.0, not an MVP. The MVP is
the smallest thing a church would run a real service on:

**Essential first release (all shipped in M0)**

1. **Live Scripture understanding** — structural parsing of spoken references.
2. **Automatic presentation + operator override** — stage and confirm queue.
3. **Navigation** — next/previous, chapter rollover, bare "verse N" jumps.
4. **Honest errors** — out-of-range messages with suggestions; no silent failures.
5. **Live transcription** — offline.
6. **Recording with scripture index** — timestamped events tied to the recording.

Everything else is M1+ and listed where it belongs in §25. The MVP is not the vision;
it is the trust-building core.

# **28. Later Expansion**

More automatic presentation content generation · greater sermon understanding · additional languages · more sophisticated multi-location workflows · deeper presentation integration · more advanced sermon discovery · richer sharing · more automated service preparation.

# **29. Non-Goals for the Initial Product**

RhemaFlow should not initially attempt to become a complete replacement for every church media tool, a church management system, a worship/music platform, a general-purpose AI assistant, or a video editor. Its differentiation remains strongly centered on:

> **Understanding live preaching and turning it into intelligent presentation and sermon records.**

# **30. Product Principles**

1. **Preacher first** — the preacher speaks naturally.
2. **Automation first** — repetitive presentation work is automated.
3. **Human control always** — the operator can intervene.
4. **Understand context** — meaning, not keywords.
5. **Beautiful by default** — auto-generated content looks professional.
6. **Useful after the service** — the sermon becomes a searchable record.
7. **Church-controlled** — presentation, access, sharing, archive.
8. **Start focused, expand intelligently** — win through scripture and sermon intelligence first.
9. **Never fail silently** *(new in v2.0)* — an honest "I could not resolve that, did you mean…" beats a confident wrong verse every time.

# **31. One-Sentence Product Definition**

> **RhemaFlow is an intelligent church presentation and sermon platform that listens to preachers in real time, understands Scripture and sermon content, automatically presents relevant information, and turns every service into a searchable, timestamped sermon record.**

# **32. Product Tagline**

> **RhemaFlow — The preacher speaks. RhemaFlow understands.**

---

# **33. Architecture and Technology Decisions — Local-First** *(new in v2.1)*

Everything here is a **decision, not an option**. Each entry records what was chosen, why,
and how expensive it is to reverse, so a future contributor can follow the reasoning rather
than guess at it.

> **Scope of this decision set.** The entire product runs locally. There is no server, no
> hosted backend, no managed database and no cloud dependency in M0–M2. "Local" here means
> *the whole system* — not a local cache in front of something remote.

## **33.1 Decision Record**

| # | Area | Decision | Why | Cost to reverse |
|---|---|---|---|---|
| **D-1** | **Framework** | Rust (edition 2021, MSRV 1.79) + `egui`/`eframe` **0.28.1**; audio capture via `cpal` **0.15.3**; ASR via a locally-run whisper model | Already the committed stack in §23. Produces one native macOS binary with no webview and no JS runtime — which is what keeps the ≤ 2.5 s reference latency and ≤ 350 MB RSS budgets reachable | **Very high** — a stack change rewrites the entire UI layer |
| **D-2** | **Database** | **SQLite** via `rusqlite` with the `bundled` feature (no system SQLite) + **FTS5** for search | Embedded, serverless, single-file, zero configuration — the only database that satisfies "runs locally" without adding an installer step. FTS5 delivers the §12 archive search and the §7.2 scripture index lookup | **Medium** — the schema is portable; the access layer is not |
| **D-3** | **Authentication** | **None at runtime.** Local-only, single-operator, no accounts, no login screen | §15, §16, §21. The live path is offline and the church owns the machine. A login prompt must never stand between a preacher and a working service. Accounts are an M3 concern and must be *additive* | **High** — but only because it is additive later, not because it blocks anything now |
| **D-4** | **File storage** | **Local filesystem only** — one fixed app-data root plus one user-selectable library root | §11, §21. Recordings, models, transcripts and exports stay on the machine. No object storage, no network share required | **Low** |
| **D-5** | Distribution | Signed and notarized macOS `.app` / `.dmg`, Apple Silicon only (`aarch64-apple-darwin`) | §23 platform commitment, M1 baseline | **Low** |
| **D-6** | **Network** | **Zero network calls in M0–M2.** No telemetry, no update pings, no crash reporting | §21. Any future sync is explicit, opt-in and M3+ | **Low** |
| **D-7** | Language of record | Rust for all core logic — no second runtime for parsing, matching or storage | Keeps the < 50 ms parse budget honest and removes an IPC boundary from the hot path | **High** |
| **D-8** | **Source of truth for the archive** | **The flat-file service folder stays authoritative; SQLite is a queryable index over it** | v0.801.2 already writes `audio.wav` + `transcript.txt` + `events.jsonl` + `index.md` per service. A church must be able to read its own archive with the app uninstalled (§21). If the database is deleted it must rebuild from the folders | **Medium** — reversing this would make the archive app-dependent |
| **D-9** | **Design token naming** | Tokens are named by **role** (`accent`, `status.ok`, `stage.verse_text`), never by appearance | `theme.rs` currently ships `GOLD` / `GREEN` / `RED` / `BLUE`. A light theme and stage presets are impossible to add without editing every call site unless tokens are role-named | **Low** — a mechanical rename, values unchanged |

## **33.2 The Local-First Boundary** *(enforced rule)*

**No slice in Phase A–D may introduce a network call.** This is a gate, not a guideline.

What follows from it:

* The ASR model is **bundled once** at install time; there is no download-on-demand at service time.
* Bible text is **embedded**; no API is consulted to resolve a reference.
* Update checking, if it ever exists, is a manual user action — never automatic during a service.
* The app must reach a fully working live state with the network cable physically pulled.

## **33.3 Data Model (SQLite)**

One database file, `rhemaflow.db`, in the app-data root. WAL mode. The schema is versioned
through `schema_migrations`; every migration is forward-only and additive.

| Table | Purpose | Key columns |
|---|---|---|
| `schema_migrations` | Migration ledger | `version`, `applied_at` |
| `settings` | Key/value application configuration | `key`, `value`, `updated_at` |
| `translations` | Available Bible translations **and their licence record** | `code`, `name`, `license`, `license_reviewed_at`, `verse_count`, `is_default`, `enabled` |
| `sermons` | One row per service (§12) | `id`, `title`, `service_date`, `service_label`, `speaker`, `translation_code`, `duration_ms`, `recording_path`, `status` |
| `sermon_events` | The append-only service timeline (§7.3) | `id`, `sermon_id`, `ts_ms`, `kind`, `payload_json`, `source`, `confidence` |
| `scripture_index` | Every staged reference with its time (§7.2) | `id`, `sermon_id`, `event_id`, `book`, `chapter`, `verse_start`, `verse_end`, `translation_code`, `ts_ms` |
| `transcript_segments` | Timestamped ASR output (§7.1) | `id`, `sermon_id`, `ts_ms`, `end_ms`, `text`, `confidence` |
| `edits` | Non-destructive corrections (§13) | `id`, `sermon_id`, `target_table`, `target_id`, `field`, `old_value`, `new_value`, `edited_at` |
| `styles` | Exported/imported presentation styles (§6.7) | `id`, `name`, `json` |
| `templates` | Reusable service templates (§20) | `id`, `name`, `json` |

**Search indexes (FTS5):** `scripture_index_fts` (book/chapter/verse as text),
`transcript_fts` (segment text), `sermons_fts` (title, speaker, service label, tags).

**Deliberately absent in M0–M2:** `users`, `churches`, `roles`, `sessions`, `sync_queue`.
These arrive in Phase E (§34.6) and must be additive — no M0–M2 table may be reshaped to
accommodate them.

**Correction rule (§13).** The original value is never destroyed. A correction writes a row
to `edits` and marks the derived value, so the original record stays auditable.

## **33.4 On-Disk Layout**

> **v2.1 correction.** An earlier draft of this section proposed a new
> `~/Library/Application Support/RhemaFlow/` tree. That would have relocated a working
> archive. The layout below is the **actual v0.801.2 layout**, with SQLite (D-2) added
> *alongside* the flat-file record (D-8), not in place of it.

```text
~/RhemaFlow-Services/                    # the archive — portable, human-readable (D-8)
└── 2026-09-27-1030-sunday-am/
    ├── audio.wav                        # 16 kHz mono PCM, ~115 MB/h (§11)
    ├── transcript.txt                   # timestamped live transcript (§7.1)
    ├── events.jsonl                     # canonical machine-readable event log (§7.2, §7.3)
    └── index.md                         # human-readable Scripture index, written at end

~/.rhemaflow/
├── settings.json                        # app settings (migrates into SQLite in B2)
├── rhemaflow.db                         # SQLite + FTS5 — index over the archive (D-2)
├── rhemaflow.db-wal                     # WAL journal
├── styles/                              # portable style files (§6.7)
├── templates/                           # portable service templates (§20)
└── logs/
    └── session-2026-09-27.jsonl         # session log powering the §24 metrics

models/ggml-tiny.en.bin                  # 77 MB, checksum-verified at setup
```

**Rebuild rule (D-8).** Deleting `rhemaflow.db` must cost nothing but time: the index is
rebuilt by reading the service folders. This is the acceptance test for slice B2.

**Library root.** The service folder is currently fixed under `$HOME`. It must become
user-selectable so a large archive can live on an external drive. If the configured root is
unreachable, the app must say so **before** the service begins — never fail mid-recording (§26).

**Budget check.** 60 minutes ≈ 115 MB measured (§11 budget was ~300 MB/h — the build is well
inside it). A free-space pre-check runs at recording start.

**Model size.** `ggml-tiny.en.bin` is 77 MB and dominates the 73 MB zip. Moving to `base.en`
(planned, slice C1) roughly doubles that and will press the §23 ≤ 100 MB installer budget —
see open decision 2 in `IMPLEMENTATION-PLAN.md`.

## **33.5 What This Deliberately Is Not**

* **Not a web app.** No browser, no local HTTP server, no frontend build pipeline.
* **Not a client/server system.** There is no backend to run and no API to version.
* **Not multi-tenant.** One installation serves one church, offline, until M3.
* **Not a cloud product with a local cache.** It is a local product with, eventually, an
  optional cloud convenience layer. The dependency direction never inverts (§15).

---

# **34. Implementation Plan — Sliced for Delivery** *(new in v2.1)*

## **34.1 How to Read a Slice**

> **The detailed, code-grounded version of this plan lives in
> [`IMPLEMENTATION-PLAN.md`](IMPLEMENTATION-PLAN.md).** That document reconciles this section
> against the shipped **v0.801.2** codebase — real crate paths, the verified 64-test count,
> the actual on-disk layout, and the `docs/ACCURACY.md` + `docs/IDEAS-100.md` backlogs. Where
> the two differ on *sequencing detail*, the standalone plan wins; where they differ on
> *product intent*, this PRD wins.

A **slice** is the smallest unit of work that can be finished, demonstrated and gated on its
own. The slicing rules:

1. **Every slice ships something visible or measurable.** No slice is "refactoring".
2. **Every slice has an exit gate.** A slice without a gate is not a slice.
3. **No slice breaks a §23 budget.** A slice that does is a failed slice, even if it works.
4. **No slice regresses Appendix B.** Any regression is **GATE: RED**.
5. **Dependencies are stated.** A slice never assumes unfinished work.

**Ordering principle: design system → architecture → features.** The visual language is fixed
before components are built; the data, identity and storage contracts are fixed before
features depend on them. This is deliberate — retrofitting either is the most expensive
mistake available to this project.

**Baseline note.** The v0.813.0 code referenced throughout §25 and Appendix A **lives outside
this repository**, which is currently documentation-only. Phase A therefore begins by
establishing the code baseline here, not by assuming it.

## **34.2 Phase A — Foundations**

### **A0 · Repository bootstrap and baseline verification**

**Goal.** Make this repository the single source of truth and prove the M0 baseline.

**Deliverables**
* Import the v0.813.0 source here: `src/`, `data/kjv.txt`, `models/`, `tests/`, `Cargo.toml`.
* Re-run the regression suite locally and record the **real** pass count (Appendix A claims 47/47).
* Reconcile every "shipped" claim against actual code — each Appendix A row gets a
  *verified* / *not found* verdict.
* Remove the duplicated PRD file; repoint `README.md` at v2.1 (see Appendix C).

**Gate.** `cargo test` green on a clean clone; every Appendix A claim either evidenced by a
file path or downgraded to "unverified"; one PRD, one README, one roadmap.

**Depends on.** Nothing.

### **A1 · Design system — foundation (tokens and theme)**

**Goal.** Fix the visual language before a single component is written.

**Deliverables**
* A single `theme` module as the **only** source of colour, type and spacing values. No
  hard-coded hex, font size or padding anywhere else in the codebase.
* **Colour roles, not colour names:** `stage.background`, `stage.verse_text`,
  `stage.reference`, `operator.surface`, `operator.surface_raised`, `status.ok`,
  `status.warn`, `status.error`, `status.listening`, `accent`. Every role defined for both a
  **light** and a **dark** operator theme.
* **Two typographic scales:** a *stage* scale (congregation — large, high contrast, legible
  from the back of a room) and an *operator* scale (dense, information-first).
* Spacing and radius scales, plus elevation rules.
* **Two surfaces defined explicitly:** the **congregation stage** (projected, minimal chrome,
  no operator controls visible) and the **operator console** (dense, all state visible).
* Contrast verification: every text/background pair meets WCAG AA; the stage pair meets AAA.

**Gate.** A theme reference screen renders every token in both themes on both surfaces;
contrast ratios are recorded; no component yet exists that bypasses the token layer.

**Depends on.** A0.

### **A2 · Design system — components**

**Goal.** Build the reusable primitives the whole product is assembled from.

**Deliverables**
* Primitives: button (primary/secondary/ghost/danger), text field, toggle, select/dropdown,
  badge/chip, status pill, card, list row, divider, tooltip, modal, toast.
* **Product-specific components** — the ones that actually carry the design language:
  * `StageView` — the congregation surface (verse text, reference, translation, auto-fit).
  * `TranscriptFeed` — rolling live transcription with confidence shading.
  * `CandidateCard` — the confirm-queue unit: alternatives + **Approve · Correct · Dismiss**.
  * `ScriptureIndexRow` — timestamped reference, clickable to seek.
  * `StatusRail` — always visible: what is on stage, what is being heard, is it recording.
  * `RecordingIndicator` — state and elapsed time, never ambiguous.
* A **keyboard map** as part of the design system, not an afterthought: override is always one
  key away (§26), and the operator never has to hunt with a mouse during a service.

**Gate.** Every component renders in both themes at three window sizes; the keyboard map is
documented; `StatusRail` alone answers the §8 ten-second question.

**Depends on.** A1.

## **34.3 Phase B — Architecture**

### **B1 · Workspace and module architecture**

**Goal.** Fix crate and module boundaries before feature code accumulates.

**Deliverables**
* A Cargo workspace split by responsibility — e.g. `core` (parser, book model, verse
  resolution), `asr`, `audio`, `store` (SQLite), `stage` (rendering), `app` (wiring/UI).
* Dependency rule: **`core` depends on nothing but `std`** — no UI, no DB, no audio. This is
  what keeps the parser testable in microseconds.
* Error model: one error type per crate boundary; no panics on the live path; every failure
  surfaces as operator-readable language (§2).

**Gate.** `cargo tree` shows no upward dependency from `core`; the parser builds and tests
with `store`, `asr` and `stage` removed.

**Depends on.** A0.

### **B2 · Persistence layer — SQLite + FTS5**

**Goal.** Implement D-2: schema, migrations, repositories, full-text search.

**Deliverables**
* `rusqlite` with `bundled`; WAL mode; foreign keys on.
* A migration runner over `schema_migrations` — forward-only, additive.
* A repository per aggregate: settings, sermons, events, scripture index, transcript, edits.
* FTS5 virtual tables plus sync triggers for the three search surfaces in §33.3.
* **Export path:** a sermon exports as a self-contained folder (JSON + audio + transcript) so
  a church can back up or move its archive without the app.
* **Backup:** SQLite online-backup API to a dated file, with a documented restore.

**Gate.** Migrations run clean on an empty DB and on a DB one version behind; a sermon
round-trips to export and back with byte-identical audio and a matching index; FTS search
returns the expected rows for scripture, speaker and free text.

**Depends on.** B1.

### **B3 · Local identity and roles (deliberately minimal)**

**Goal.** Implement D-3 without building an account system.

**Deliverables**
* **No login.** The app opens straight into the operator console.
* A **role enum** (`Administrator`, `Operator`, `Speaker`, `Viewer`) that exists in config and
  in the UI permission model but is **not enforced** in M0–M2, because there is one local
  operator. Defining it now means M3 adds enforcement, not redesign.
* **Optional local passcode** guarding settings that change church-wide behaviour (retention,
  deletion, sharing defaults). Stored as a salted hash, never plaintext.
* macOS Keychain integration reserved for future secrets; no secret is written to the DB.
* A written statement on the settings surface: *"RhemaFlow runs entirely on this machine.
  Nothing about your services leaves it."*

**Gate.** No network code exists; no credential is stored outside the Keychain path; the role
model is unit-tested as data even though it is not enforced.

**Depends on.** B2.

### **B4 · File storage layer**

**Goal.** Implement D-4: one owner of every byte written to disk.

**Deliverables**
* A `storage` module that is the **only** code allowed to construct paths — no ad-hoc
  `PathBuf` joins anywhere else.
* Roots: app-data root (fixed) and library root (user-selectable, may be external).
* Recording writer: streaming WAV in M0, container swap in M1 behind the same interface.
* Model store: bundled, read-only, integrity-checked at startup.
* Retention policy: church-configured age/size limits with a **dry-run preview** before delete.
* Free-space pre-check at recording start; a hard stop with an honest message rather than a
  truncated recording.

**Gate.** Recording survives a simulated full disk with an honest error; the retention dry-run
matches what deletion actually does; changing the library root mid-archive migrates cleanly or
refuses clearly.

**Depends on.** B1.

### **B5 · Session state machine and event log**

**Goal.** One source of truth for "what is happening right now".

**Deliverables**
* An explicit session state machine: `Idle → Armed → Listening → Staged → Recording → Ended`.
* A single **append-only event log** per session. Every stage change, translation change,
  candidate, approval and correction is an event. The database (§33.3) is a *projection* of
  this log, not a parallel truth.
* **Deterministic replay:** a recorded session can be replayed through the parser offline to
  reproduce every decision — this is how parser regressions get diagnosed.
* All §24 metrics are computed from this log, not from scattered counters.

**Gate.** Replaying a captured session reproduces the same stage sequence and the same §7.2
index, timestamp for timestamp; no UI state exists that is not derivable from the log.

**Depends on.** B1, B2.

### **B6 · Settings, translation registry and licence records**

**Goal.** Make §6.4 and its licence constraint structurally enforceable.

**Deliverables**
* A settings store over §33.3 `settings`, with typed accessors and defaults.
* A **translation registry** where a translation cannot be enabled unless its `license` and
  `license_reviewed_at` fields are populated. KJV ships enabled; WEB is reviewed then added;
  nothing else is bundled without a recorded review.
* Default translation selection, per-service override, and the explicit-request path ("now
  let's read it in the NIV") all routed through the same registry.

**Gate.** A translation with an empty licence record cannot be enabled — enforced in code, not
by convention. The attempt produces an operator-readable refusal.

**Depends on.** B2.

### **B7 · Session logging and metric instrumentation**

**Goal.** Make §24 measurable from day one instead of retrofitted.

**Deliverables**
* A JSONL session log per service: every event with wall-clock and monotonic timestamps.
* Instrumented metrics: auto-stage rate, recognition precision, silent-failure count,
  honest-miss quality, reference latency (p95), operator touches, archive lookup time.
* A **local metrics view** — the church sees its own numbers. No upload, ever (§21).
* Latency measurement starts at speech-end detection, not at parse start, so the §23 ≤ 2.5 s
  budget is measured honestly end-to-end.

**Gate.** A 20-minute test session produces all §24 metrics without manual counting; the
silent-failure count is computable and is provably zero or a release blocker.

**Depends on.** B5.

### **B8 · Test harness, golden corpus and release gates**

**Goal.** Make Appendix B mechanical.

**Deliverables**
* The locked regression utterances become a **golden corpus** run in CI on every commit.
* A **parser fuzz corpus** for filler tolerance — the parser must not depend on any word list.
* A **latency harness** on M1 hardware asserting the §23 budgets.
* A **memory harness** asserting ≤ 350 MB RSS across a simulated 60-minute service.
* Gate definition: any Appendix B regression is **GATE: RED** regardless of other results.
* Process rule: every real mishear reported by a church becomes a locked test **in the same
  release** it is fixed in (§26).

**Gate.** CI fails the build on an Appendix B regression; the corpus runs offline with no
network; the latency and memory harnesses produce numbers, not impressions.

**Depends on.** B1, B5.

## **34.4 Phase C — M1 Feature Train**

| Slice | Scope | Exit gate |
|---|---|---|
| **C1 · Translation management and dropdown port** | Port the v0.812 dropdown onto the B6 registry | Switching translation re-renders the on-stage verse without interrupting the service; the licence guard still holds |
| **C2 · Audio input picker and auto-gain** | Device enumeration, live switching, auto-gain behind a manual override | Per §10: a device change takes effect within two seconds without restart, and the active device is always visible on the StatusRail |
| **C3 · ASR accuracy pass** | Whisper initial-prompt biasing with the 66 book names; post-ASR fuzzy correction against the book list using the §26 preaching-frequency tie-break | Appendix B utterances 1, 2 and 5 stay green; the mishears that motivated this pass become new locked utterances |
| **C4 · Scripture quotation recognition (§6.2)** | Quotation matching behind the confirm queue — never auto-staged above the operator's confidence setting | Per §6.2: a quotation whose first eight words uniquely match a KJV verse appears as a *labelled candidate*, not on stage |
| **C5 · Natural context commands (§6.3)** | "Let's go back to that verse", "the same passage", "compare that with Romans 8" resolved against stage history | Deictic phrases resolve to the correct prior reference when history is unambiguous, and **ask rather than guess** when it is not |
| **C6 · Rich-text stage (italics)** | Port italics handling from v0.812 into the A2 `StageView` | Emphasis renders correctly at every stage size without breaking auto-fit |
| **C7 · Regression expansion** | Every real mishear and operator correction collected during M1 becomes a locked utterance | The corpus grows monotonically; no locked utterance is ever removed |

## **34.5 Phase D — M2 Archive and Polish**

| Slice | Scope | Exit gate |
|---|---|---|
| **D1 · Sermon archive and search (§12)** | Archive browser over B2's FTS | Per §24: a referenced verse is findable in a past sermon in ≤ 30 s by scripture, speaker, date, series, topic or tag |
| **D2 · Post-service editing (§13)** | Corrections to transcript, identified references, titles, metadata, translation info and tags — all through the `edits` table | No correction destroys the original record; the original is retrievable after any number of edits |
| **D3 · Sermon timeline view (§7.3)** | Chronological timeline over `sermon_events`; selecting an entry seeks the recording | Every event kind named in §7.3 is represented and seekable |
| **D4 · Service modes (§9)** | Full Service · Sermon · Bible Reading · Custom | A mode change provably suppresses triggers in the excluded portions without restarting the session |
| **D5 · Service templates (§20)** | Save / apply / export templates | A template round-trips between installations and applies cleanly; preparation stays optional, never mandatory |
| **D6 · Branding and presentation styles (§6.7)** | Style editor over the A1 tokens, exported as a single portable file | Per §6.7: a style imported into a different installation renders identically |
| **D7 · Consolidated operator command centre (§8)** | Unify status, transcript, candidates, stage controls, translation, history and recording into one workspace | Per §8: a first-time operator answers "what is on stage, what is it hearing, is it recording" within ten seconds |
| **D8 · Suggested content — "three things" (§7.4)** | Strict enumerated-pattern detection first; semantics later | Per §7.4: N between 2 and 5 raises exactly one card listing all N items; nothing is staged without approval |

## **34.6 Phase E — M3 Cloud, Accounts, Teams (deferred)**

**Not to be started until M2 is trusted in real services.** Phase E is where the local-first
boundary is deliberately widened — and only there.

* **E1 · Accounts and roles (§16)** — the B3 role enum becomes enforced. Adds `users`,
  `churches`, `roles`, `sessions` additively; no M0–M2 table is reshaped.
* **E2 · Multi-service and multi-location (§17)** — service and location scoping on `sermons`.
* **E3 · Cloud sync and sharing (§14)** — explicit, opt-in, and never on the live path. Local
  stays authoritative; the cloud is a convenience layer, per §15.
* **E4 · Language expansion (§18)** — additional spoken languages and Bible-language pairs.
* **E5 · Adoption metrics (§24)** — measurable only once accounts exist, and only with
  explicit church consent (§21).

## **34.7 Cross-Cutting — Release Engineering**

Not a phase; a discipline running alongside every phase.

* **X1 · Packaging and signing** — notarized `.app`/`.dmg`, Apple Silicon. Gate: installer
  ≤ 100 MB (§23), ASR model bundled once, no build artifacts shipped (§26).
* **X2 · Onboarding and permissions** — the one-time guided microphone permission step with a
  visible state indicator (§26 risk: the app must never look broken on first run).
* **X3 · Performance budget gate** — latency, parse time, memory and installer size asserted
  in CI against §23. A release that breaks a budget is a failed release.
* **X4 · Documentation upkeep** — README, PRD and code stay in agreement. Appendix C is the
  first instance of this discipline, not the last.

---

# **Appendix A — Current-State Map (verified against v0.801.2)** *(rewritten in v2.1)*

> **This appendix was previously wrong.** It cited `src/engine.rs`, `src/session.rs`,
> `src/asr.rs` and `src/rec.rs`. **None of those paths exist.** The real codebase is a Cargo
> workspace of four crates. It also claimed 47 tests; the real count is 64, and several
> capabilities listed as "planned" had already shipped. Every row below has been re-verified
> against `Desktop M1 app/RhemaFlow-D-v0.801.2.zip`.

**Baseline:** v0.801.2 · workspace `rf-bible`, `rf-core`, `rf-asr`, `rf-app` ·
`egui`/`eframe` `=0.28.1`, `cpal` `=0.15.3`, `whisper-rs` `=0.13.2` ·
model `ggml-tiny.en.bin` (77 MB) · **64/64 tests green**.

| PRD capability | State | Verified code evidence |
|---|---|---|
| Structural reference parsing (filler-tolerant) | shipped | `crates/rf-core/src/parser.rs` |
| Digit-split / number-word parsing ("three sixteen" → 3:16) | shipped | `crates/rf-core/src/parser.rs` |
| Fuzzy book matching with preaching-frequency tie-break | shipped | `crates/rf-core/src/books.rs`, `parser.rs` |
| Honest out-of-range + "did you mean" | shipped | `crates/rf-core/src/parser.rs` (`RefError`, `Suggestion`) |
| Bare "verse N" / relative-to-stage jumps | shipped | `crates/rf-core/src/parser.rs` (`ParseContext`) |
| **Quotation recognition (§6.2)** | **shipped** | `crates/rf-bible/src/lib.rs` — leading n-gram index → confirm queue |
| **Context resolution incl. "that verse" (§6.3)** | **shipped** | `crates/rf-core/src/parser.rs` |
| Voice command grammar (nav, zoom, fullscreen, clear, read) | shipped | `crates/rf-core/src/commands.rs` (11 tests) |
| Scripture-vs-command guard | shipped | `crates/rf-core/src/commands.rs` |
| **Translation management (§6.4)** — KJV **+ BBE** + `from_translation()` | **shipped** | `crates/rf-bible/src/lib.rs` (9 tests); `kjv.json`, `bbe.json` |
| Licensed-translation scaffold (NIV/AMPC recorded honestly, falls back to KJV) | shipped | `crates/rf-bible/src/lib.rs` |
| Confirm queue + confidence floor | shipped | `crates/rf-app/src/state.rs` (`QueuedDetection`), `ui.rs` |
| **"Three things" sermon points (§7.4)** | **shipped** | `crates/rf-core/src/parser.rs` → `StageKind::Points` |
| **Operator command centre (§8)** | **shipped** | `crates/rf-app/src/ui.rs` — three-zone layout |
| Offline ASR (whisper tiny.en, beam search 5, domain prompt, deterministic) | shipped | `crates/rf-asr/src/engines.rs` |
| VAD with pre-roll + adaptive noise floor | shipped | `crates/rf-asr/src/vad.rs` (3 tests) |
| Mic device picker + input level meter | shipped | `crates/rf-asr/src/capture.rs`, `ui.rs` |
| Offline recording + timestamped scripture events | shipped | `crates/rf-app/src/recorder.rs`, `actions.rs` |
| Human-readable `index.md` + `events.jsonl` + `transcript.txt` | shipped | `crates/rf-app/src/actions.rs` |
| Full KJV embedded (31,102 verses), build-validated | shipped | `crates/rf-bible/assets/kjv.json` |
| Stage presentation, auto-fit, fade, chapter-only badge | shipped | `crates/rf-app/src/stage.rs`, `theme.rs` |
| Stage zoom (buttons / keys / voice, persisted) | shipped | `ui.rs`, `stage.rs` |
| Scripture read-aloud with natural voice picker | shipped | `crates/rf-app/src/tts.rs` (4 tests) |
| Companion mode (§19) — standalone stage window | shipped | `crates/rf-app/src/stage.rs` |
| Cathedral Dark design system | shipped | `crates/rf-app/src/theme.rs` |
| One-command bootstrap + checksum-verified model setup | shipped | `run.sh` |
| Sermon archive browser + search (§12) | planned M2 | — (no database exists yet) |
| Post-service editing (§13) | planned M2 | — |
| Timeline view (§7.3) | planned M2 | — (events are recorded; no view) |
| Service modes (§9) · templates (§20) · branding editor (§6.7) | planned M2 | — |
| Cloud, accounts, sharing, multi-site | planned M3 | — |
| Signed/notarized `.app` bundle | not started | `run.sh` only — see slice X1 |

**Test breakdown:** `rf-core` 43 (`tests.rs` 30, `commands.rs` 11, `books.rs` 2) ·
`rf-bible` 9 · `rf-asr` 8 (`engines` 2, `resampler` 3, `vad` 3) · `tts` 4 = **64**.

**Version drift to fix:** the workspace version, `theme.rs` and `README.md` all say
**v0.801.2**; §25 previously said v0.813.0; `docs/TESTING.md` still quotes 47 tests.
Slice **X4** makes this a release-time audit.

---

# **Appendix B — Locked Regression Utterances (must stay green forever)**

Every real-world failure a user actually hit becomes a permanent test. Current set
(the screenshot set that produced v0.813.0):

1. "1st Corinthians five, for seventeen" → honest out-of-range + suggests 2 Corinthians 5:17 (1 Cor 5 has 13 verses)
2. "Perverse seventeen" → corrected to "verse seventeen" → relative jump
3. Bare "verse 17" → relative jump within the on-stage chapter
4. "exit full screen" / ASR mishears of it → fullscreen exits
5. "let's go to john three sixteen" → John 3:16 staged
6. Chapter-only "First Corinthians chapter 13" → chapter 13 verse 1, marked chapter-only

A release that regresses any of these is GATE: RED regardless of other results.

> **v2.1 note.** The list above is the *origin* set. The shipped corpus in v0.801.2 is
> **64 tests** (`rf-core` 43 · `rf-bible` 9 · `rf-asr` 8 · `tts` 4), covering every §6
> acceptance utterance, the full voice-command grammar, all 15 numbered books in every
> prefix form, the exact-beats-fuzzy rule, quotation handling, `[BLANK_AUDIO]` / `[MUSIC]`
> suppression, and ordinary speech producing nothing. `docs/TESTING.md` still quotes the
> old 47 — see slice X4. The six utterances above stay the canonical named set.

---

# **Appendix C — Folder Review and Documentation Debt** *(new in v2.1)*

Recorded so the review is not repeated and the debt is not forgotten. **Two rounds** were
performed: the documentation-only folder, then the shipped v0.801.2 codebase.

## **C.1 Round 1 — the documentation folder**

| File | Lines | Verdict |
|---|---|---|
| `PRD.md` | 478 → v2.1 | **Authoritative.** PRD v2.0, now extended by §25a, §33, §34 |
| `docs/RhemaFlow-PRD-v2.0.md` | 478 | Byte-identical duplicate — **collapsed to a pointer stub** |
| `docs/RhemaFlow - Product Requirements Document.md` | 833 | PRD v1.0 — superseded, retained for history |
| `README.md` | 118 | Was stale (linked v1.0, "not yet started") — **rewritten** |
| `.gitignore` | 1 | `.DS_Store` only — **rewritten** for Rust/`target/`, `*.db`, recordings, `models/*.bin` |
| Git history | 1 commit | `7c71dff` — docs only, `master` only |

## **C.2 Round 2 — the v0.801.2 codebase**

`Desktop M1 app/RhemaFlow-D-v0.801.2.zip` (73 MB, 59 files) was opened and read.

| Fact | Value |
|---|---|
| Version | **v0.801.2** — not v0.813.0 as §25 claimed |
| Layout | Cargo workspace: `rf-bible`, `rf-core`, `rf-asr`, `rf-app` |
| Stack | `eframe`/`egui` `=0.28.1`, `cpal` `=0.15.3`, `whisper-rs` `=0.13.2` — matches §23 exactly |
| Tests | **64/64 green**, not 47 |
| Storage | `~/RhemaFlow-Services/<ts>/` + `~/.rhemaflow/settings.json` — **no database** |
| Recording | 16 kHz mono WAV, **~115 MB/h** — well inside the ~300 MB/h budget |
| Design system | **Cathedral Dark** already exists in `theme.rs`; dark-only, appearance-named colours |
| Backlogs | `docs/ACCURACY.md` (20 ranked accuracy items) and `docs/IDEAS-100.md` (115 items, 57 shipped) are **more current than §25** |

## **C.3 Findings**

1. **The code is real and in better shape than the PRD credited.** The workspace split is
   exactly what §34.3 proposed; `rf-core` is already pure logic with no I/O. Several
   capabilities listed as "planned" had shipped: quotation recognition (§6.2), "that verse"
   (§6.3), translation management incl. BBE (§6.4), "three things" (§7.4), the command
   centre (§8).
2. **Appendix A cited paths that do not exist.** `src/engine.rs`, `src/session.rs`,
   `src/asr.rs`, `src/rec.rs` — none present. Rewritten in v2.1 with verified paths.
3. **The test count was wrong and inconsistent.** PRD and `TESTING.md` said 47; `README.md`
   and `ACCURACY.md` said 64. The real count is **64**.
4. **Version strings drifted.** Code, `theme.rs` and `README.md` say v0.801.2; §25 said
   v0.813.0. `docs/PRD-v2-review.md` had already flagged this and it was not fixed.
5. **§23 named the stack but not storage, identity or file handling.** §33 closes that.
6. **A whole feature ships with no PRD section: TTS read-aloud.** Plus the voice command
   grammar, the simulator, zoom, BBE, `index.md` and `run.sh`. Now catalogued in §25a.
7. **There is no database.** The flat-file record is already portable and human-readable,
   so D-2 is *additive* — which is why D-8 exists and why B2's gate is "delete the DB and
   rebuild from the folders".
8. **§24 defines metrics with no persistence behind them.** A live HUD exists
   (`IDEAS-100` #100); nothing is stored. Slice B7 fixes this.
9. **The `run.sh` model download is the one network call.** Install-time only, checksum
   verified, never on the live path — a sanctioned D-6 exception that must stay documented.
10. **Three competing roadmaps.** §25, `docs/ACCURACY.md` and `docs/IDEAS-100.md` all
    sequence work, and the two docs are more current. Open decision 5 in
    `IMPLEMENTATION-PLAN.md`.

## **C.4 Debt and disposition**

| Debt | Disposition |
|---|---|
| Duplicate v2.0 PRD in `docs/` | **Done** — collapsed to a pointer stub |
| README linked v1.0, said implementation had not started | **Done** — rewritten for v2.1 |
| `.gitignore` covered only `.DS_Store` | **Done** — rewritten |
| Appendix A cited non-existent paths | **Done** — rewritten against v0.801.2 |
| Test count 47 vs 64 | **Done** — 64, with a per-crate breakdown |
| §25 said v0.813.0 | **Done** — corrected to v0.801.2 |
| Shipped-but-undocumented features | **Done** — catalogued in §25a; still need real PRD sections |
| v1.0 PRD | Keep in `docs/` as history; marked superseded |
| Version-sync discipline | **Open** — slice X4 |
| Three competing roadmaps (§25 / ACCURACY / IDEAS-100) | **Open** — decision 5 |
| No database | **Open** — slice B2 |
| No signed `.app` | **Open** — slice X1 |
