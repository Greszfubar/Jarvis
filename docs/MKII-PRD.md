# JARVIS MK II — Technical PRD

> How the vision in `MKII-VISION.md` gets built on top of MK I.
> Status: draft v1 — 2026-07-22.

## Guiding decision

**MK II is a new face on the MK I brain, not a rewrite.** Everything below reuses
the running system at `~/jarvis`: the `claude`-CLI orchestrator, the agent layer
(`BaseAgent` + specialists), the event bus, APScheduler, Whisper listener,
speaker, PARA/ChromaDB memory, and the FastAPI server on `:8765`.

"JARVIS OS" is technically: **full-screen frameless webview windows in kiosk mode**
(Dock and menu bar hidden), one per display, rendered by the existing pywebview /
WKWebView shell. It looks and behaves like an OS; it ships like an app. It runs on
**macOS** (the Mac Studio) — the phone app is the only iOS component.

## Architecture

```
┌────────────── Screen 1: DASHBOARD ─────────────┐  ┌───── Screen 2: STAGE ─────┐
│  pywebview kiosk window → http://:8765/os      │  │  kiosk window → /stage    │
│  Single-page app: three.js globe + island      │  │  summaries, night cycle,  │
│  + windows/pages, dots background, waveform    │  │  checklists, sessions     │
└───────────────────────┬────────────────────────┘  └────────────┬──────────────┘
                        │        WebSocket /ws/os (events both ways)
┌───────────────────────┴─────────────────────────────────────────┴─────────────┐
│  FastAPI (:8765)  ←→  core.bus  ←→  Orchestrator (claude CLI)                 │
│  agents/* (weather, news, calendar, gmail, VISION, ULTRON, FRIDAY, GRESZ, …)  │
│  APScheduler (proactive ticks, night cycle)   Memory (SQLite+Chroma+PARA)     │
├───────────────────────────────────────────────────────────────────────────────┤
│  hands/ service: camera → MediaPipe Hands → gesture recogniser                │
│                → {cursor, pinch, scroll, zoom} events → /ws/os                │
│  voice/: existing Whisper listener + speaker; audio levels → waveform events  │
└───────────────────────────────────────────────────────────────────────────────┘
```

### New top-level modules

| Module | Purpose |
|---|---|
| `ui/os/` | The MK II SPA (served at `/os` and `/stage`): three.js scenes, HUD, windows. No build step — ES modules + vendored three.js, same pattern as the current dashboard. |
| `hands/` | Gesture service. OpenCV camera capture → MediaPipe Hands (21 landmarks) → gesture state machine → JSON events over the bus/WebSocket. Runs as an asyncio task inside main.py, toggleable. |
| `factory/` | Calvera Synthesis Works: Planner/Manager/Builder loop that writes agent files into `agents/generated/`, plus install/registration. |
| `stage/` | Night cycle jobs (dream, plan, ponder, stim, activate) and STAGE state (checklists, sessions, sign-off). |

## Key technical choices

1. **Renderer: three.js in the WKWebView.** One WebGL scene graph handles the
   globe, the island, and the wireframe city zooms with camera fly-throughs.
   The M3 Ultra makes performance a non-issue; dev works fine on the MacBook.
2. **Hand tracking: MediaPipe Hands in Python first.** Cross-platform, ~30 fps on
   the MacBook camera, and it keeps the whole stack in one language. A Swift
   `Vision`-framework helper (native, lower latency) is a swap-in upgrade later —
   the gesture event schema is the stable interface, not the tracker.
   - Gesture schema: `{type: cursor|pinch_down|pinch_up|scroll|zoom, x, y, dx, dy, scale, hand}`
     in normalised 0–1 screen coordinates.
   - Pinch = thumb-tip/index-tip distance below threshold with hysteresis.
     Two-finger scroll = index+middle extended, vertical motion. Zoom = spread delta.
3. **One WebSocket, everything is an event.** `/ws/os` bridges `core.bus` to the
   browser. Gestures, waveform levels, Jarvis speech, agent updates, globe-mode
   commands, STAGE updates — all typed bus events. Jarvis changes the UI by
   publishing events (new `[ACTION:os:...]` tags in the orchestrator), so
   "show me Tenerife" glides the globe with zero special-casing.
4. **Voice unchanged, plus levels.** Existing listener/speaker stay. The speaker
   and listener publish RMS amplitude frames so the waveform reacts to both sides.
   In-OS mode: no wake word — every utterance goes to the orchestrator.
5. **Globe data sources** (all free tiers to start): Open-Meteo (heat/wind/rain —
   weather agent already exists), existing news agent + RSS for News mode,
   radio-browser.info API for Radio mode, OpenSky Network for live flights,
   OSRM/Apple Maps links for directions. Wars mode: curated GeoJSON via FRIDAY
   research, rendered as animated arcs/markers (clearly labelled as illustrative).
6. **The island is authored once, rendered forever.** Port Calvera is a handmade
   low-poly GLTF (island + 3 city blocks + 7 hero buildings), displayed with
   wireframe materials. City "drone views" are camera paths, not separate scenes.
7. **Agent factory = claude CLI sessions with roles.** Planner proposes specs,
   Manager critiques (two gates: usefulness, correctness), Builder writes a
   `BaseAgent` subclass into `agents/generated/`. Install = dynamic import +
   `orchestrator.register_agent`, persisted in a manifest. Generated code runs
   with the same trust as the rest of Jarvis, so the Manager gate includes a
   safety checklist and Evan's install click is the final approval.
8. **The Hive renders 45, runs ~6.** Colmeia Gelada's graph shows 45 nodes;
   behind it a debate loop of ~6 claude sessions (proposer/critic/synthesiser
   rotation) does the real work. Node count scales with observed answer quality,
   not vibes.
9. **STAGE + night cycle = APScheduler.** Sign-off phrase triggers the summary
   render and flips night mode: Dreaming reuses/extends `ConsolidationAgent`,
   Planning generates the morning brief, Pondering drains a "didn't-understand"
   queue the orchestrator feeds during the day, Stimming is a random 20–60 min
   job, Activating publishes flagged items to the STAGE at low opacity.
10. **Hard lines.** Payments (flights etc.): Jarvis prepares, Evan clicks pay.
    Shutdown X asks for confirmation before `osascript` shutdown. Camera and mic
    toggles genuinely stop capture, not just hide UI.

## Non-goals for now

Phone app, house monitoring, health check-ins, real flight booking automation —
all deferred until the desk experience is complete (Phase 6 backlog).

## Definition of "MK II exists"

Clap twice → boot cinematic → globe dashboard → say "show me the weather in
Tenerife" and watch the globe respond → pinch the island, fly into Alto Norte,
open Citadela Jarvis and watch real tasks → say "I'm signing off" → STAGE renders
the day and the night cycle takes over. All without touching the keyboard.
