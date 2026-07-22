// Dots starfield — the permanent JARVIS OS backdrop.
// Faint white dots, slow parallax drift, occasional twinkle.

const canvas = document.getElementById("dots");
const ctx = canvas.getContext("2d");
let dots = [];
let w = 0, h = 0;

function resize() {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  w = window.innerWidth;
  h = window.innerHeight;
  canvas.width = w * dpr;
  canvas.height = h * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  seed();
}

function seed() {
  const count = Math.round((w * h) / 4200);
  dots = Array.from({ length: count }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    r: Math.random() < 0.85 ? 0.7 + Math.random() * 0.5 : 1.2 + Math.random() * 0.8,
    a: 0.05 + Math.random() * 0.22,
    tw: Math.random() * Math.PI * 2,          // twinkle phase
    tws: 0.2 + Math.random() * 0.6,           // twinkle speed
    vx: (Math.random() - 0.5) * 0.02,
    vy: (Math.random() - 0.5) * 0.02,
  }));
}

function frame(t) {
  ctx.clearRect(0, 0, w, h);
  for (const d of dots) {
    d.x += d.vx; d.y += d.vy;
    if (d.x < -2) d.x = w + 2; if (d.x > w + 2) d.x = -2;
    if (d.y < -2) d.y = h + 2; if (d.y > h + 2) d.y = -2;
    const twinkle = 0.75 + 0.25 * Math.sin(d.tw + t * 0.001 * d.tws);
    ctx.globalAlpha = d.a * twinkle;
    ctx.fillStyle = "#f2f4f6";
    ctx.beginPath();
    ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  requestAnimationFrame(frame);
}

window.addEventListener("resize", resize);
resize();
requestAnimationFrame(frame);
