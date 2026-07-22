// Boot cinematic — the Jarvis core circle and its technology rings.
//
// States: idle (one thin ring, small orbiter) → ignited (many rings, claps heard)
//         → launching (expand → collapse → gone)
// The core also renders the dashboard's globe placeholder in "passive" mode.

export class Core {
  constructor(canvas, { passive = false } = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.state = passive ? "passive" : "idle";
    this.t0 = performance.now();
    this.launchStart = 0;
    this.igniteStart = 0;
    this.done = false;
    requestAnimationFrame((t) => this.frame(t));
  }

  ignite() {
    if (this.state === "idle") {
      this.state = "ignited";
      this.igniteStart = performance.now();
    }
  }

  launch(onDone) {
    this.state = "launching";
    this.launchStart = performance.now();
    this.onDone = onDone;
  }

  frame(t) {
    if (this.done) return;
    const { ctx, canvas } = this;
    const cx = canvas.width / 2, cy = canvas.height / 2;
    const base = canvas.width * 0.17;
    const e = (t - this.t0) / 1000;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let scale = 1, alpha = 1, ringCount = 1;

    if (this.state === "ignited" || this.state === "passive") {
      const k = this.state === "passive" ? 1
        : Math.min(1, (t - this.igniteStart) / 900);
      ringCount = 1 + Math.floor(k * 5);
    }

    if (this.state === "launching") {
      const k = (t - this.launchStart) / 1000; // seconds into launch
      ringCount = 6;
      if (k < 1.1) {
        scale = 1 + this.easeOut(k / 1.1) * 0.65;          // expand
      } else if (k < 1.9) {
        const c = this.easeIn((k - 1.1) / 0.8);
        scale = 1.65 - c * 1.65;                            // collapse to centre
        alpha = 1 - c * 0.9;
      } else {
        this.done = true;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        if (this.onDone) this.onDone();
        return;
      }
    }

    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(scale, scale);
    ctx.globalAlpha = alpha;

    // Core circle
    ctx.strokeStyle = "#f2f4f6";
    ctx.lineWidth = 1.4;
    ctx.globalAlpha = alpha * 0.9;
    ctx.beginPath();
    ctx.arc(0, 0, base, 0, Math.PI * 2);
    ctx.stroke();

    // Inner pulse dot
    ctx.globalAlpha = alpha * (0.35 + 0.25 * Math.sin(e * 2));
    ctx.beginPath();
    ctx.arc(0, 0, base * 0.06, 0, Math.PI * 2);
    ctx.fillStyle = "#f2f4f6";
    ctx.fill();

    // Technology rings — arcs with gaps, each rotating at its own speed
    for (let i = 0; i < ringCount; i++) {
      const r = base * (1.18 + i * 0.16);
      const speed = (i % 2 === 0 ? 1 : -1) * (0.25 + i * 0.09);
      const rot = e * speed;
      const segs = 2 + (i % 3);
      ctx.globalAlpha = alpha * (0.55 - i * 0.06);
      ctx.lineWidth = i === 0 ? 1.2 : 0.8;
      for (let s = 0; s < segs; s++) {
        const start = rot + (s / segs) * Math.PI * 2;
        const len = (Math.PI * 2 / segs) * (0.42 + 0.18 * Math.sin(e * 0.7 + i + s));
        ctx.beginPath();
        ctx.arc(0, 0, r, start, start + len);
        ctx.stroke();
      }
      // Ring node dots
      ctx.globalAlpha = alpha * 0.7;
      const nodeAngle = rot * 1.3 + i;
      ctx.beginPath();
      ctx.arc(Math.cos(nodeAngle) * r, Math.sin(nodeAngle) * r, 1.8, 0, Math.PI * 2);
      ctx.fill();
    }

    // Passive (globe placeholder) — faint meridian hints inside the core
    if (this.state === "passive") {
      ctx.globalAlpha = 0.14;
      ctx.lineWidth = 0.7;
      for (let m = 1; m <= 3; m++) {
        ctx.beginPath();
        ctx.ellipse(0, 0, base * (m / 4), base, 0, 0, Math.PI * 2);
        ctx.stroke();
        ctx.beginPath();
        ctx.ellipse(0, 0, base, base * (m / 4), 0, 0, Math.PI * 2);
        ctx.stroke();
      }
    }

    ctx.restore();
    requestAnimationFrame((tt) => this.frame(tt));
  }

  easeOut(x) { return 1 - Math.pow(1 - x, 3); }
  easeIn(x) { return x * x * x; }
}
