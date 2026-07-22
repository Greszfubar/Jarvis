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

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from core.bus import bus

log = logging.getLogger("jarvis.os")

_OS_DIR = Path(__file__).parent / "os"

_STAGE_PLACEHOLDER = """<!DOCTYPE html>
<html><head><title>THE STAGE</title><style>
html,body{height:100%;margin:0;background:#000;color:rgba(242,244,246,.3);
display:flex;align-items:center;justify-content:center;
font-family:"Helvetica Neue",sans-serif;font-size:12px;letter-spacing:.6em;
text-transform:uppercase}</style></head>
<body>THE STAGE&nbsp;&mdash;&nbsp;PHASE 5</body></html>"""


def register_os(app: FastAPI, broadcast):
    """Attach OS routes. `broadcast(kind, payload)` is ui.web's client fan-out."""

    app.mount("/os/static", StaticFiles(directory=str(_OS_DIR)), name="os-static")

    @app.get("/os", response_class=HTMLResponse)
    async def os_page():
        return FileResponse(_OS_DIR / "index.html")

    @app.get("/stage", response_class=HTMLResponse)
    async def stage_page():
        return HTMLResponse(_STAGE_PLACEHOLDER)

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
