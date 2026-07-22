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

const $ = (id) => document.getElementById(id);
const scenes = { boot: $("boot"), gresz: $("card-gresz"), launch: $("card-launch"), dash: $("dashboard") };
let state = "standby";

const core = new Core($("core"));
const waveform = new Waveform($("waveform"));

const audio = new AudioLink({ onLevel: (v) => waveform.setLevel(v) });
audio.start();
// WebKit requires a user gesture before audio can start
document.addEventListener("click", () => audio.resume(), { once: false });

const hud = new Hud({
  onUtterance: (text) => link.say(text),
  onMicToggle: (on) => audio.setEnabled(on),
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
  new Core($("globe-placeholder"), { passive: true });
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
      break;
  }
});

// ── Dev simulation (?sim=1) ─────────────────────────────────────────────────
if (new URLSearchParams(location.search).has("sim")) {
  $("boot-hint").textContent += "  ·  sim: c l s d r";
  document.addEventListener("keydown", (e) => {
    if (document.activeElement === $("cmd")) return;
    if (e.key === "c") ignite();
    if (e.key === "l") launchSequence();
    if (e.key === "s") { waveform.setSpeaking(true); hud.showSubtitle("Good evening, Evan. All systems are operational and standing by."); }
    if (e.key === "d") waveform.setSpeaking(false);
    if (e.key === "r") hud.showBanner("OS EVENT CHANNEL LIVE");
  });
}
