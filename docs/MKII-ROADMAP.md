# JARVIS MK II — Roadmap

> ⚠ **Canonical plan updated 2026-07-22**: `MKII-MASTER-OVERVIEW.md` (what it is)
> and `MKII-DEV-PLAN.md` (Demo → Launch → Cognition → Full) are now the source of
> truth. This file tracks the *current build* — the Demo-phase spine running on
> the MacBook until the M5 mini + 3 screens + OBSBOT arrive.
>
> Key reconciliations with the new plan:
> - What's built (boot, voice shell, gesture tracking) = the Demo-phase spine.
>   The Face (Screen 1), Brain & Vitals (Screen 2), and 3-screen Electron kiosk
>   need the real hardware; current pywebview shell carries development until then.
> - Gestures move to **relative, trackpad-style mapping** (new plan) during the
>   2.6 tuning pass — current absolute mapping is the placeholder.
> - Business engine = **gradeUP** (not Upwork). Hard rule from the first agent:
>   all student-facing output is human-reviewed — gradeUP users are minors.
> - Phase-0 safety scaffolding (permission gate, rollback spine, vault, budget
>   governor) must land before Patch or any installable agent gets real access.
> - Voice stack upgrade path: Deepgram STT + Cartesia TTS + Sonnet streaming
>   (current Whisper + `say`/ElevenLabs is the placeholder).

**Status: Phase 1 live ✓ · Phase 2 built ✓ (real-hand tuning pending) — next: Phase-0 safety scaffolding from `MKII-DEV-PLAN.md`, then the Globe**

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

- [x] 2.1 `hands/` service: OpenCV capture + MediaPipe Hands (0.10.35, model_complexity 0), camera-button start/stop via `/api/os/camera`
- [x] 2.2 Gesture state machine (`hands/gestures.py`, unit-tested): cursor EMA smoothing, pinch-click with hysteresis, two-finger scroll, open-hand zoom deltas, clean pinch-release on hand loss
- [x] 2.3 Fingertip trail cursor: fading trail, cursor dot + halo (blue while pinched), pinch pulse rings
- [x] 2.4 Pinch → synthesized mousedown/up/click at the fingertip (`elementFromPoint`); scroll → wheel events; zoom events emitted (globe consumes them in Phase 3)
- [x] 2.5 Camera toggle truly stops capture (camera released, tracking thread ends); sensitivity constants live in `GestureEngine` — calibration screen deferred until real-hand tuning shows what needs adjusting
- [ ] 2.6 Daily-driving with a real hand; tune thresholds until gestures feel inevitable *(Evan — camera button, then tell Jarvis what feels wrong)*

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
