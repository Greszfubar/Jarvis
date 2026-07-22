// HUD — control bar, overlays, subtitles, keyboard command bar.

export class Hud {
  constructor({ onUtterance, onMicToggle, onShutdown }) {
    this.onUtterance = onUtterance;
    this.subtitle = document.getElementById("subtitle");
    this.subtitleHeard = document.getElementById("subtitle-heard");
    this.banner = document.getElementById("os-banner");
    this._subTimer = null;
    this._heardTimer = null;
    this._bannerTimer = null;

    // Mic
    const mic = document.getElementById("btn-mic");
    mic.addEventListener("click", () => {
      mic.classList.toggle("active");
      onMicToggle(mic.classList.contains("active"));
    });

    // Camera — Phase 2 stub
    const cam = document.getElementById("btn-cam");
    cam.addEventListener("click", () => {
      cam.classList.toggle("active");
      this.showBanner(cam.classList.contains("active")
        ? "HAND TRACKING — ARRIVES IN PHASE 2" : "CAMERA OFF", 2600);
    });

    // Settings
    const settings = document.getElementById("settings-panel");
    document.getElementById("btn-settings").addEventListener("click", () => settings.classList.add("on"));
    settings.addEventListener("click", (e) => { if (e.target === settings) settings.classList.remove("on"); });

    // Power
    const confirm = document.getElementById("confirm-power");
    document.getElementById("btn-power").addEventListener("click", () => confirm.classList.add("on"));
    document.getElementById("power-no").addEventListener("click", () => confirm.classList.remove("on"));
    document.getElementById("power-yes").addEventListener("click", () => {
      confirm.classList.remove("on");
      onShutdown();
    });

    // Keyboard fallback: "/" opens the command bar
    const bar = document.getElementById("cmdbar");
    const input = document.getElementById("cmd");
    document.addEventListener("keydown", (e) => {
      if (e.key === "/" && !bar.classList.contains("on")) {
        e.preventDefault();
        bar.classList.add("on");
        input.focus();
      } else if (e.key === "Escape") {
        bar.classList.remove("on");
        input.blur();
      }
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && input.value.trim()) {
        this.onUtterance(input.value.trim());
        this.showHeard(input.value.trim());
        input.value = "";
        bar.classList.remove("on");
      }
      e.stopPropagation();
    });
  }

  showHeard(text) {
    this.subtitleHeard.textContent = `“${text}”`;
    this.subtitleHeard.classList.add("on");
    clearTimeout(this._heardTimer);
    this._heardTimer = setTimeout(() => this.subtitleHeard.classList.remove("on"), 6000);
  }

  showSubtitle(text, holdMs = null) {
    this.subtitle.textContent = text;
    this.subtitle.classList.add("on");
    clearTimeout(this._subTimer);
    // Hold roughly as long as it takes to speak, min 4 s
    const ms = holdMs ?? Math.max(4000, text.split(/\s+/).length * 320);
    this._subTimer = setTimeout(() => this.subtitle.classList.remove("on"), ms);
  }

  hideSubtitle() {
    clearTimeout(this._subTimer);
    this.subtitle.classList.remove("on");
  }

  showBanner(text, ms = 5000) {
    this.banner.textContent = text;
    this.banner.classList.add("on");
    clearTimeout(this._bannerTimer);
    this._bannerTimer = setTimeout(() => this.banner.classList.remove("on"), ms);
  }
}
