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
const FOCUS_HOLD_MS = 75 * 1000;     // after a fly/mode command: hold still,
                                     // then auto-clear + resume natural spin

const PORT_CALVERA = { lat: 36.8, lon: -34.2 };

// Cities that get on-globe temperature labels in heat mode
const LABEL_CITIES = [
  { name: "LONDON", lat: 51.5, lon: -0.13 },   { name: "MADRID", lat: 40.4, lon: -3.7 },
  { name: "NEW YORK", lat: 40.7, lon: -74.0 }, { name: "LOS ANGELES", lat: 34.1, lon: -118.2 },
  { name: "SÃO PAULO", lat: -23.6, lon: -46.6 }, { name: "CAIRO", lat: 30.0, lon: 31.2 },
  { name: "LAGOS", lat: 6.5, lon: 3.4 },       { name: "MOSCOW", lat: 55.8, lon: 37.6 },
  { name: "DUBAI", lat: 25.2, lon: 55.3 },     { name: "DELHI", lat: 28.6, lon: 77.2 },
  { name: "BEIJING", lat: 39.9, lon: 116.4 },  { name: "TOKYO", lat: 35.7, lon: 139.7 },
  { name: "SINGAPORE", lat: 1.35, lon: 103.8 },{ name: "SYDNEY", lat: -33.9, lon: 151.2 },
  { name: "CAPE TOWN", lat: -33.9, lon: 18.4 },{ name: "REYKJAVÍK", lat: 64.1, lon: -21.9 },
];

// Heat colour ramp (cold → hot): purple → magenta → blue → green → yellow → orange → red
const HEAT_STOPS = [
  [-30, 0.55, 0.20, 0.85],   // purple
  [-20, 0.85, 0.25, 0.75],   // magenta
  [-10, 0.25, 0.40, 0.95],   // blue
  [  2, 0.15, 0.60, 0.90],   // cyan-blue
  [ 10, 0.20, 0.80, 0.40],   // green
  [ 17, 0.65, 0.85, 0.30],   // yellow-green
  [ 23, 0.95, 0.88, 0.25],   // yellow
  [ 30, 1.00, 0.60, 0.15],   // orange
  [ 38, 1.00, 0.30, 0.12],   // red
  [ 45, 1.00, 0.12, 0.10],   // deep red
];

function heatColor(t, out) {
  if (t <= HEAT_STOPS[0][0]) {
    const s = HEAT_STOPS[0];
    return out.setRGB(s[1], s[2], s[3]);
  }
  for (let i = 1; i < HEAT_STOPS.length; i++) {
    const a = HEAT_STOPS[i - 1], b = HEAT_STOPS[i];
    if (t <= b[0]) {
      const k = (t - a[0]) / (b[0] - a[0]);
      return out.setRGB(
        a[1] + (b[1] - a[1]) * k,
        a[2] + (b[2] - a[2]) * k,
        a[3] + (b[3] - a[3]) * k,
      );
    }
  }
  return out.setRGB(1, 1, 1);
}

function toXYZ(lat, lon, r = R) {
  const la = THREE.MathUtils.degToRad(lat), lo = THREE.MathUtils.degToRad(lon);
  return new THREE.Vector3(
    r * Math.cos(la) * Math.sin(lo),
    r * Math.sin(la),
    r * Math.cos(la) * Math.cos(lo),
  );
}

export class Globe {
  constructor(container, { onPinClick, onModeChange } = {}) {
    this.el = container;
    this.onPinClick = onPinClick || (() => {});
    this.onModeChange = onModeChange || (() => {});
    this.mode = "clear";
    this._vel = 0;                    // drag inertia (rad/frame)
    this._lastInteract = 0;
    this._fly = null;                 // active glide animation
    this._weatherTimer = null;
    this._holdUntil = 0;              // while focused: no idle spin
    this._modeLabels = [];            // temp labels (heat mode)
    this.holdMs = FOCUS_HOLD_MS;      // overridable (dev/testing)
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

    // ── Landmass dot field (vertex-coloured so heat mode can paint it) ────
    this._landDots = dots;            // [lat, lon] per dot — kept for recolour
    const pos = new Float32Array(dots.length * 3);
    const col = new Float32Array(dots.length * 3).fill(1);
    dots.forEach(([lat, lon], i) => {
      const v = toXYZ(lat, lon);
      pos[i * 3] = v.x; pos[i * 3 + 1] = v.y; pos[i * 3 + 2] = v.z;
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    this.landPoints = new THREE.Points(geo, new THREE.PointsMaterial({
      color: 0xf2f4f6, vertexColors: true, size: 1.35, sizeAttenuation: true,
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
    this.onModeChange(mode);
    clearTimeout(this._weatherTimer);
    this._clearWeatherLayer();
    if (mode === "clear") {
      this._holdUntil = 0;            // release the focus hold → natural spin
      return;
    }
    this._holdUntil = performance.now() + this.holdMs;

    let cities;
    try {
      cities = (await (await fetch(`/api/globe/weather`)).json()).cities || [];
    } catch { return; }
    if (this.mode !== mode) return;   // mode changed while fetching

    if (mode === "heat") {
      this._paintHeat(cities);
    } else if (mode === "wind") {
      this._buildWind(cities);
    } else if (mode === "rain") {
      await this._buildRain(cities);
    }
    this._weatherTimer = setTimeout(() => this.setMode(mode), WEATHER_REFRESH_MS);
  }

  _clearWeatherLayer() {
    const drop = (obj) => {
      if (!obj) return;
      this.group.remove(obj);
      obj.geometry?.dispose();
      obj.material?.dispose();
    };
    drop(this.weatherPoints); this.weatherPoints = null;
    if (this._wind) { drop(this._wind.lines); this._wind = null; }
    drop(this._clouds); this._clouds = null;
    if (this._rain) { drop(this._rain.points); this._rain = null; }
    if (this._storms) {
      for (const s of this._storms) {
        s.spiral.geometry.dispose();
        s.spiral.material.dispose();
        this.group.remove(s.holder);
      }
      this._storms = null;
    }
    // reset land dots to white
    const col = this.landPoints.geometry.getAttribute("color");
    col.array.fill(1);
    col.needsUpdate = true;
    // drop temp/storm labels
    for (const l of this._modeLabels) l.label.remove();
    this._modeLabels = [];
  }

  // Heat: the land itself takes the temperature colour, interpolated from
  // the city grid (inverse-distance weighting on the unit sphere)
  _paintHeat(cities) {
    const cityVecs = cities.map((ct) => {
      const v = toXYZ(ct.lat, ct.lon, 1);
      return { x: v.x, y: v.y, z: v.z, t: ct.t };
    });
    const col = this.landPoints.geometry.getAttribute("color");
    const c = new THREE.Color();

    // Pass 1: interpolate every dot's temperature
    const temps = new Float32Array(this._landDots.length);
    this._landDots.forEach(([lat, lon], i) => {
      const v = toXYZ(lat, lon, 1);
      let wSum = 0, tSum = 0;
      for (const ct of cityVecs) {
        const dot = Math.max(-1, Math.min(1, v.x * ct.x + v.y * ct.y + v.z * ct.z));
        const d = Math.acos(dot) + 0.02;              // great-circle distance
        const w = 1 / (d * d);
        wSum += w; tSum += w * ct.t;
      }
      temps[i] = tSum / wSum;
    });

    // Pass 2: stretch the ramp over today's actual spread (5th–95th
    // percentile) — otherwise a July world is one long orange smear.
    const sorted = Array.from(temps).sort((a, b) => a - b);
    let lo = sorted[Math.floor(sorted.length * 0.05)];
    let hi = sorted[Math.floor(sorted.length * 0.95)];
    if (hi - lo < 12) { const mid = (hi + lo) / 2; lo = mid - 6; hi = mid + 6; }
    const RAMP_LO = HEAT_STOPS[0][0], RAMP_HI = HEAT_STOPS[HEAT_STOPS.length - 1][0];

    temps.forEach((t, i) => {
      const k = Math.max(0, Math.min(1, (t - lo) / (hi - lo)));
      heatColor(RAMP_LO + k * (RAMP_HI - RAMP_LO), c);
      col.array[i * 3] = c.r; col.array[i * 3 + 1] = c.g; col.array[i * 3 + 2] = c.b;
    });
    col.needsUpdate = true;

    // Temperature labels for landmark cities
    for (const lc of LABEL_CITIES) {
      let best = null, bestD = 1e9;
      for (const ct of cities) {
        const d = (ct.lat - lc.lat) ** 2 + (ct.lon - lc.lon) ** 2;
        if (d < bestD) { bestD = d; best = ct; }
      }
      if (!best) continue;
      const label = document.createElement("div");
      label.className = "globe-templabel";
      label.innerHTML = `<span class="tn">${lc.name}</span><span class="tt">${Math.round(best.t)}°</span>`;
      this.el.appendChild(label);
      this._modeLabels.push({ local: toXYZ(lc.lat, lc.lon, R + 2), label });
    }
  }

  // ── Wind: streamline particles flowing with the real wind field ─────────
  //
  // A 5° vector-field grid is interpolated (IDW) from the city wind
  // speed+direction; ~900 particles advect through it leaving short
  // trails, so the motion itself shows the direction.

  _buildWind(cities) {
    const NLON = 72, NLAT = 36;
    const grid = new Float32Array(NLON * NLAT * 2);   // u (east), v (north) km/h
    const cityVecs = cities.map((ct) => {
      const v = toXYZ(ct.lat, ct.lon, 1);
      const dir = THREE.MathUtils.degToRad(ct.wd || 0);   // wind FROM this bearing
      return { x: v.x, y: v.y, z: v.z,
               u: -Math.sin(dir) * ct.w, v: -Math.cos(dir) * ct.w };
    });
    for (let j = 0; j < NLAT; j++) {
      const lat = -90 + (j + 0.5) * (180 / NLAT);
      for (let i = 0; i < NLON; i++) {
        const lon = -180 + (i + 0.5) * (360 / NLON);
        const p = toXYZ(lat, lon, 1);
        let wSum = 0, uSum = 0, vSum = 0;
        for (const ct of cityVecs) {
          const dot = Math.max(-1, Math.min(1, p.x * ct.x + p.y * ct.y + p.z * ct.z));
          const d = Math.acos(dot) + 0.03;
          const w = 1 / (d * d);
          wSum += w; uSum += w * ct.u; vSum += w * ct.v;
        }
        grid[(j * NLON + i) * 2] = uSum / wSum;
        grid[(j * NLON + i) * 2 + 1] = vSum / wSum;
      }
    }

    const N = 1500;
    const particles = [];
    for (let n = 0; n < N; n++) particles.push(this._spawnParticle());
    const pos = new Float32Array(N * 2 * 3);
    const col = new Float32Array(N * 2 * 3);
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
    const lines = new THREE.LineSegments(geo, new THREE.LineBasicMaterial({
      vertexColors: true, transparent: true, opacity: 1,
      blending: THREE.AdditiveBlending, depthWrite: false,
    }));
    this.group.add(lines);
    this._wind = { grid, NLON, NLAT, particles, lines, pos, col };
  }

  _spawnParticle() {
    const lat = THREE.MathUtils.radToDeg(Math.asin(Math.random() * 2 - 1)) * 0.94;
    const lon = Math.random() * 360 - 180;
    return {
      lat, lon,
      tlat: lat, tlon: lon,              // lagged tail position
      age: 0, life: 3 + Math.random() * 5,
    };
  }

  _windAt(lat, lon) {
    const w = this._wind;
    const i = Math.min(w.NLON - 1, Math.max(0, Math.floor((lon + 180) / (360 / w.NLON))));
    const j = Math.min(w.NLAT - 1, Math.max(0, Math.floor((lat + 90) / (180 / w.NLAT))));
    const k = (j * w.NLON + i) * 2;
    return [w.grid[k], w.grid[k + 1]];
  }

  _advanceWind(dt) {
    const w = this._wind;
    const SPEED_K = 0.22;              // km/h → degrees per second (stylised)
    const TAIL_LAG = 0.9;              // lower = longer comet trails
    const c = new THREE.Color();
    w.particles.forEach((p, n) => {
      const [u, v] = this._windAt(p.lat, p.lon);
      p.lat += v * SPEED_K * dt;
      p.lon += (u * SPEED_K * dt) / Math.max(0.25, Math.cos(THREE.MathUtils.degToRad(p.lat)));
      if (p.lon > 180) p.lon -= 360;
      if (p.lon < -180) p.lon += 360;
      // Tail chases the head with a lag → visible streak in the wind direction
      const lag = Math.min(1, dt * TAIL_LAG);
      p.tlat += (p.lat - p.tlat) * lag;
      p.tlon += (p.lon - p.tlon) * lag;
      if (Math.abs(p.lon - p.tlon) > 90) { p.tlon = p.lon; p.tlat = p.lat; } // date-line jump
      p.age += dt;
      if (p.age > p.life || Math.abs(p.lat) > 85) {
        Object.assign(p, this._spawnParticle());
      }

      const head = toXYZ(p.lat, p.lon, R + 1.5);
      const tail = toXYZ(p.tlat, p.tlon, R + 1.5);
      const speed = Math.hypot(u, v);
      const k = Math.min(1, speed / 28);          // typical winds fill the range
      const fade = Math.min(1, p.age * 2, (p.life - p.age));
      c.setRGB(0.45 + 0.4 * k, 0.8 + 0.15 * k, 1.0).multiplyScalar(0.6 + 0.4 * k);
      const b = n * 6;
      w.pos[b] = tail.x; w.pos[b + 1] = tail.y; w.pos[b + 2] = tail.z;
      w.pos[b + 3] = head.x; w.pos[b + 4] = head.y; w.pos[b + 5] = head.z;
      w.col[b] = c.r * 0.25 * fade; w.col[b + 1] = c.g * 0.25 * fade; w.col[b + 2] = c.b * 0.25 * fade;
      w.col[b + 3] = c.r * fade; w.col[b + 4] = c.g * fade; w.col[b + 5] = c.b * fade;
    });
    w.lines.geometry.getAttribute("position").needsUpdate = true;
    w.lines.geometry.getAttribute("color").needsUpdate = true;
  }

  // ── Rain: soft clouds, falling rain, live cyclones (GDACS) ──────────────

  _softTexture() {
    if (this._softTex) return this._softTex;
    const cv = document.createElement("canvas");
    cv.width = cv.height = 64;
    const g = cv.getContext("2d").createRadialGradient(32, 32, 2, 32, 32, 30);
    g.addColorStop(0, "rgba(255,255,255,0.9)");
    g.addColorStop(0.5, "rgba(255,255,255,0.35)");
    g.addColorStop(1, "rgba(255,255,255,0)");
    const ctx = cv.getContext("2d");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 64, 64);
    this._softTex = new THREE.CanvasTexture(cv);
    return this._softTex;
  }

  // WMO weather codes that mean "it is raining/showering/storming"
  _isRaining(ct) {
    const wc = ct.wc || 0;
    return (ct.p || 0) > 0.05
      || (wc >= 51 && wc <= 67)          // drizzle + rain
      || (wc >= 80 && wc <= 82)          // showers
      || (wc >= 95);                     // thunderstorms
  }

  _rainIntensity(ct) {
    const wc = ct.wc || 0;
    let k = Math.min(1, (ct.p || 0) / 4);
    if (wc >= 61 && wc <= 67) k = Math.max(k, 0.5);
    if (wc >= 80) k = Math.max(k, 0.7);
    if (wc >= 95) k = 1;
    return Math.max(0.3, k);
  }

  async _buildRain(cities) {
    // Clouds: dense grey-white puffs — the cloudier, the thicker
    const puffs = [];
    for (const ct of cities) {
      const cover = ct.c || 0;
      if (cover < 25) continue;
      const n = 2 + Math.round((cover / 100) * 5);      // up to 7 puffs
      for (let i = 0; i < n; i++) {
        puffs.push({
          lat: ct.lat + (Math.random() - 0.5) * 8,
          lon: ct.lon + (Math.random() - 0.5) * 10,
          k: Math.pow(cover / 100, 1.1),
        });
      }
    }
    const cpos = new Float32Array(puffs.length * 3);
    const ccol = new Float32Array(puffs.length * 3);
    puffs.forEach((p, i) => {
      const v = toXYZ(p.lat, p.lon, R + 5);
      cpos[i * 3] = v.x; cpos[i * 3 + 1] = v.y; cpos[i * 3 + 2] = v.z;
      const b = 0.4 + 0.6 * p.k;
      ccol[i * 3] = b; ccol[i * 3 + 1] = b; ccol[i * 3 + 2] = b;
    });
    const cgeo = new THREE.BufferGeometry();
    cgeo.setAttribute("position", new THREE.BufferAttribute(cpos, 3));
    cgeo.setAttribute("color", new THREE.BufferAttribute(ccol, 3));
    this._clouds = new THREE.Points(cgeo, new THREE.PointsMaterial({
      map: this._softTexture(), vertexColors: true, size: 18,
      sizeAttenuation: true, transparent: true, opacity: 0.75,
      depthWrite: false,
    }));
    this.group.add(this._clouds);

    // Rain: falling STREAKS under every raining city (weather-code aware,
    // so drizzle counts even when instantaneous precipitation reads zero)
    const drops = [];
    for (const ct of cities) {
      if (!this._isRaining(ct)) continue;
      const inten = this._rainIntensity(ct);
      const n = Math.round(8 + inten * 16);             // 8..24 streaks
      for (let i = 0; i < n; i++) {
        drops.push({
          lat: ct.lat + (Math.random() - 0.5) * 6,
          lon: ct.lon + (Math.random() - 0.5) * 8,
          phase: Math.random(), spd: 0.6 + Math.random() * 0.7,
          inten,
        });
      }
    }
    const nDrops = Math.max(1, drops.length);
    const rpos = new Float32Array(nDrops * 2 * 3);      // line: tail + head
    const rcol = new Float32Array(nDrops * 2 * 3);
    const rgeo = new THREE.BufferGeometry();
    rgeo.setAttribute("position", new THREE.BufferAttribute(rpos, 3));
    rgeo.setAttribute("color", new THREE.BufferAttribute(rcol, 3));
    const rainLines = new THREE.LineSegments(rgeo, new THREE.LineBasicMaterial({
      vertexColors: true, transparent: true, opacity: 1,
      blending: THREE.AdditiveBlending, depthWrite: false,
    }));
    this.group.add(rainLines);
    this._rain = { drops, points: rainLines, pos: rpos, col: rcol, t: 0 };

    // Live cyclones (typhoons/hurricanes) from GDACS
    try {
      const storms = (await (await fetch("/api/globe/storms")).json()).storms || [];
      if (this.mode !== "rain") return;
      // Alert level sets the storm's scale: green small, orange big, red massive
      const levelSpec = {
        green:  { radius: 5,  puffs: 42,  size: 7,  css: "#69f0ae" },
        orange: { radius: 10, puffs: 80,  size: 10, css: "#ffb74d" },
        red:    { radius: 18, puffs: 140, size: 14, css: "#ff5252" },
      };
      this._storms = [];
      for (const s of storms) {
        const spec = levelSpec[s.level] || levelSpec.green;
        // A cyclone built of clouds: puffs along two spiral arms + dense eye
        const pts = [];
        for (let i = 0; i < spec.puffs; i++) {
          const t = i / spec.puffs;
          const arm = i % 2 ? Math.PI : 0;
          const th = arm + t * Math.PI * 3.2 + (Math.random() - 0.5) * 0.35;
          const rr = spec.radius * (0.12 + t * 0.88) * (0.9 + Math.random() * 0.2);
          pts.push(new THREE.Vector3(
            Math.cos(th) * rr, Math.sin(th) * rr, (Math.random() - 0.5) * 1.2));
        }
        for (let i = 0; i < 8; i++) {                     // the eye wall
          const th = Math.random() * Math.PI * 2;
          const rr = spec.radius * 0.14 * Math.random();
          pts.push(new THREE.Vector3(Math.cos(th) * rr, Math.sin(th) * rr, 0.5));
        }
        const geo = new THREE.BufferGeometry().setFromPoints(pts);
        const spiral = new THREE.Points(geo, new THREE.PointsMaterial({
          map: this._softTexture(), color: 0xffffff, size: spec.size,
          sizeAttenuation: true, transparent: true, opacity: 0.85,
          depthWrite: false,
        }));
        const holder = new THREE.Group();
        const surface = toXYZ(s.lat, s.lon, R + 2.5);
        holder.position.copy(surface);
        holder.quaternion.setFromUnitVectors(
          new THREE.Vector3(0, 0, 1), surface.clone().normalize());
        holder.add(spiral);
        this.group.add(holder);
        this._storms.push({ holder, spiral });

        const label = document.createElement("div");
        label.className = "globe-stormlabel";
        label.innerHTML = `<span class="sn" style="color:${spec.css}">${s.name}</span>`
                        + `<span class="st">TROPICAL CYCLONE — ${s.level.toUpperCase()}</span>`;
        this.el.appendChild(label);
        this._modeLabels.push({ local: toXYZ(s.lat, s.lon, R + spec.radius * 0.6 + 3), label });
      }
    } catch { /* storms are a bonus — rain still works without them */ }
  }

  _animateRain(dt) {
    const r = this._rain;
    r.t += dt;
    r.drops.forEach((d, i) => {
      const h = 1 - ((r.t * d.spd + d.phase) % 1);        // 1 → 0 falling
      const head = toXYZ(d.lat, d.lon, R + 1 + h * 4.5);
      const tail = toXYZ(d.lat, d.lon, R + 1 + h * 4.5 + 1.6 + d.inten);
      const b = (0.35 + 0.65 * h) * (0.6 + 0.4 * d.inten);
      const k = i * 6;
      r.pos[k] = tail.x; r.pos[k + 1] = tail.y; r.pos[k + 2] = tail.z;
      r.pos[k + 3] = head.x; r.pos[k + 4] = head.y; r.pos[k + 5] = head.z;
      r.col[k] = 0.12 * b; r.col[k + 1] = 0.25 * b; r.col[k + 2] = 0.5 * b;
      r.col[k + 3] = 0.45 * b; r.col[k + 4] = 0.7 * b; r.col[k + 5] = 1.0 * b;
    });
    r.points.geometry.getAttribute("position").needsUpdate = true;
    r.points.geometry.getAttribute("color").needsUpdate = true;
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
    // Focused on a place: hold position (no idle drift) until the hold expires
    this._holdUntil = performance.now() + this.holdMs;
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
    const now = performance.now();
    const held = now < this._holdUntil;

    // Focus hold expired with a mode still on → revert to the default globe:
    // clear markers/colours, ease back, resume the natural spin.
    // (Runs before the size guard — behaviour must not depend on rendering.)
    if (!held && this._holdUntil !== 0) {
      this._holdUntil = 0;
      if (this.mode !== "clear") this.setMode("clear");
      this._fly = { t: 0, dur: 2.0,
        fromX: this.group.rotation.x, toX: 0,
        fromY: this.group.rotation.y, toY: this.group.rotation.y,
        fromD: this.camDist, toD: R * 3.1 };
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
    } else if (held) {
      // Focused: stay exactly where Jarvis put the globe — no drift
    } else if (now - this._lastInteract > 4000) {
      this.group.rotation.y += IDLE_SPIN * dt;        // natural spin
      // ease tilt back to equator view
      this.group.rotation.x *= (1 - 0.4 * dt);
    } else if (Math.abs(this._vel) > 0.0004) {
      this.group.rotation.y += this._vel;             // inertia
      this._vel *= 0.94;
    }

    this.camera.position.z = this.camDist;

    // Animated weather layers
    if (this._wind) this._advanceWind(dt);
    if (this._rain) this._animateRain(dt);
    if (this._storms) for (const s of this._storms) s.spiral.rotation.z -= dt * 2.4;

    // Project labels (pins + heat-mode temps); fade behind the horizon
    const projectLabel = (world, label, interactive) => {
      const toCam = this.camera.position.clone().sub(world).normalize();
      const facing = world.clone().normalize().dot(toCam);
      const proj = world.clone().project(this.camera);
      const x = (proj.x * 0.5 + 0.5) * w;
      const y = (-proj.y * 0.5 + 0.5) * h;
      label.style.transform = `translate(-50%, -110%) translate(${x}px, ${y - 10}px)`;
      label.style.opacity = facing > 0.12 ? String(Math.min(1, facing * 1.6)) : "0";
      label.style.pointerEvents = interactive && facing > 0.12 ? "auto" : "none";
    };
    for (const pin of this.pins) {
      projectLabel(pin.mesh.getWorldPosition(new THREE.Vector3()), pin.label, true);
    }
    for (const ml of this._modeLabels) {
      projectLabel(ml.local.clone().applyMatrix4(this.group.matrixWorld), ml.label, false);
    }

    this.renderer.render(this.scene, this.camera);
  }
}
