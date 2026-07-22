// Corner waveform — Jarvis's presence indicator.
// White bars follow Evan's mic level; blue synthetic wave while Jarvis speaks.

const BAR_COUNT = 36;

export class Waveform {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.level = 0;          // live mic RMS 0..1 (set by audio.js)
    this.speaking = false;   // Jarvis talking → blue mode
    this.bars = new Array(BAR_COUNT).fill(0.05);
    requestAnimationFrame((t) => this.frame(t));
  }

  setLevel(v) { this.level = Math.min(1, v * 6); }
  setSpeaking(on) { this.speaking = on; }

  frame(t) {
    const { ctx, canvas } = this;
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Advance bars: shift left, push new sample
    let target;
    if (this.speaking) {
      target = 0.25 + 0.55 * Math.abs(Math.sin(t * 0.012) * Math.sin(t * 0.0053));
    } else {
      target = Math.max(0.04, this.level);
    }
    this.bars.push(this.bars[BAR_COUNT - 1] * 0.4 + target * 0.6);
    this.bars.shift();

    const bw = w / BAR_COUNT;
    for (let i = 0; i < BAR_COUNT; i++) {
      const v = this.bars[i];
      const bh = Math.max(2, v * h * 0.9);
      const x = i * bw + bw * 0.25;
      const fade = 0.25 + 0.75 * (i / BAR_COUNT); // older bars fade out
      if (this.speaking) {
        ctx.fillStyle = `rgba(77, 163, 255, ${0.85 * fade})`;
        ctx.shadowColor = "rgba(77, 163, 255, 0.6)";
        ctx.shadowBlur = 8;
      } else {
        ctx.fillStyle = `rgba(242, 244, 246, ${0.55 * fade})`;
        ctx.shadowBlur = 0;
      }
      ctx.fillRect(x, (h - bh) / 2, bw * 0.5, bh);
    }
    ctx.shadowBlur = 0;
    requestAnimationFrame((tt) => this.frame(tt));
  }
}
