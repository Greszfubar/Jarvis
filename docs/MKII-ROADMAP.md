# JARVIS MK II — Roadmap

> Build order for `MKII-PRD.md`. Each phase ends with something Evan can stand in
> front of and feel. Check boxes as tasks complete; keep the status line current.

**Status: Phase 1 built ✓ (browser-verified 2026-07-22; live clap+voice run pending) — Phase 2 next**

---

## Phase 1 — The Shell *(the future feeling, immediately)*

Goal: clap twice → cinematic boot → dotted black dashboard with waveform and
controls, talking to the real MK I brain. Keyboard still allowed as fallback.

- [x] 1.1 `ui/os/` SPA skeleton served at `/os`: dots background, base styles, scene manager
- [x] 1.2 Full-screen kiosk window pointed at `/os` — run with `JARVIS_OS=1 python main.py`
- [x] 1.3 Bus ⇄ browser events — simplified: reused the existing `/ws` (chat + voice events) and `/ws/audio` (mic PCM) channels instead of a new `/ws/os`; `os.command` bus topic broadcasts as kind `os`
- [x] 1.4 Boot cinematic: Jarvis circle + rings → clap-twice trigger (existing listener) → expand/collapse → "Directed by Gresz Industries" → "JARVIS OS Launching" → dashboard fade-in
- [x] 1.5 Jarvis waveform: local mic RMS (client-side, no server round-trip), blue synthetic wave on `speaking` events
- [x] 1.6 In-OS voice mode: `set_always_on` on BrowserListener (≥3 words, no wake word), enabled via `/api/os/voice` when the dashboard loads
- [x] 1.7 Bottom control bar: mic toggle (wired to `/api/mute`), camera stub (Phase 2), settings panel, shutdown X with confirm (`/api/os/shutdown`; machine shutdown only if `JARVIS_SHUTDOWN_MACHINE=1`)
- [x] 1.8 `[ACTION:os:banner|…]` orchestrator tag → bus → OS banner; the `os` action channel is the hook for Phase 3 globe commands

*Verified in browser via `/os?sim=1` (keys: c=clap l=launch s=speaking d=done r=banner). Full clap→voice loop needs a live `python main.py` run — Whisper + mic aren't available in the dev preview.*

## Phase 2 — Hands *(no type, no click)*

Goal: control the shell entirely by hand from across the desk.

- [ ] 2.1 `hands/` service: camera capture + MediaPipe Hands landmarks at ≥25 fps
- [ ] 2.2 Gesture state machine: cursor, pinch-click (with hysteresis), pinch-drag, two-finger scroll, zoom in/out
- [ ] 2.3 Fingertip trail cursor rendered in the SPA from gesture events
- [ ] 2.4 Gesture → DOM/three.js hit-testing so pinch actually clicks buttons and grabs the globe
- [ ] 2.5 Calibration screen + sensitivity settings; camera toggle truly stops capture
- [ ] 2.6 One week of daily-driving; tune thresholds until gestures feel inevitable

## Phase 3 — The Globe *(the centrepiece)*

Goal: the spinning globe with pins, spinnable by hand, mode-switchable by voice.

- [ ] 3.1 three.js globe: slow idle spin, hand-spinnable, dots aesthetic, "Gresz Industries" footnote
- [ ] 3.2 Passive state: Madrid + Port Calvera pins with labels and live temperatures
- [ ] 3.3 Camera glide system: fly to any lat/lon on command ("show me Tenerife")
- [ ] 3.4 Weather mode: heat / wind / rain overlays (Open-Meteo), world or focused
- [ ] 3.5 News mode: stories pinned to the globe from the news agent; pinch to open article/video natively in an OS window
- [ ] 3.6 Radio mode: globe as tuner via radio-browser.info; zoom into a station to listen
- [ ] 3.7 Flights: live plane arcs (OpenSky) + route view with flight info panel
- [ ] 3.8 Directions: high-scale country routes and low-scale street directions with Maps handoff link
- [ ] 3.9 Wars mode: illustrative conflict layer from FRIDAY-curated GeoJSON

## Phase 4 — Port Calvera *(the island of agents)*

Goal: fly from the globe into wireframe cities where every building is a live subsystem.

- [ ] 4.1 Island GLTF: Port Calvera landmass, 3 biomes, 3 city blocks, helicopter view
- [ ] 4.2 Wireframe drone-view camera paths into each city
- [ ] 4.3 **Citadela Jarvis**: live task inspector (left) fed by orchestrator/agent activity; **Patch** repair agent chat (right, text-only)
- [ ] 4.4 **Calvera Synthesis Works**: `factory/` Planner → Manager → Builder loop; live loop view (right), agent catalogue with install buttons (left); install requires Evan's click
- [ ] 4.5 **Voz de Calvera**: island bulletins generated from real system activity + volcano lore; readable articles, listenable radio
- [ ] 4.6 **Government Building**: Mayor agent — laws, construction lore, documents, imagery; directable by conversation
- [ ] 4.7 **Los Cielos de Gresz**: business timelines (left); Upwork feed ranked + summarised, Marketing/Sales/Developer/Manager agent reports (right) — extends GRESZ agent
- [ ] 4.8 **Colmeia Gelada**: 45-node animated graph over a ~6-session debate loop; question intake from JARVIS and Layer-2 agents; breakthrough timeline
- [ ] 4.9 **Porto das Velas**: finance/flows dashboard (subscriptions, commitments, in/out) — read-only v1

## Phase 5 — THE STAGE & the night cycle *(Jarvis never sleeps)*

Goal: second screen alive; "I'm signing off" hands the machine to Jarvis until morning.

- [ ] 5.1 Second kiosk window at `/stage` on display 2, with graceful single-display fallback
- [ ] 5.2 Sign-off trigger phrases → end-of-day overview: news, messages, Port Calvera summary
- [ ] 5.3 Dreaming: nightly memory consolidation (extend `ConsolidationAgent`) with visible dream log
- [ ] 5.4 Planning: overnight plan + morning brief rendered on wake
- [ ] 5.5 Pondering: orchestrator flags things it didn't fully understand → overnight research queue
- [ ] 5.6 Stimming: random 20–60 min self-checks — anything undone? anything drifting?
- [ ] 5.7 Activating: urgent flags rendered faintly on the STAGE at night
- [ ] 5.8 Events mode: routines checklist, tasks checkmark that expands to the task page, voice-started focus sessions that lock the top of the STAGE

## Phase 6 — Beyond the desk *(backlog, not scoped)*

- [ ] Phone app (talk to Jarvis remotely, monitor him, HealthKit bridge)
- [ ] House monitoring from a video walkthrough
- [ ] Weekly health check-in (journal + trends framing)
- [ ] Flight prep/check-in assistance (Evan always makes the payment)
- [ ] Swift Vision-framework hand tracker upgrade on the Mac Studio
