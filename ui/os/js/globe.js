// The Globe — JARVIS OS centrepiece. Landmass dot-field in three.js.
//
//   const globe = new Globe(containerEl);  await globe.init();
//   globe.flyTo(40.4, -3.7);               // glide to lat/lon
//   globe.setMode("heat" | "wind" | "rain" | "clear");
//
// Interaction: drag to spin (mouse, or pinch-drag via hands.js synthesized
// pointer events), wheel / hand-zoom to dolly. Idle → slow natural spin.

import * as THREE from "/os/static/vendor/three.module.js";

const R = 100;                       // globe radius (scene units)
const IDLE_SPIN = 0.04;              // rad/s when untouched
const WEATHER_REFRESH_MS = 15 * 60 * 1000;

const PORT_CALVERA = { lat: 36.8, lon: -34.2 };

function toXYZ(lat, lon, r = R) {
  const la = THREE.MathUtils.degToRad(lat), lo = THREE.MathUtils.degToRad(lon);
  return new THREE.Vector3(
    r * Math.cos(la) * Math.sin(lo),
    r * Math.sin(la),
    r * Math.cos(la) * Math.cos(lo),
  );
}

export class Globe {
  constructor(container, { onPinClick } = {}) {
    this.el = container;
    this.onPinClick = onPinClick || (() => {});
    this.mode = "clear";
    this._vel = 0;                    // drag inertia (rad/frame)
    this._lastInteract = 0;
    this._fly = null;                 // active glide animation
    this._weatherTimer = null;
  }

  async init() {
    const dots = await (await fetch("/os/static/land-dots.json")).json();

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(38, 1, 1, 2000);
    this.camDist = R * 3.1;
    this.camera.position.z = this.camDist;

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setClearColor(0x000000, 0);
    // Never override a fixed/absolute container — that collapses its height
    if (getComputedStyle(this.el).position === "static") {
      this.el.style.position = "relative";
    }
    // Canvas out of flow so its size never feeds back into the container's
    const dom = this.renderer.domElement;
    dom.style.position = "absolute";
    dom.style.top = "0";
    dom.style.left = "0";
    this.el.appendChild(dom);

    this.group = new THREE.Group();
    this.scene.add(this.group);

    // ── Landmass dot field ────────────────────────────────────────────────
    const pos = new Float32Array(dots.length * 3);
    dots.forEach(([lat, lon], i) => {
      const v = toXYZ(lat, lon);
      pos[i * 3] = v.x; pos[i * 3 + 1] = v.y; pos[i * 3 + 2] = v.z;
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    this.landPoints = new THREE.Points(geo, new THREE.PointsMaterial({
      color: 0xf2f4f6, size: 1.35, sizeAttenuation: true,
      transparent: true, opacity: 0.85, depthWrite: false,
    }));
    this.group.add(this.landPoints);

    // Occluder sphere: hides dots on the far side, keeps the black-void look
    this.group.add(new THREE.Mesh(
      new THREE.SphereGeometry(R - 1.5, 48, 32),
      new THREE.MeshBasicMaterial({ color: 0x000000 }),
    ));

    // Faint graticule
    const grat = new THREE.Group();
    const mat = new THREE.LineBasicMaterial({ color: 0xf2f4f6, transparent: true, opacity: 0.06 });
    for (let lat = -60; lat <= 60; lat += 30) {
      const pts = [];
      for (let lon = 0; lon <= 360; lon += 4) pts.push(toXYZ(lat, lon, R + 0.3));
      grat.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), mat));
    }
    for (let lon = 0; lon < 180; lon += 30) {
      const pts = [];
      for (let lat = -90; lat <= 90; lat += 4) pts.push(toXYZ(lat, lon, R + 0.3));
      grat.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), mat));
      const ptsB = [];
      for (let lat = -90; lat <= 90; lat += 4) ptsB.push(toXYZ(lat, lon + 180, R + 0.3));
      grat.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(ptsB), mat));
    }
    this.group.add(grat);

    // ── Weather layer (built on demand) ───────────────────────────────────
    this.weatherPoints = null;

    // ── Pins ──────────────────────────────────────────────────────────────
    this.pins = [];
    this._pinGeo = new THREE.SphereGeometry(1.6, 12, 12);
    await this._buildPins();

    // ── Controls ──────────────────────────────────────────────────────────
    this._wireControls();

    // ── Render loop ───────────────────────────────────────────────────────
    this._clock = new THREE.Clock();
    const loop = () => {
      this._tick(this._clock.getDelta());
      requestAnimationFrame(loop);
    };
    loop();
    return this;
  }

  // ── Pins ────────────────────────────────────────────────────────────────

  async _buildPins() {
    let home = { city: "Madrid", lat: 40.42, lon: -3.70, temp: null };
    try {
      const s = await (await fetch("/api/status")).json();
      const w = s.weather || {};
      if (w.city) {
        home.city = w.city;
        home.temp = w.temp;
        if (w.lat && w.lon) { home.lat = w.lat; home.lon = w.lon; }
        else {
          const known = { petersfield: [51.0, -0.94], madrid: [40.42, -3.70], london: [51.5, -0.12] };
          const k = known[String(w.city).toLowerCase()];
          if (k) { home.lat = k[0]; home.lon = k[1]; }
        }
      }
    } catch { /* offline — defaults stand */ }

    this._addPin({
      id: "home", lat: home.lat, lon: home.lon,
      lines: [`${home.city}`, "Home of Evan", home.temp != null ? `${Math.round(home.temp)}°` : ""],
    });
    this._addPin({
      id: "calvera", lat: PORT_CALVERA.lat, lon: PORT_CALVERA.lon,
      lines: ["Alto Norte, Nova Calvera", "Gresz Industries", "48°"],
    });
  }

  _addPin({ id, lat, lon, lines }) {
    const mesh = new THREE.Mesh(this._pinGeo,
      new THREE.MeshBasicMaterial({ color: 0xf2f4f6 }));
    mesh.position.copy(toXYZ(lat, lon, R + 0.5));
    this.group.add(mesh);

    const label = document.createElement("div");
    label.className = "globe-label";
    label.innerHTML = lines.filter(Boolean)
      .map((l, i) => `<span class="${i === 0 ? "l0" : "ln"}">${l}</span>`).join("");
    label.addEventListener("click", () => this.onPinClick(id));
    this.el.appendChild(label);

    this.pins.push({ id, mesh, label });
  }

  // ── Weather modes ───────────────────────────────────────────────────────

  async setMode(mode) {
    this.mode = mode;
    clearTimeout(this._weatherTimer);
    if (this.weatherPoints) {
      this.group.remove(this.weatherPoints);
      this.weatherPoints.geometry.dispose();
      this.weatherPoints.material.dispose();
      this.weatherPoints = null;
    }
    if (mode === "clear") return;

    let cities;
    try {
      cities = (await (await fetch(`/api/globe/weather`)).json()).cities || [];
    } catch { return; }

    const pos = new Float32Array(cities.length * 3);
    const col = new Float32Array(cities.length * 3);
    const c = new THREE.Color();
    cities.forEach((ct, i) => {
      const v = toXYZ(ct.lat, ct.lon, R + 1.2);
      pos[i * 3] = v.x; pos[i * 3 + 1] = v.y; pos[i * 3 + 2] = v.z;
      if (mode === "heat") {
        const k = Math.max(0, Math.min(1, (ct.t + 20) / 65));      // -20..45°C
        c.setHSL(0.66 - 0.66 * k, 0.9, 0.35 + 0.3 * k);
      } else if (mode === "wind") {
        const k = Math.max(0, Math.min(1, ct.w / 70));             // 0..70 km/h
        c.setHSL(0.5, 0.85, 0.25 + 0.55 * k);
      } else if (mode === "rain") {
        const k = Math.max(0.06, Math.min(1, ct.p / 6));           // 0..6 mm
        c.setHSL(0.6, 0.9, 0.18 + 0.55 * k);
      }
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    this.weatherPoints = new THREE.Points(geo, new THREE.PointsMaterial({
      vertexColors: true, size: 4.2, sizeAttenuation: true,
      transparent: true, opacity: 0.95, depthWrite: false,
      blending: THREE.AdditiveBlending,
    }));
    this.group.add(this.weatherPoints);
    this._weatherTimer = setTimeout(() => this.setMode(mode), WEATHER_REFRESH_MS);
  }

  // ── Fly-to glide ────────────────────────────────────────────────────────

  flyTo(lat, lon, dist = null) {
    const target = {
      rx: THREE.MathUtils.degToRad(lat),
      ry: -THREE.MathUtils.degToRad(lon),
      dist: dist || R * 2.2,
    };
    // shortest wrap for longitude spin
    const cur = this.group.rotation.y % (Math.PI * 2);
    let dy = target.ry - cur;
    while (dy > Math.PI) dy -= Math.PI * 2;
    while (dy < -Math.PI) dy += Math.PI * 2;
    this._fly = {
      t: 0, dur: 2.2,
      fromX: this.group.rotation.x, toX: target.rx,
      fromY: this.group.rotation.y, toY: this.group.rotation.y + dy,
      fromD: this.camDist, toD: target.dist,
    };
    this._lastInteract = performance.now();
  }

  zoomBy(factor) {
    this.camDist = Math.max(R * 1.35, Math.min(R * 5, this.camDist * factor));
    this._lastInteract = performance.now();
  }

  // ── Controls ────────────────────────────────────────────────────────────

  _wireControls() {
    const dom = this.renderer.domElement;
    let dragging = false, px = 0, py = 0;
    dom.style.touchAction = "none";
    dom.addEventListener("pointerdown", (e) => {
      dragging = true; px = e.clientX; py = e.clientY;
      this._fly = null;
      this._lastInteract = performance.now();
    });
    window.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const dx = (e.clientX - px) / this.el.clientWidth;
      const dy = (e.clientY - py) / this.el.clientHeight;
      px = e.clientX; py = e.clientY;
      this.group.rotation.y += dx * 3.2;
      this.group.rotation.x = Math.max(-1.2, Math.min(1.2, this.group.rotation.x + dy * 2.2));
      this._vel = dx * 3.2;
      this._lastInteract = performance.now();
    });
    window.addEventListener("pointerup", () => { dragging = false; });
    dom.addEventListener("wheel", (e) => {
      e.preventDefault();
      this.zoomBy(1 + Math.sign(e.deltaY) * 0.08);
    }, { passive: false });
    // Hand open-palm zoom events (hands.js dispatches on window)
    window.addEventListener("jarvis:zoom", (e) => this.zoomBy(1 - e.detail.ds * 2.2));
  }

  // ── Frame ───────────────────────────────────────────────────────────────

  _tick(dt) {
    const w = this.el.clientWidth, h = this.el.clientHeight;
    if (w && h && (this._w !== w || this._h !== h)) {
      this._w = w; this._h = h;
      this.renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
      this.renderer.setSize(w, h);
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
    }
    if (!w || !h) return;

    if (this._fly) {
      const f = this._fly;
      f.t += dt;
      const k = Math.min(1, f.t / f.dur);
      const e = k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      this.group.rotation.x = f.fromX + (f.toX - f.fromX) * e;
      this.group.rotation.y = f.fromY + (f.toY - f.fromY) * e;
      this.camDist = f.fromD + (f.toD - f.fromD) * e;
      if (k >= 1) this._fly = null;
    } else if (performance.now() - this._lastInteract > 4000) {
      this.group.rotation.y += IDLE_SPIN * dt;        // natural spin
      // ease tilt back to equator view
      this.group.rotation.x *= (1 - 0.4 * dt);
    } else if (Math.abs(this._vel) > 0.0004) {
      this.group.rotation.y += this._vel;             // inertia
      this._vel *= 0.94;
    }

    this.camera.position.z = this.camDist;

    // Project pin labels; fade when the pin rotates behind the globe
    for (const pin of this.pins) {
      const world = pin.mesh.getWorldPosition(new THREE.Vector3());
      const toCam = this.camera.position.clone().sub(world).normalize();
      const normal = world.clone().normalize();
      const facing = normal.dot(toCam);
      const proj = world.clone().project(this.camera);
      const x = (proj.x * 0.5 + 0.5) * w;
      const y = (-proj.y * 0.5 + 0.5) * h;
      pin.label.style.transform = `translate(-50%, -110%) translate(${x}px, ${y - 10}px)`;
      pin.label.style.opacity = facing > 0.12 ? String(Math.min(1, facing * 1.6)) : "0";
      pin.label.style.pointerEvents = facing > 0.12 ? "auto" : "none";
    }

    this.renderer.render(this.scene, this.camera);
  }
}
