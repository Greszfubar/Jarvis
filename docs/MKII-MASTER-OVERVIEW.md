# JARVIS MKII — Master Overview

*A personal AI superintelligence · Gresz Industries · built for and operated by Evan*

This is the canonical description of the whole system: what JARVIS MKII is, how it's structured, how you interact with it, and how its world fits together. Where the development plan answers *when and how to build*, this document answers *what it is* — the design bible you return to when any single piece needs to be reconciled with the whole.

---

## 1. What JARVIS MKII is

JARVIS MKII is a personal AI superintelligence that acts as a second superbrain for Evan's life. It is both deeply functional and unapologetically cinematic — an Iron-Man-grade operating environment that thinks, remembers, plans, builds, earns, and speaks. It is proactive by design: it reaches out to you as much as you reach out to it, the way the AI in the films does, rather than waiting passively for commands.

It serves three intertwined purposes:

- **A second brain** — it holds your whole life in memory, organises it, and surfaces the right thing at the right moment.
- **A working engine** — it runs real agents that do real work, including earning money through your business.
- **A showcase** — it is personal branding made tangible: proof, to you first and to clients and onlookers later, of what you can build.

It is for one person: **Evan**. Nobody else operates it, and its memory is private and hidden.

---

## 2. The physical setup

JARVIS MKII runs on a single **M5 Mac mini Max**, driving **three screens** and seeing the room through one **OBSBOT Tiny 3 Lite** PTZ camera that auto-tracks you in 4K and can pan to cover the whole space from any seat. Text, when needed, is drawn as letter-patterns on a **Magic Trackpad**. The room itself is arranged so JARVIS can see what you're doing from anywhere in it.

The whole experience is **one unified app spanning all three screens**. It launches on boot into fullscreen kiosk mode and traps Cmd-Tab and Mission Control, so you never leave it — macOS runs underneath but is never exposed. Anything macOS would normally surface (notifications, updates, other apps) is brought *into* JARVIS and shown on the Stage rather than handed back to the desktop. A single secret unlock path always exists so you're never locked out of your own machine.

---

## 3. The three screens

### Screen 1 — The Face

JARVIS's face: white pixels on a black screen, rendered as hand-designed expressions that JARVIS chooses according to its mood and to whether it's speaking. The face is white when JARVIS itself speaks. When a **Rank 2 agent** speaks to you instead, the face changes colour and displays that speaker's title, rank, and district. Muting JARVIS turns the face screen off; tapping the face again unmutes.

### Screen 2 — Brain & Vitals

The diagnostic and self-awareness screen, in three parts:

- **Vitals** — the live health of everything running, so a failure anywhere is visible at a glance.
- **The brain** — a 3D model of JARVIS's mind whose regions light up wired to *real telemetry*: whichever agent or model is actually firing right now. It is both spectacle and genuine failure-spotting instrument.
- **The AI register** — every AI in the system at scale, obsidian-styled, showing each one's health, rank, and title.

### Screen 3 — The Stage

The adaptive, interactive surface where JARVIS shows you what it's doing and what it wants you to see. It **defaults to the 3D globe** but is fully JARVIS-controllable: it can open and edit apps on the Stage, draw arrows, highlight text or objects, zoom in, render its own graphics, and surface anything it wants you to look at. The Stage is also where payment pages, context-recall pages, the navigable island, and surfaced macOS items appear. It is, in effect, JARVIS's hands.

---

## 4. How you interact

**Voice is primary — roughly 96% of all interaction.** JARVIS is always listening and operates in three modes:

- **Active** — responds to everything you say.
- **Sleeping** — still running and still listening, but only responds when you address it with a "Jarvis…" action.
- **Muted** — hears nothing; face screen off. Tap the face to unmute.

**Gestures are secondary**, used only when something manual is needed and you're seated with your arms on the armrests. Tracked from the OBSBOT's 2D feed, they map relatively, like a trackpad, with a faint trail following your fingers:

- **Slide** — move the cursor; **Click** — pinch; **Slide + Click** — pinch then move; **Scroll** — two fingers; **Zoom** — all fingers out-then-in / in-then-out.

**Text** is entered by drawing letter-patterns on the Magic Trackpad — used for rare secure fields such as a card CVV. The physical keyboard and mouse stay locked until you say "Jarvis, allow me to use my keyboard and mouse," with the keyboard always available as a fallback.

---

## 5. The intelligence core

JARVIS doesn't run on one model — it runs on a routed stack:

- **Conversation** is carried by an always-on lightweight model (**Claude Sonnet**), so talking to JARVIS feels instant.
- **Reasoning** escalates to **Claude Opus 4.8** — JARVIS's true brain — only when a task genuinely needs it, rather than always-on.
- **Simple tasks** route to a **local model** running natively on the mini.
- **Advanced work** routes to **Codex and Claude**.

A **rules-based classifier** (the aggregator) decides where each task goes, keeping routing fast and cheap rather than spending a model call just to choose a model.

For the hardest problems, JARVIS escalates to **the hive**: three independent responses from Codex/Claude are generated, and a separate judge model synthesises the single best answer by combining them. The hive is reserved for genuine escalation, not everyday questions.

---

## 6. The agent hierarchy

JARVIS commands a ranked organisation of AIs.

| Rank | Who | Role |
|---|---|---|
| **Rank 1** | **JARVIS** (Opus 4.8) | The mind. Commands all Rank 2 agents, sees *all* memory, and is the safety guardrail — every consequential action passes through him, and through you. |
| **Rank 2** | Named agents — **Ultron, Patch, Vision**, and others, defined up front | Each owns a specific domain, holds real code/config and account access when needed, and can spawn Rank 3 subagents. |
| **Rank 3** | Subagents | Spun up by Rank 2 agents to handle pieces of a job. |

An **agent** here is an AI with a defined functionality that JARVIS (or a Rank 2 agent) can send prompts to and have complete a task. Newly built agents are produced inside the world's agent factory, run first in a **sandbox**, and only receive real machine access when you press their **Install** button — after which JARVIS can call them like any other Rank 2 capability.

**Patch** is the special case: the agent that edits JARVIS's own real code and config to keep him functional. Patch is powerful and therefore the single biggest risk in the system, which is why the rollback spine (below) wraps everything it does.

---

## 7. Memory

JARVIS **remembers absolutely everything** unless you tell it to delete something. Near the end of each day it commits the day to memory, summarising the low-value parts the way a context window compresses, while the majority is retained in full. Everything lives on the **6TB drive** and is backed up to your cloud drive; the store is private and hidden, seen by no one.

Memory is **per-agent**, with **JARVIS as the only one who can see all of it**. Recall draws on a mix — semantic vector search, structured queries, raw files, and the knowledge graph described in the next section — and JARVIS presents results as an **interactable context page it pulls up on the Stage**. "Forgetting" means choosing not to surface something rather than deleting it; true deletion only happens on your explicit instruction, and JARVIS only discards information it judges it will never need to recall.

---

## 8. The cognitive layer — what makes it a *super*brain

Memory stores; the cognitive layer *thinks*. This is the connective tissue that turns a very capable assistant into a genuine second brain: systems that link what JARVIS knows, learn how Evan specifically thinks, and actively steer him rather than passively serving him. These are force-multipliers on everything else in this document — without them JARVIS gets bigger over time; with them it gets **smarter every day just by living with you**.

### The connective layer (the core of it)

Beneath memory sits a **personal knowledge graph** — not merely vector search, but an actual web of people, projects, concepts, decisions, and how they relate to one another. A brain's real superpower is association: noticing that something said three weeks ago bears on something today, and surfacing the link you would never have made yourself.

The night cycle gains a cycle for exactly this — **Connecting** — in which JARVIS hunts for non-obvious relationships across your entire history and brings the worthwhile ones to the morning brief: *"These two ideas you had a month apart are the same idea."* The Brain screen (Screen 2) visualises this graph lighting up as connections form, so the aesthetic and the function are the same thing.

### The absorb pipeline

Memory records what happens *to* you; the absorb pipeline ingests knowledge you *choose*. Feed JARVIS a book, paper, video, podcast, or your own notes and it distills, stores, and graphs the contents so they connect to everything else it knows. Without this, JARVIS knows your life but not the knowledge you're deliberately building into yourself.

### The model of Evan

This is what makes it a *second* brain rather than a generic one — a living model of how you specifically think, refined continuously:

- **The personal constitution** — your values, goals, recurring mistakes, energy patterns, and writing voice. It lets JARVIS advise as you, challenge you when you're about to repeat a known mistake, and draft in your actual voice rather than generic AI prose.
- **The decision journal** — every meaningful decision logged with its rationale *at the time it was made*. Future-you rarely remembers why past-you chose something; JARVIS holds the "why" and later reports whether the reasoning held up.

### Goal steering

JARVIS holds your long-term arcs — gradeUP revenue, JARVIS itself, life direction — and actively connects today's actions to them. It notices drift and says so: *"you've spent two weeks on polish and nothing on the thing that makes money."* Organising the day is table stakes; owning the arc is the point.

### The hive turned inward

The hive was built for abstract hard problems, but it is just as powerful aimed at *your own* decisions — three perspectives plus a judge running a premortem on a choice you're agonising over, or arguing deliberately against a plan you're attached to. A thinking partner, not only an answer machine.

### Spaced repetition

For anything you're actively learning, JARVIS resurfaces it at the right intervals so the knowledge lands in *your* biological memory rather than only on its drive. The brain extends into your head — which is the entire point of a second brain.

### Cognitive-state awareness

The wearable is not only for the weekly health check-up; it's a cognition signal. Knowing your sleep and HRV lets JARVIS time work to your actual capacity — *"don't start the hard problem now, you're depleted; clear email instead."*

### Ubiquitous capture

Ideas don't wait until you're at the three screens. The phone app accepts voice memos, photos, and screenshots from anywhere, flows them into memory, and processes them in the night cycle. Frictionless capture is the backbone of every serious second-brain system.

### The relationship layer

JARVIS remembers people — what you last discussed, what matters to them, when to follow up — and briefs you before a call. For a founder this alone carries real weight.

### Metacognition

Patch repairs JARVIS's code; a parallel loop repairs JARVIS's *thinking*. Periodically JARVIS reflects on where it misjudged you, which advice missed, and what it should weight differently — then updates the model of you accordingly. Alongside it runs simple epistemic honesty: JARVIS makes clear when it is guessing versus when it knows, so you can safely trust it with real decisions.

---

## 9. The night cycle

JARVIS stays on through the night but spends credits only when there's a reason to. At day's end you say you're signing off; JARVIS gives an overview and summary on the Stage, then works on through the night under a **stim-gated throttle**:

A timer fires every **20–60 minutes**. On each fire, JARVIS checks whether anything has changed or needs doing — a new email, an action required. If nothing has, the timer simply rolls on to the next cycle and **spends zero credits**. If something has, a stim is raised and one of the cycles runs:

- **Dreaming** — consolidating the day's events into the right parts of memory, saving what matters.
- **Connecting** — hunting the knowledge graph for non-obvious links across your whole history, and carrying the worthwhile ones into the morning brief.
- **Planning** — thinking ahead, preparing the next day, and generating the morning brief delivered when sleep mode lifts.
- **Pondering** — researching anything you said that it didn't fully understand.
- **Activating** — faintly surfacing anything dangerous or important on the Stage for you to see.
- **Organising** — handling email, calendar, tasks, and routines; overnight JARVIS may send email and modify your calendar, both visible to you.

A hard nightly budget cap governs all of it and is designed never to be approached.

---

## 10. The world — Gresz Industries & Port Calvera

JARVIS's interface is wrapped in a living fiction: **Gresz Industries**, headquartered on **Port Calvera**, a tropical volcanic island in the mid-Atlantic. This is not decoration over flat panels — it is a **literal navigable 3D interface you fly through**, where each city and building *is* a real system of JARVIS, skinned in the world's lore. From the globe you descend to the island; from a top-down helicopter view you drop into any of three cities; inside each, black-and-white wireframe drone views let you interact with specific facilities.

### Nova Calvera — the capital (the brain of the island)

A fortress of mind and infrastructure in a volcanic basin: layered, dust-hardened, AI-run, defined by the philosophy of *Co-Sovereignty* — humans set direction, AI executes. Three interactive facilities:

- **Calvera Synthesis Works** — the agent factory. A Planner proposes new agents, a Manager critically reviews and directs, a Builder builds, and the loop iterates until the finished agent appears with an **Install** button. New agents run in a sandbox before install.
- **Voz de Calvera** — the news network: island news, discoveries, environmental and volcano reports, with articles to read and radio to hear.
- **The Government Building** — where the **mayor agent** authors the island's "laws," which in real terms are the configuration and rules that govern how JARVIS and the other agents behave. You can read, edit, and talk to it here.

### Alto Norte — the tech city (the systems mind of the island)

A cold high-mountain citadel of uptime and code. Three interactive facilities:

- **Citadela Jarvis** — JARVIS's own command post: a live list of everything JARVIS is doing, each item drillable into its tools and plan, alongside **Patch's** fix console (the one place you type, to direct the agent that repairs JARVIS).
- **Los Cielos de Gresz** — the business skyscraper: your business's events and timeline, ranked opportunities, reports from the business agents, and the engine that earns money.
- **Colmeia Gelada** — the hive: the chain of agents that converge on the hardest problems, visualised as interlinked nodes that light up as they exchange information, with a timeline of breakthroughs and the original question at the top.

### Porto das Velas — the port (contact with the outside world)

A warm harbour-and-finance city, the gateway for all incoming and outgoing flows — money, goods, travel, schedules, commitments. The financial AIs here run accounts, payments, invoices, and the rest. When money is tight or abundant, it's felt here first. It is, as the lore puts it, the island's left ventricle, keeping everything flowing.

---

## 11. The globe

The Stage's default view is a blue, Iron-Man-style 3D globe — naturally spinning, grabbable, and able to transform to show many things, each driven from real API sources, with the rule that anything not cross-confirmed across sources never appears on the map:

- **Weather** — heat, wind, and rain, worldwide or zoomed to a country in context.
- **Travel** — flights with full information and animated routes; high-scale road/rail directions with advice on food, fuel, stops, and hotels; low-scale turn-by-turn that can hand off to your phone.
- **News** — major networks surfaced on the globe, opened and read natively.
- **Wars** — live conflicts portrayed with animated forces and arrows, cross-checked across sources.
- **Radio** — spin the globe to tune into stations around the world.

---

## 12. The business engine — gradeUP

Behind the lore sits a real business: **gradeUP**, an iOS app that helps students with their GCSEs (built on **Expo / React Native** with **Clerk** for auth, hosted on **GitHub**). JARVIS runs it through a team of agents working as one unit:

- **Marketing** — reach and presence; coaching material, the website, getting gradeUP in front of as many students as possible.
- **Sales** — pursuing and answering opportunities.
- **Support** — handling user questions so you're freed up.
- **Developer** — building against the gradeUP codebase.
- **Manager** — keeping the team focused and coordinated.

Agents may handle parts of the work unsupervised, but because gradeUP's users are **minors, all student-facing output is human-reviewed before it goes out — a hard, permanent rule.** Success is measured concretely: more installs and subscriptions, faster feature shipping, and support handled so your time is returned to you.

---

## 13. Safety & security architecture

Because JARVIS edits its own code and runs agents with real access, four systems hold the whole thing safe:

- **The permission gate** — every external or destructive action (sending email, committing code, autofilling a card, modifying the calendar, installing an agent) passes through JARVIS and, for anything irreversible, requires your spoken confirmation. CVV entry and final page-accept always stay manual.
- **The rollback spine** — Patch snapshots JARVIS's code to **GitHub before every change**. If a change fails its health check, Patch auto-reverts to the last known-good snapshot rather than looping on the fix, writes a report, and hands it to JARVIS to read aloud or display on the Stage.
- **The vault** — all credentials live in a **local encrypted vault**, never in plaintext or in a repo.
- **The budget governor** — middleware accounts every model call against a hard nightly cap and an overall **£5,000/month ceiling**, throttling and warning you before any cap is reached.

---

## 14. Cinematic identity

JARVIS MKII is meant to feel like the movie. It boots through a deliberate sequence: a minimalist black screen scattered with white dots and a small ringed core; a double clap lights it up into rotating technology circles that expand, contract into the centre, and fade back to the dotted black; then *directed by Gresz Industries* with a spinning loader, followed by *JARVIS OS Launching*. The pixel face emotes with hand-designed expressions, the globe and island carry the Gresz Industries world, and the footnote beneath it all reads, simply, **Gresz Industries**.

---

*This overview is the single source of truth for what JARVIS MKII is. The companion development plan sequences how it gets built — Demo → Launch → Full — with the safety architecture above standing up first.*
