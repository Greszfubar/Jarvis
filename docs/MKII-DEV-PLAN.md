# JARVIS MKII — Phased Development Plan

*Personal AI superintelligence · Gresz Industries · for Evan*

This plan turns everything we scoped into a buildable roadmap. It runs **Demo → Launch → Cognition → Full**, following the Demo/Launch/Full sequence you set with a cognitive layer folded in between Launch and Full, with the dull-but-critical safety scaffolding (rollback, permissions, secrets, budget) built *first* so that Patch's self-editing and the full-access installable agents never get a chance to wreck the system. Where you had no preference, I've committed to a concrete recommendation and noted the alternative — override anything freely.

Two principles shape the sequencing:

1. **Money comes early.** You currently need income, so a real gradeUP earning-agent lands inside the Demo phase, not deferred to Full.
2. **The cinematic world is the reward, not the foundation.** The island flythrough, the hive, the globe modes, and the brain visualisation are spectacular but they sit on top of a working voice + agent + memory core. We build the spine first, then dress it.

---

## 0. Recommended stack

One unified Electron app spans your three screens; a Python backend orchestrates models and agents and talks to the front end over a local websocket. This gives you the fastest cinematic iteration (web 3D) plus deep system control (kiosk, multi-monitor, shortcut trapping).

| Layer | Recommendation | Alternative |
|---|---|---|
| App shell (kiosk, 3-screen, traps Cmd-Tab/Mission Control) | **Electron** | Tauri (lighter, Rust) |
| Front-end + all 3D (globe, island, face, brain) | **React + react-three-fiber (Three.js)** | Unity, if you later want AAA visuals |
| Backend / agent orchestration | **Python (FastAPI) + async agent workers** | Node |
| Conversational voice brain (always-on) | **Claude Sonnet** (streaming) | — |
| Reasoning brain (JARVIS, on escalation) | **Claude Opus 4.8** | — |
| Coding / build agents | **Codex/GPT + Claude** | — |
| Local model (simple tasks, Apple-Silicon native) | **Qwen2.5 / Llama 3.3 via Ollama or LM Studio (MLX)** | — |
| Speech-to-text | **Deepgram Nova** (streaming, low latency) | Local Whisper (private, slower) |
| Text-to-speech | **Cartesia Sonic** (lowest latency) | ElevenLabs Flash (higher quality) |
| Hand/gesture tracking from OBSBOT feed | **MediaPipe Hands** | — |
| Memory — raw store | **Files on 6TB + SQLite index** | — |
| Memory — semantic recall | **LanceDB** (embedded vector store) | Chroma / pgvector |
| Embeddings | **Voyage or OpenAI embeddings** | local embedding model |
| Secrets | **Local encrypted vault** (age/SOPS or Keychain-backed) | — |
| Snapshots / rollback | **Git + GitHub**, auto-commit per Patch change | — |
| Budget governor | **Custom credit-accounting middleware on every model call** | — |

On latency: a cloud voice round-trip is realistically ~0.5–1.5s, not literally zero. We make it *feel* instant with streaming STT/TTS and barge-in (you can talk over him). That's the right target.

---

## Cross-cutting architecture (built in Phase 0, used everywhere after)

These four systems are non-negotiable and come before any agent gets real power.

**The permission gate.** Every external or destructive action — sending email, committing to GitHub, autofilling a card, modifying calendar, installing an agent — routes through one chokepoint that requires your spoken confirmation by default. JARVIS is the guardrail; nothing reaches the outside world without passing through him and, for anything irreversible, through you. CVV and final page-accept stay manual, always.

**The rollback spine.** Patch commits a snapshot to GitHub *before* every change to JARVIS's code. A health check runs after each change; if the new code fails, Patch auto-reverts to the last known-good snapshot instead of looping on the fix, writes a report, and hands it to JARVIS to read to you or pull up on the Stage. Self-modifying systems brick themselves without this — so it exists from day one.

**The vault.** All credentials (email, GitHub, card, API keys) live in a local encrypted vault. Nothing in plaintext, nothing in the repo.

**The budget governor.** Middleware wraps every model call and accounts credits against caps: a hard **nightly cap** (which the night cycle is designed never to approach) and an overall **£5,000/month ceiling**. When a cap is near, JARVIS throttles and tells you rather than silently overspending.

---

## Phase 1 — DEMO: "It's alive"

**Goal:** the moment the face talks back and an agent earns money. Your two demo centrepieces — *the interface* and *agents earning money* — proven in one build. This is for you; it has to feel alive.

**The face + voice loop**
- Face screen (Screen 1): white-pixel face on black, your hand-designed expression set, JARVIS choosing an expression by mood and when speaking. White by default; colour-shifts and shows speaker title/rank/district when a Rank 2 agent speaks.
- Streaming STT (Deepgram) → Sonnet → streaming TTS (Cartesia) with barge-in.
- Voice modes: **Active** (responds to everything, as specified), **Sleeping** (always listening, responds only to "Jarvis…" actions), **Muted** (face screen off; tap face to unmute).

**The Stage + globe (Screen 3)**
- The blue, Iron-Man-style 3D globe as the default Stage view, naturally spinning, grabbable.
- Stage primitives JARVIS will reuse forever: open an app/view, draw arrows, highlight, zoom. Built here once.

**Screen 2 — brain & vitals (real telemetry from the start)**
- Live vitals: what's running, what's healthy, what failed.
- 3D brain model whose regions light up wired to *real* activity — which agent/model is firing right now. Real telemetry, not animation, so it doubles as your failure-spotting dashboard.

**The first earning agent (gradeUP)**
- One real business agent — Support or Marketing — doing genuine draft-and-approve work on gradeUP. Because gradeUP serves GCSE students (minors), **every student-facing output is human-reviewed before it goes out. Hard rule, no exceptions.**
- This is what makes "agents earning money" real in the demo rather than a promise.

**App shell (kiosk, but with an escape hatch)**
- Electron app spanning all three screens. *During development, do not fully lock the kiosk* — you're building on the same M5 mini, and trapping Cmd-Tab on your only dev machine would brick your workflow. Keep a secret unlock phrase and SSH access. Full lockdown lands in Phase 2.

**Demo done when:** you speak, the face emotes and replies instantly-feeling, the globe is live on the Stage, Screen 2 shows real activity, and a gradeUP agent has produced approved, shippable work.

---

## Phase 2 — LAUNCH: the working second brain

**Goal:** JARVIS becomes genuinely useful day-to-day — memory, the model aggregator, the night cycle, the core Rank 2 agents, and the business engine. This is the version you *live in*.

**Memory**
- Store-everything pipeline: raw capture to the 6TB drive, end-of-day summarisation (context-window-style compression for the low-value parts, full retention for the rest), cloud backup.
- Recall = LanceDB semantic search + SQLite structured queries + raw files, surfaced as an **interactable context page JARVIS pulls onto the Stage**.
- **Separate memory per agent; JARVIS is the only one who sees all.** "Forgetting" means not surfacing, not deleting — except where you explicitly say delete.

**The aggregator / router**
- Rules-based classifier routes each task: local model for simple, Codex/Claude for advanced, Opus 4.8 for JARVIS-level reasoning — Opus invoked *when needed*, not always-on, with Sonnet carrying conversation.

**Rank 2 agents — defined up front**
- Lock the roster and domains now (Ultron, Patch, Vision, + the rest), each owning a specific area and able to spawn Rank 3 subagents. Patch ships with the rollback spine from Phase 0 fully wired.

**The night cycle (stim-gated)**
- A timer fires every 20–60 min; JARVIS checks for changes or needed actions; **if nothing, the timer rolls on and spends zero credits.** Only a real stim spends.
- Cycles: **Dreaming** (consolidate the day into memory), **Planning** (next-day plan + morning brief), **Pondering** (research things you said that it didn't fully grasp), **Activating** (faintly surface anything dangerous/important on the Stage), **Organising** (email, calendar, tasks, routines).
- Overnight, JARVIS **may send email and modify your calendar** — both visible to you. The nightly budget cap governs all of it and is designed never to be hit.

**The business engine (Los Cielos de Gresz · gradeUP)**
- Marketing, Sales, Support, Dev, and Manager agents working as a unit. Dev agent operates against the gradeUP GitHub repo (Expo / React Native front end, Clerk auth).
- Agents may handle parts unsupervised; **all student-facing output stays human-reviewed.**
- Success metric, wired into the business view: more installs/subscriptions, faster feature shipping, support handled so you're freed up.

**Input layer**
- Gesture control via MediaPipe on the OBSBOT 2D feed — relative, trackpad-style, used only when you're seated with arms on the armrests. **Treat as secondary/experimental: voice is the spine (~96%).**
- Magic Trackpad letter-pattern drawing for text input (incl. CVV entry); physical keyboard/mouse unlock only on voice command.

**Kiosk lockdown finalised** — now that the system is stable, enable auto-launch on boot, fullscreen, and Cmd-Tab/Mission Control trapping, keeping one secret unlock path so you're never locked out of your own machine. macOS notifications/updates/other apps get surfaced by JARVIS on the Stage rather than exposed.

**Launch done when:** JARVIS remembers, routes intelligently, runs the night cycle within budget, organises your life, and the gradeUP agents are moving the metric.

---

## Phase 2.5 — COGNITION: the superbrain layer

**Goal:** turn a very capable assistant into a genuine second brain. This phase adds the connective tissue — the systems that link what JARVIS knows, learn how *you* think, and steer you rather than merely serve you. It sits here deliberately: it needs Phase 2's memory to exist, and it makes everything in Phase 3 smarter. Skip it and JARVIS gets bigger over time; build it and JARVIS gets smarter every day just by living with you.

**The knowledge graph (the highest-leverage single item in the entire plan)**
- A personal graph of people, projects, concepts and decisions and their relationships, built beneath the existing memory store — association, not just retrieval.
- Add **Connecting** as a night cycle: JARVIS hunts for non-obvious links across your whole history and carries the good ones into the morning brief.
- Wire the graph into Screen 2's brain visualisation so connections light up as they form — same work, aesthetic and functional at once.

**The absorb pipeline**
- Ingest chosen knowledge — books, papers, videos, podcasts, your own notes — distilled, stored, and graphed so it connects to everything else. Without this JARVIS knows your life but not what you're deliberately learning.

**The model of Evan**
- **Personal constitution:** a continuously refined profile of your values, goals, recurring mistakes, energy patterns and writing voice — so JARVIS can advise as you, challenge you on known mistakes, and draft in your real voice.
- **Decision journal:** every meaningful decision logged with its rationale *at the time*, and later reviewed against how it actually played out.

**Goal steering**
- Long-term arcs (gradeUP revenue, JARVIS itself, life direction) held explicitly, with today's actions connected to them and drift called out. Ties directly to the money reality.

**The hive turned inward**
- Reuse the Phase 3 hive pattern against your *own* decisions: premortems, devil's advocate, three perspectives plus a judge on choices you're stuck on.

**Ubiquitous capture + cognitive state**
- Phone app capture (voice memos, photos, screenshots) flowing into memory and processed overnight.
- Wearable signals (sleep, HRV) used to time work to your actual capacity, not just for the weekly health check.
- Spaced repetition to push learning into your biological memory.
- Relationship layer: people, last discussions, follow-ups, pre-call briefings.

**Metacognition**
- A reflection loop where JARVIS reviews where it misjudged you and updates the model of you — Patch for cognition rather than code — plus explicit epistemic honesty (guessing vs. knowing) so you can trust it with real decisions.

**Cognition done when:** JARVIS surfaces a connection you genuinely hadn't made yourself, drafts in your voice convincingly, and tells you unprompted that you're drifting from what matters.

---

## Phase 3 — FULL: the cinematic world

**Goal:** the Gresz Industries universe you designed, as a literal navigable interface, plus the remaining intelligence systems. This is where it becomes the movie.

**Port Calvera — the navigable island**
- Fly-through 3D island (AI-3D pipeline + your hand-fixing), three cities skinning real functions:
  - **Nova Calvera (capital):** *Calvera Synthesis Works* — the Planner → Manager → Builder agent factory producing installable agents, each running in the **island-page sandbox** before its Install button grants real access; *Voz de Calvera* news; the *Government Building* where the mayor agent manages "laws" (your config/rules) with images and written records.
  - **Alto Norte (tech city):** *Citadela Jarvis* (live JARVIS task list + Patch's fix console); *Los Cielos de Gresz* (the business view from Phase 2, now in-world); *Colmeia Gelada* — **the hive**: on escalation only, 3 independent Codex/Claude responses + a judge model that synthesises the best answer from them.
  - **Porto das Velas (port):** finance and money-flow view — accounts, payments, the felt pulse of money in and out.

**Globe modes (full set)**
- Weather (heat / wind / rain) from real API sources; Travel (flights, high-scale and low-scale directions); News / Wars / Radio — with the rule you set: anything not cross-confirmed across sources never goes on the map.

**Brain model — full visualisation** of JARVIS's active regions, evolved from the Phase 1 telemetry baseline.

**Life systems**
- **Health:** weekly check-up with real guidance, fed by a wearable (to acquire) + self-report + camera when needed. *Health guidance is sensitive; we scope its limits carefully when we get there.*
- **House monitoring:** the home-inventory video pass (taken with no one else present, full consent) → object tracking and care reminders (e.g. water plant X every Y).

**Later nice-to-haves (kept in development, not blocking):** autonomous flight booking + self-check-in, Google/Apple Maps phone hand-off, radio tuner.

**Polish:** the boot sequence (double-clap → expanding rings → "directed by Gresz Industries" → "JARVIS OS Launching"), full expression set, sound design.

---

## Risk flags (shaping the plan, not blocking it)

- **Gestures from a 2D camera.** The OBSBOT Tiny 3 Lite gives a tracked 2D feed, not depth. MediaPipe can infer pinch, but reliability at room distance across a moving PTZ frame is the real unknown. Voice stays primary; gestures stay secondary and get validated in Phase 2 before you lean on them.
- **Self-modifying code.** Patch is powerful and the single biggest brick-risk. The rollback spine (Phase 0) is what makes it safe; never let Patch run without it.
- **Full-access installable agents.** The sandbox (Phase 3) and the permission gate (Phase 0) are the two things standing between a flawed agent and your data. Both must precede any agent getting real machine access.
- **Minors.** gradeUP's users are children. The human-review rule on all student-facing output is a hard safety boundary, not a phase task — it's true from the first gradeUP agent onward.
- **Don't lock yourself out.** You're building on the production mini. Kiosk lockdown is staged last, with a permanent secret escape path.

---

## At 15 hours a week

The phases are ordered so value compounds: after Phase 1 you have something alive and earning; after Phase 2 you have something you actually rely on; Phase 3 is the world. If a week is tight, protect the spine (voice, memory, agents, safety) over the spectacle — the spectacle is far cheaper to add once the spine holds.

One addition to the priority rule above: if a week is tight in Phase 2.5, protect the **knowledge graph and the model of Evan** over the smaller cognitive modules. Those two are force-multipliers on everything else in the system; the rest are useful but additive.

The very next build steps, in order: stand up the repo + GitHub auto-snapshot, the encrypted vault, the budget governor, and the permission gate (Phase 0) → then the face + Sonnet voice loop. That gets you to the first "it's alive" moment on the shortest safe path.
