// Hands — renders the fingertip trail cursor and turns gesture events
// into real interactions (pinch = click, scroll = wheel).
//
// Server events arrive as kind "hands": cursor / pinch_down / pinch_up /
// scroll / zoom / started / stopped / error / hand_lost.

const TRAIL_LIFE = 650;   // ms a trail point lives
const RING_LIFE = 450;    // ms the pinch ring pulse lives

export class Hands {
  constructor({ onStatus } = {}) {
    this.onStatus = onStatus || (() => {});
    this.canvas = document.getElementById("hand-trail");
    this.ctx = this.canvas.getContext("2d");
    this.active = false;
    this.visible = false;      // hand currently detected
    this.x = innerWidth / 2;
    this.y = innerHeight / 2;
    this.pinched = false;
    this.trail = [];
    this.rings = [];           // pinch pulse animations
    this._resize();
    window.addEventListener("resize", () => this._resize());
    requestAnimationFrame((t) => this._frame(t));
  }

  _resize() {
    this._w = innerWidth;
    this._h = innerHeight;
    const dpr = Math.min(devicePixelRatio || 1, 2);
    this.canvas.width = this._w * dpr;
    this.canvas.height = this._h * dpr;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  setActive(on) {
    this.active = on;
    if (!on) { this.visible = false; this.trail = []; }
    const feed = document.getElementById("cam-feed");
    if (feed) {
      feed.classList.toggle("on", on);
      if (!on) feed.removeAttribute("src");   // drop the last frame when off
    }
  }

  showFrame(jpgB64) {
    if (!this.active) return;
    const feed = document.getElementById("cam-feed");
    if (feed) feed.src = "data:image/jpeg;base64," + jpgB64;
  }

  handle(d) {
    switch (d.type) {
      case "cursor":
        this.visible = true;
        this.x = d.x * innerWidth;
        this.y = d.y * innerHeight;
        this.pinched = !!d.pinched;
        this.trail.push({ x: this.x, y: this.y, t: performance.now() });
        // While pinched, a moving fingertip is a drag (spins the globe etc.)
        if (this._down) this._pointer("pointermove", this.x, this.y, "mousemove");
        break;
      case "pinch_down": {
        const x = d.x * innerWidth, y = d.y * innerHeight;
        this._down = { x, y, t: performance.now(),
                       target: document.elementFromPoint(x, y) || document.body };
        this._pointer("pointerdown", x, y, "mousedown", this._down.target);
        this.rings.push({ x, y, t: performance.now() });
        break;
      }
      case "pinch_up": {
        this.pinched = false;
        const x = this.x, y = this.y;
        if (this._down) {
          this._pointer("pointerup", x, y, "mouseup");
          const moved = Math.hypot(x - this._down.x, y - this._down.y);
          const held = performance.now() - this._down.t;
          // Short, stationary pinch = a click on what was under the fingertip
          if (moved < 14 && held < 700) {
            const opts = { bubbles: true, cancelable: true, clientX: x, clientY: y, view: window };
            this._down.target.dispatchEvent(new MouseEvent("click", opts));
          }
          this._down = null;
        }
        break;
      }
      case "scroll":
        this._scroll(d.dy * innerHeight);
        break;
      case "zoom":
        window.dispatchEvent(new CustomEvent("jarvis:zoom", { detail: { ds: d.ds } }));
        break;
      case "started":
        this.onStatus("HAND TRACKING ONLINE");
        break;
      case "stopped":
        this.setActive(false);
        break;
      case "error":
        this.onStatus(`HANDS ERROR — ${String(d.message || "").toUpperCase()}`);
        break;
      case "hand_lost":
        this.visible = false;
        break;
    }
  }

  // Synthesize pointer+mouse events at the fingertip: elements (and the
  // globe's drag controls) never know it wasn't a real mouse
  _pointer(type, x, y, mouseType, target = null) {
    const el = target || document.elementFromPoint(x, y) || document.body;
    const opts = { bubbles: true, cancelable: true, clientX: x, clientY: y,
                   view: window, pointerId: 7, pointerType: "touch", isPrimary: true };
    el.dispatchEvent(new PointerEvent(type, opts));
    if (mouseType) el.dispatchEvent(new MouseEvent(mouseType, opts));
  }

  _scroll(dyPx) {
    const el = document.elementFromPoint(this.x, this.y) || document.body;
    el.dispatchEvent(new WheelEvent("wheel", {
      bubbles: true, cancelable: true,
      clientX: this.x, clientY: this.y, deltaY: dyPx,
    }));
  }

  _frame(now) {
    // Self-heal zero-size / resized viewports (webview prerender quirk)
    if (this._w !== innerWidth || this._h !== innerHeight) this._resize();
    const { ctx } = this;
    ctx.clearRect(0, 0, innerWidth, innerHeight);

    if (this.active) {
      // Fading trail
      this.trail = this.trail.filter((p) => now - p.t < TRAIL_LIFE);
      for (const p of this.trail) {
        const k = 1 - (now - p.t) / TRAIL_LIFE;
        ctx.globalAlpha = k * 0.35;
        ctx.fillStyle = "#f2f4f6";
        ctx.beginPath();
        ctx.arc(p.x, p.y, 2.5 * k + 0.5, 0, Math.PI * 2);
        ctx.fill();
      }

      // Cursor dot + halo
      if (this.visible) {
        ctx.globalAlpha = 0.9;
        ctx.fillStyle = this.pinched ? "#4da3ff" : "#f2f4f6";
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.pinched ? 5 : 3.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 0.25;
        ctx.strokeStyle = ctx.fillStyle;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.pinched ? 14 : 11, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Pinch pulse rings
      this.rings = this.rings.filter((r) => now - r.t < RING_LIFE);
      for (const r of this.rings) {
        const k = (now - r.t) / RING_LIFE;
        ctx.globalAlpha = (1 - k) * 0.6;
        ctx.strokeStyle = "#4da3ff";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(r.x, r.y, 8 + k * 30, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    ctx.globalAlpha = 1;
    requestAnimationFrame((t) => this._frame(t));
  }
}
