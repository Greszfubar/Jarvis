"""
JARVIS OS (MK II) routes — the shell served at /os.

Registered onto the main FastAPI app by ui.web. The OS page reuses the
existing event channels: /ws (chat + voice events) and /ws/audio (mic PCM).
This module adds the pages, OS control endpoints, and the os.command bridge.
"""
import asyncio
import logging
import os as _os
import threading
import time
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from core.bus import bus

log = logging.getLogger("jarvis.os")

_OS_DIR = Path(__file__).parent / "os"

# ── Globe weather grid — world cities sampled for heat/wind/rain modes ───────
_WORLD_CITIES = [
    # (lat, lon) — spread for even globe coverage
    (51.5, -0.13), (48.9, 2.35), (40.4, -3.7), (41.9, 12.5), (52.5, 13.4),
    (55.8, 37.6), (59.9, 30.3), (59.3, 18.1), (60.2, 24.9), (64.1, -21.9),
    (38.7, -9.1), (37.9, 23.7), (41.0, 29.0), (50.1, 8.7), (47.5, 19.0),
    (50.5, 30.5), (44.4, 26.1), (53.3, -6.3), (55.7, 12.6), (52.4, 4.9),
    (40.7, -74.0), (34.1, -118.2), (41.9, -87.6), (29.8, -95.4), (33.4, -112.1),
    (47.6, -122.3), (39.7, -105.0), (25.8, -80.2), (38.9, -77.0), (42.4, -71.1),
    (45.5, -73.6), (43.7, -79.4), (49.3, -123.1), (19.4, -99.1), (23.1, -82.4),
    (9.9, -84.1), (4.7, -74.1), (10.5, -66.9), (-0.2, -78.5), (-12.0, -77.0),
    (-16.5, -68.2), (-23.6, -46.6), (-22.9, -43.2), (-34.6, -58.4), (-33.5, -70.7),
    (-25.3, -57.6), (-34.9, -56.2), (30.0, 31.2), (33.6, -7.6), (36.8, 10.2),
    (32.9, 13.2), (6.5, 3.4), (5.6, -0.2), (14.7, -17.5), (9.1, 38.7),
    (-1.3, 36.8), (-6.8, 39.3), (-4.3, 15.3), (-8.8, 13.2), (-26.2, 28.0),
    (-33.9, 18.4), (-29.9, 31.0), (-18.9, 47.5), (31.6, -8.0), (15.6, 32.5),
    (35.7, 139.7), (34.7, 135.5), (37.6, 127.0), (39.9, 116.4), (31.2, 121.5),
    (22.3, 114.2), (25.0, 121.6), (23.1, 113.3), (30.6, 104.1), (39.1, 117.2),
    (28.6, 77.2), (19.1, 72.9), (13.1, 80.3), (22.6, 88.4), (12.9, 77.6),
    (17.4, 78.5), (24.9, 67.0), (23.8, 90.4), (27.7, 85.3), (6.9, 79.9),
    (13.8, 100.5), (21.0, 105.8), (10.8, 106.7), (11.6, 104.9), (16.8, 96.2),
    (3.1, 101.7), (1.35, 103.8), (-6.2, 106.8), (-7.8, 110.4), (14.6, 121.0),
    (25.3, 51.5), (24.5, 54.4), (25.2, 55.3), (21.4, 39.8), (24.7, 46.7),
    (33.3, 44.4), (35.7, 51.4), (31.8, 35.2), (33.9, 35.5), (36.2, 37.2),
    (40.2, 44.5), (41.7, 44.8), (43.2, 76.9), (41.3, 69.2), (38.6, 68.8),
    (47.9, 106.9), (48.0, 66.9), (55.0, 73.4), (56.0, 92.9), (62.0, 129.7),
    (43.1, 131.9), (53.0, 158.7), (64.7, 177.5), (-33.9, 151.2), (-37.8, 145.0),
    (-27.5, 153.0), (-31.9, 115.9), (-35.3, 149.1), (-41.3, 174.8), (-36.8, 174.8),
    (-17.7, 168.3), (-9.4, 147.2), (21.3, -157.9), (61.2, -149.9), (64.8, -147.7),
    (78.2, 15.6), (-54.8, -68.3), (-77.8, 166.7), (72.8, -56.1), (81.7, -16.7),
]
_weather_cache = {"ts": 0.0, "cities": []}
_storms_cache = {"ts": 0.0, "storms": []}
_flights_cache = {"ts": 0.0, "flights": []}
_routes_cache = {}          # callsign → {route info} (routes rarely change)
_WEATHER_TTL = 30 * 60
_FLIGHTS_TTL = 150          # OpenSky anonymous credits are scarce — ~24 calls/h max



def register_os(app: FastAPI, broadcast):
    """Attach OS routes. `broadcast(kind, payload)` is ui.web's client fan-out."""

    app.mount("/os/static", StaticFiles(directory=str(_OS_DIR)), name="os-static")

    @app.get("/os", response_class=HTMLResponse)
    async def os_page():
        return FileResponse(_OS_DIR / "index.html")

    @app.get("/globe", response_class=HTMLResponse)
    async def globe_page():
        return FileResponse(_OS_DIR / "globe.html")

    @app.get("/stage", response_class=HTMLResponse)
    async def stage_page():
        return FileResponse(_OS_DIR / "stage.html")

    # Jarvis drives the UI: orchestrator [ACTION:os:cmd|arg] → bus → browser
    bus.subscribe(
        "os.command",
        lambda p: asyncio.create_task(broadcast("os", p)),
    )

    # Hand tracking events: hands.service (camera thread) → bus → browser
    bus.subscribe(
        "hands.event",
        lambda p: asyncio.create_task(broadcast("hands", p)),
    )

    # Faint live camera feed frames (JPEG base64, ~10 fps)
    bus.subscribe(
        "hands.frame",
        lambda p: asyncio.create_task(broadcast("hands_frame", p)),
    )

    # Permission gate → OS overlay (+ resolution feedback)
    bus.subscribe(
        "permission.request",
        lambda p: asyncio.create_task(broadcast("permission", p)),
    )
    bus.subscribe(
        "permission.resolved",
        lambda p: asyncio.create_task(broadcast("permission_resolved", p)),
    )

    @app.post("/api/os/permission")
    async def os_permission(body: dict):
        """Overlay buttons — approve/deny the pending permission request."""
        from core.permissions import gate
        ok = gate.resolve_ui(str(body.get("id", "")), bool(body.get("allow", False)))
        return {"resolved": ok}

    @app.get("/api/os/budget")
    async def os_budget():
        from core.governor import summary
        return summary()

    @app.get("/api/globe/weather")
    async def globe_weather():
        """World-city weather grid for the globe's heat/wind/rain modes.
        One batched Open-Meteo call, cached 30 minutes."""
        now = time.time()
        if now - _weather_cache["ts"] < _WEATHER_TTL and _weather_cache["cities"]:
            return {"cities": _weather_cache["cities"], "cached": True}
        lats = ",".join(str(c[0]) for c in _WORLD_CITIES)
        lons = ",".join(str(c[1]) for c in _WORLD_CITIES)
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": lats, "longitude": lons,
                        "current": "temperature_2m,wind_speed_10m,wind_direction_10m,"
                                   "precipitation,cloud_cover,weather_code",
                    },
                )
                data = r.json()
        except Exception as e:
            log.warning(f"globe weather fetch failed: {e}")
            return {"cities": _weather_cache["cities"], "error": str(e)}
        results = data if isinstance(data, list) else [data]
        cities = []
        for (lat, lon), res in zip(_WORLD_CITIES, results):
            cur = res.get("current", {}) if isinstance(res, dict) else {}
            cities.append({
                "lat": lat, "lon": lon,
                "t": cur.get("temperature_2m", 0),
                "w": cur.get("wind_speed_10m", 0),
                "wd": cur.get("wind_direction_10m", 0),
                "p": cur.get("precipitation", 0),
                "c": cur.get("cloud_cover", 0),
                "wc": cur.get("weather_code", 0),
            })
        _weather_cache.update(ts=now, cities=cities)
        return {"cities": cities, "cached": False}

    @app.get("/api/globe/storms")
    async def globe_storms():
        """Active tropical cyclones from GDACS (cached 30 minutes)."""
        now = time.time()
        if now - _storms_cache["ts"] < _WEATHER_TTL:
            return {"storms": _storms_cache["storms"], "cached": True}
        storms = []
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    "https://www.gdacs.org/gdacsapi/api/events/geteventlist/MAP",
                    params={"eventtypes": "TC"},
                )
                seen = set()
                for feat in r.json().get("features", []):
                    props = feat.get("properties", {})
                    geom = feat.get("geometry") or {}
                    # GDACS mixes point events with track LineStrings — points only
                    if geom.get("type") != "Point":
                        continue
                    coords = geom.get("coordinates") or []
                    if len(coords) < 2 or not all(
                            isinstance(c, (int, float)) for c in coords[:2]):
                        continue
                    name = (props.get("eventname") or "CYCLONE").upper()
                    key = props.get("eventid") or name
                    if key in seen:
                        continue
                    seen.add(key)
                    storms.append({
                        "name": name,
                        "lat": coords[1], "lon": coords[0],
                        "level": (props.get("alertlevel") or "Green").lower(),
                    })
        except Exception as e:
            log.warning(f"GDACS storms fetch failed: {e}")
            return {"storms": _storms_cache["storms"], "error": str(e)}
        _storms_cache.update(ts=now, storms=storms)
        return {"storms": storms, "cached": False}

    @app.get("/api/globe/flights")
    async def globe_flights():
        """Every airborne aircraft OpenSky can see, trimmed for the globe's
        flights mode. Cached — anonymous OpenSky credits are limited."""
        now = time.time()
        if now - _flights_cache["ts"] < _FLIGHTS_TTL and _flights_cache["flights"]:
            return {"flights": _flights_cache["flights"], "cached": True}
        try:
            async with httpx.AsyncClient(timeout=25) as client:
                r = await client.get("https://opensky-network.org/api/states/all")
                states = r.json().get("states") or []
        except Exception as e:
            log.warning(f"OpenSky fetch failed: {e}")
            return {"flights": _flights_cache["flights"], "error": str(e)}
        flights = []
        for s in states:
            # state vector: 0 icao24, 1 callsign, 2 country, 5 lon, 6 lat,
            # 7 baro_alt, 8 on_ground, 9 velocity m/s, 10 true_track
            if s[5] is None or s[6] is None or s[8]:
                continue
            flights.append({
                "id": s[0],
                "cs": (s[1] or "").strip(),
                "lat": round(s[6], 2), "lon": round(s[5], 2),
                "alt": int(s[7] or 0),
                "v": int(s[9] or 0),
                "hdg": int(s[10] or 0),
                "co": s[2] or "",
            })
        _flights_cache.update(ts=now, flights=flights)
        return {"flights": flights, "cached": False}

    @app.get("/api/globe/flight/{callsign}")
    async def globe_flight(callsign: str):
        """Route lookup (origin → destination airports) for a picked plane."""
        cs = callsign.strip().upper()
        if not cs or len(cs) > 12 or not cs.isalnum():
            return {"route": None}
        if cs in _routes_cache:
            return {"route": _routes_cache[cs], "cached": True}
        route = None
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.get(f"https://api.adsbdb.com/v0/callsign/{cs}")
                resp = r.json().get("response")   # a string on unknown callsigns
                fr = resp.get("flightroute") if isinstance(resp, dict) else {}
                fr = fr or {}
                o, d = fr.get("origin") or {}, fr.get("destination") or {}
                if o.get("latitude") is not None and d.get("latitude") is not None:
                    route = {
                        "airline": (fr.get("airline") or {}).get("name", ""),
                        "from": {"iata": o.get("iata_code", ""),
                                 "city": o.get("municipality", ""),
                                 "lat": o["latitude"], "lon": o["longitude"]},
                        "to": {"iata": d.get("iata_code", ""),
                               "city": d.get("municipality", ""),
                               "lat": d["latitude"], "lon": d["longitude"]},
                    }
        except Exception as e:
            log.warning(f"route lookup {cs} failed: {e}")
            return {"route": None, "error": str(e)}
        _routes_cache[cs] = route            # cache misses too — no re-hammering
        return {"route": route, "cached": False}

    @app.post("/api/os/camera")
    async def os_camera(body: dict):
        """Camera button — start/stop the hand-tracking service."""
        on = bool(body.get("on", False))
        try:
            from hands.service import get_hands
            if on:
                get_hands().start()
            else:
                get_hands().stop()
            return {"camera": on}
        except Exception as e:
            log.error(f"hands toggle failed: {e}")
            return {"camera": False, "error": str(e)}

    @app.post("/api/os/voice")
    async def os_voice(body: dict):
        """Toggle in-OS voice mode — every utterance is a command, no wake word."""
        always_on = bool(body.get("always_on", False))
        try:
            from voice.browser_listener import get_listener
            get_listener().set_always_on(always_on)
        except Exception as e:
            log.warning(f"os_voice toggle failed: {e}")
        return {"always_on": always_on}

    @app.post("/api/os/shutdown")
    async def os_shutdown():
        """Close JARVIS OS. Shuts the machine down too only if JARVIS_SHUTDOWN_MACHINE=1."""
        log.info("OS shutdown requested from the shell")
        await broadcast("shutdown", {})
        threading.Thread(target=_shutdown_worker, daemon=True).start()
        return {"status": "shutting_down"}


def _shutdown_worker():
    time.sleep(1.5)  # let the response + broadcast flush
    if _os.environ.get("JARVIS_SHUTDOWN_MACHINE", "") in ("1", "true", "yes"):
        import subprocess
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to shut down'],
            timeout=10,
        )
    try:
        import webview
        for w in list(webview.windows):
            w.destroy()
    except Exception:
        pass
    time.sleep(0.5)
    _os._exit(0)
