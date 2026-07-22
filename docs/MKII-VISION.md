# JARVIS MK II — Vision

> The canonical design north star. Written 2026-07-22 from Evan's original vision.
> Technical decisions live in `MKII-PRD.md`. Build order lives in `MKII-ROADMAP.md`.

## The one-liner

A no-type, no-click AI operating environment. Two screens on a Mac Studio M3 Ultra:
the **Dashboard** (a living 3D globe and the fictional island of Port Calvera, home
of Gresz Industries) and **THE STAGE** (Jarvis's own canvas — summaries, checklists,
night work). You control everything with your hands in the air and your voice.
Jarvis always answers when spoken to.

## Aesthetic

Black screens with faint white dots. White wireframe 3D. Minimalist, abstract,
cinematic. Nothing exists without a reason. "Directed by Gresz Industries."

## Boot sequence

1. Black screen, white dots. A Jarvis circle sits centred with one thin technology ring.
2. **Two claps** → the circle ignites: many concentric tech rings orbit the core (black & white).
3. Everything expands, collapses into the centre, fades back to dots.
4. Text: *Directed by Gresz Industries* — three spinning dots.
5. Text: *JARVIS OS Launching* — three spinning dots.
6. Dashboard fades in.

## Interaction model

**Hands** (tracked by the camera; a faint trail follows your fingertip on screen):
| Gesture | Action |
|---|---|
| Slide | Move the cursor |
| Pinch | Click |
| Pinch + move | Drag |
| Two fingers | Scroll (trackpad-style) |
| Fingers spread → in | Zoom in |
| Fingers in → spread | Zoom out |

**Voice**: Jarvis responds every time Evan speaks. No wake word once the OS is up,
no hesitation to interject. Voice is the primary channel; hands are for spatial work.

## The Dashboard (screen 1)

Black, dotted. A large 3D globe spins slowly in the centre (spinnable by hand).
Beneath it, like a footnote: **Gresz Industries**.

Passive state — two lit pins:

```
Madrid, Spain                Alto Norte, Nova Calvera
Home of Evan                 Gresz Industries
36°                          48°
```

- Corner: the **Jarvis waveform** — reacts to Evan's speech, glows blue when Jarvis speaks. Click → Jarvis Brain page.
- Bottom centre buttons, left → right: **Mic** toggle · **Camera** toggle · **Settings** cog · **X** (shut down JARVIS OS and the machine).
- Click Madrid pin → Home page. Click island pin → Island page.

### Globe modes

- **Weather** — Heat / Wind / Rain, world-wide news-broadcast style or focused by context ("show me Tenerife, I'm there next week").
- **Travel** — three tiers:
  1. *Flights*: animated plane on a blue arc with full flight info.
  2. *High scale*: country-level road/rail routes with Jarvis's advice — food, fuel, sights, hotels.
  3. *Low scale*: street-level directions (Maps-powered), opening hours, busyness. Handoff: Jarvis pushes the trip to the phone and starts navigation.
  - Flight *booking* and check-in: Jarvis prepares everything; Evan approves payment.
- **News** — major networks pop up on the globe; pinch-drag to open a story natively (video or article). Jarvis offers stories by voice and glides the globe to the region.
- **Wars** — live conflict visualisation: units, arrows, movements on the globe.
- **Radio** — spin the globe as a tuner; zoom into a country/station to listen.

## Port Calvera (the island)

A fictional tropical volcanic island in the mid-Atlantic — the home of Gresz
Industries. Three biomes, three cities. Clicking it from the globe gives a
helicopter top-down 3D view; clicking a city zooms into a black & white
**wireframe drone view**. Every building is a real subsystem of Jarvis.

### Nova Calvera — the capital (volcanic desert basin)

The brain of the island: government, law, narrative. Layered city — dust-hardened
towers above, covered arcades mid-level, data centres underground. Philosophy:
**Co-Sovereignty** — humans set direction, AI executes. "The island runs on our code."

| Building | What it really is |
|---|---|
| **Calvera Synthesis Works** | The agent factory. Left: catalogue of finished agents with install buttons. Right: live view of the Planner → Manager → Builder loop inventing, critiquing, and building new agents for Evan. |
| **Voz de Calvera** | Island news network & radio. Bulletins about what every part of the system is working on, volcano reports, discoveries. Readable articles, listenable radio. |
| **Government Building** | The lore engine. The Mayor agent writes the island's laws, plans construction, produces documents and imagery. Evan can talk to and direct the Mayor. |

### Alto Norte — the tech citadel (cold high mountains)

An infrastructure monastery above the clouds. Compact glass-and-stone buildings
bored into ridges, sky-bridges, cold blue glow at night. Nova Calvera talks for
the island; Alto Norte thinks for it.

| Building | What it really is |
|---|---|
| **Citadela Jarvis** (on Pico Negro) | Jarvis's live task inspector. Left: everything Jarvis is doing right now — click for full plan, tools, progress. Right: **Patch**, the text-only repair agent that fixes Jarvis all day. |
| **Los Cielos de Gresz** (in Pie de Silicona) | Business HQ. Left: business events & timelines. Right: ranked, summarised Upwork jobs (click → opens on the whiteboard) plus reports from the Marketing, Sales, and Developer agents run by a Manager agent. |
| **Colmeia Gelada** | The Hive — a 45-node reasoning collective for the hardest problems. Left ⅔: the agent graph, connections lighting up as information flows; click an active node to inspect it. Right: the original question, who asked it, and a timeline of breakthroughs. Layer-2 agents and JARVIS (priority) may submit dilemmas. |

### Porto das Velas — the port city (beaches & jungle)

The gateway. Everything that flows in and out of Evan's life — money, goods,
travel, commitments — lands here. Harbour district, the Velas Financial Belt
(accounts, payments, invoices, subscriptions), jungle-edge secure facilities.
Warmer and more human than the other two. "The left ventricle: it keeps
everything flowing."

## THE STAGE (screen 2)

Jarvis's own screen. Extremely ingenuitive.

- **Sign-off** — Evan says "I'm signing off" / "I'm going to sleep" → Jarvis renders the day's overview: important news, messages, and a summary of the workings of Port Calvera. Then he works through the night.
- **Night cycle**:
  - *Dreaming* — replays the day, files information into memory, saves what matters to preserve context.
  - *Planning* — plans tomorrow, generates the morning brief for wake-up.
  - *Pondering* — researches anything Evan said that Jarvis didn't fully understand.
  - *Stimming* — random firings every 20–60 min: check position, catch anything undone.
  - *Activating* — dangerous or important flags rendered faintly on the STAGE for night viewing.
- **Events mode** — the STAGE becomes a checklist: routines as lists, tasks as a bottom checkmark that expands into the task page, sessions ("let's start a one-hour work session") locking the top of the STAGE.

## Beyond the desk

- **Phone app** — talk to Jarvis anywhere; monitor him at home.
- **House monitoring** — one video walkthrough → Jarvis identifies everything (the plant that needs watering every N days, clothes, risks) and reminds on schedule.
- **Health** — weekly check-in tracking how Evan is doing (honest framing: guided journal + trends; real sensor data comes via HealthKit through the phone app).
