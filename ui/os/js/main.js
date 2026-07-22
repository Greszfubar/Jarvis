// JARVIS OS shell — boot state machine.
//
//   STANDBY ──clap_detected──▶ IGNITED ──launching──▶ CINEMATIC ──▶ DASHBOARD
//
// Dev simulation: open /os?sim=1 and press  c = clap   l = launch
//                                           s = speaking   d = done   r = response

import "./dots.js";
import { Core } from "./boot.js";
import { Waveform } from "./waveform.js";
import { AudioLink } from "./audio.js";
import { EventLink } from "./ws.js";
import { Hud } from "./hud.js";
import { Hands } from "./hands.js";

const $ = (id) => document.getElementById(id);
const scenes = { boot: $("boot"), gresz: $("card-gresz"), launch: $("card-launch"), dash: $("dashboard") };
let state = "standby";

const core = new Core($("core"));
const waveform = new Waveform($("waveform"));

const audio = new AudioLink({ onLevel: (v) => waveform.setLevel(v) });
audio.start();
// WebKit requires a user gesture before audio can start
document.addEventListener("click", () => audio.resume(), { once: false });

const hands = new Hands({ onStatus: (msg) => hud.showBanner(msg, 3200) });

const hud = new Hud({
  onUtterance: (text) => link.say(text),
  onMicToggle: (on) => audio.setEnabled(on),
  onCamToggle: (on) => {
    hands.setActive(on);
    fetch("/api/os/camera", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ on }),
    }).catch(() => {});
  },
  onShutdown: () => {
    hud.showBanner("SHUTTING DOWN", 4000);
    fetch("/api/os/shutdown", { method: "POST" }).catch(() => {});
  },
});

function show(name) {
  for (const [k, el] of Object.entries(scenes)) el.classList.toggle("visible", k === name);
}

// ── Boot sequence ───────────────────────────────────────────────────────────
function ignite() {
  if (state !== "standby") return;
  state = "ignited";
  core.ignite();
  $("boot-hint").textContent = "say — wake up jarvis";
}

function launchSequence() {
  if (state === "cinematic" || state === "dashboard") return;
  state = "cinematic";
  $("boot-hint").style.display = "none";
  core.ignite(); // ensure rings are up even if clap event was missed
  setTimeout(() => {
    core.launch(() => {
      show("gresz");
      setTimeout(() => {
        show("launch");
        setTimeout(() => enterDashboard(), 2400);
      }, 2400);
    });
  }, 600);
}

function enterDashboard() {
  state = "dashboard";
  show("dash");
  // The Jarvis window keeps its rings; the globe lives on /globe (screen 2)
  new Core($("core-idle"), { passive: true });
  // In-OS voice: no wake word needed from here on
  fetch("/api/os/voice", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ always_on: true }),
  }).catch(() => {});
}

// ── Event link ──────────────────────────────────────────────────────────────
const link = new EventLink((d) => {
  switch (d.kind) {
    case "clap_detected": ignite(); break;
    case "launching": launchSequence(); break;
    case "got_command": if (d.text) hud.showHeard(d.text); break;
    case "speaking":
      waveform.setSpeaking(true);
      audio.setSpeaking(true);
      if (d.text) hud.showSubtitle(d.text);
      break;
    case "speaking_done":
      waveform.setSpeaking(false);
      audio.setSpeaking(false);
      break;
    case "response":
      if (d.text) hud.showSubtitle(d.text);
      break;
    case "os":
      if (d.command === "banner" && d.arg) hud.showBanner(String(d.arg).toUpperCase());
      if (d.command === "globe" && d.arg) {
        // Globe lives on screen 2 — just acknowledge here
        hud.showBanner(`GLOBE — ${d.arg.trim().toUpperCase()}`, 2200);
      }
      break;
    case "hands":
      hands.handle(d);
      break;
    case "hands_frame":
      hands.showFrame(d.jpg);
      break;
    case "permission":
      hud.showPermission(d);
      break;
    case "permission_resolved":
      hud.resolvePermission();
      hud.showBanner(d.allowed ? "APPROVED" : "DENIED", 2200);
      break;
  }
});

// ── Dev simulation (?sim=1) ─────────────────────────────────────────────────
if (new URLSearchParams(location.search).has("sim")) {
  $("boot-hint").textContent += "  ·  sim: c l s d r h p";
  window.__os = { hands, hud, waveform };   // sim-mode debug handle
  let mouseHand = false;
  document.addEventListener("keydown", (e) => {
    if (document.activeElement === $("cmd")) return;
    if (e.key === "c") ignite();
    if (e.key === "l") launchSequence();
    if (e.key === "s") { waveform.setSpeaking(true); hud.showSubtitle("Good evening, Evan. All systems are operational and standing by."); }
    if (e.key === "d") waveform.setSpeaking(false);
    if (e.key === "r") hud.showBanner("OS EVENT CHANNEL LIVE");
    // h = mouse-as-hand (tests the full hands pipeline without a camera)
    if (e.key === "h") {
      mouseHand = !mouseHand;
      hands.setActive(mouseHand);
      hud.showBanner(mouseHand ? "SIM HAND — MOVE MOUSE, P TO PINCH" : "SIM HAND OFF", 2600);
    }
    if (e.key === "p" && mouseHand) {
      hands.handle({ type: "pinch_down", x: hands.x / innerWidth, y: hands.y / innerHeight });
      setTimeout(() => hands.handle({ type: "pinch_up", x: hands.x / innerWidth, y: hands.y / innerHeight }), 180);
    }
  });
  document.addEventListener("mousemove", (e) => {
    if (mouseHand) hands.handle({ type: "cursor", x: e.clientX / innerWidth, y: e.clientY / innerHeight, pinched: false });
  });
}
