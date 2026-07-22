"""
Sub-app window management for Layer 2 specialist agents.

Phase 5 adds voice routing: opening a Layer 2 window (Ultron / Vision /
Friday / Gresz) mutes JARVIS and routes voice directly to that agent.
The agent greets you on open and voice returns to JARVIS when the window
closes.

Flow:
  1. User clicks agent button in JARVIS sidebar
  2. JS calls: window.pywebview.api.open_app('ultron')
  3. JarvisAPI.open_app() calls create_sub_window() in a thread
  4. pywebview 6.x dispatches create_window() to the macOS main run-loop
  5. New native window appears at /ultron (etc.)
  6. Active-agent state is set → voice now routes to Ultron
  7. Agent greeting is spoken via the TTS speaker
  8. When window closes → active-agent cleared → JARVIS gets voice back
"""
import logging
import threading
import time
import webbrowser

log = logging.getLogger("jarvis.subapps")

_HOST = "127.0.0.1"
_PORT = 8765

# ── Layer 2 agents that take over voice ──────────────────────────────────────
VOICE_AGENTS = {"ultron", "vision", "friday", "gresz"}

SUB_APPS = {
    "ultron": {
        "title":  "ULTRON — GreszTech Security",
        "path":   "/ultron",
        "width":  1440,
        "height": 900,
        "bg":     "#070707",
    },
    "vision": {
        "title":  "VISION — GreszTech Intelligence",
        "path":   "/vision",
        "width":  1440,
        "height": 900,
        "bg":     "#071a0f",
    },
    "friday": {
        "title":  "FRIDAY — GreszTech Content",
        "path":   "/friday",
        "width":  1440,
        "height": 900,
        "bg":     "#0f1923",
    },
    "gresz": {
        "title":  "GRESZ INDUSTRIES — AiOS Platform",
        "path":   "/gresz",
        "width":  1440,
        "height": 900,
        "bg":     "#080c14",
    },
    "newspaper": {
        "title":  "THE GRESZ GAZETTE",
        "path":   "/newspaper",
        "width":  1440,
        "height": 940,
        "bg":     "#f5f0e2",
    },
    "blog": {
        "title":  "GRESZ BLOG",
        "path":   "/blog",
        "width":  900,
        "height": 840,
        "bg":     "#0a0a0f",
    },
}

# ── Window handles ────────────────────────────────────────────────────────────
_windows: dict = {}
_lock = threading.Lock()

# ── Active voice agent ────────────────────────────────────────────────────────
_active_agent = None  # str | None
_agent_lock   = threading.Lock()


def get_active_agent():
    """Return the name of the agent currently owning the voice, or None."""
    with _agent_lock:
        return _active_agent


def _set_active_agent(name):
    global _active_agent
    with _agent_lock:
        _active_agent = name
    log.info(f"Voice active agent → {name or 'JARVIS'}")
    # Update browser listener wake words so "Hey Ultron" works when Ultron is open
    try:
        from voice.browser_listener import get_listener
        get_listener().set_wake_words({name} if name else set())
    except Exception:
        pass
    # Broadcast so the UI can show the indicator
    try:
        from core.bus import bus
        bus.publish_sync("voice.active_agent", {"agent": name})
    except Exception:
        pass


def _remove_window(name: str):
    """Called by pywebview's closed event."""
    with _lock:
        _windows.pop(name, None)
    log.info(f"Sub-app window closed: {name}")

    if name in VOICE_AGENTS:
        # Find any remaining voice-agent window
        with _lock:
            still_open = [k for k in _windows if k in VOICE_AGENTS]
        if not still_open:
            _set_active_agent(None)
            try:
                from voice.browser_listener import get_listener
                get_listener().skip_conversation_window()
            except Exception:
                pass
            try:
                from voice.speaker import speak
                speak("Returning voice control to JARVIS.")
            except Exception:
                pass
        elif get_active_agent() == name:
            # Another agent window is still open — give it voice
            _set_active_agent(still_open[-1])


# ── Greeting ──────────────────────────────────────────────────────────────────

def _build_greeting(name: str) -> str:
    """
    Build a fast, data-driven spoken greeting for an agent.
    Reads directly from SQLite so it works before JARVIS full-init.
    """
    import json, sqlite3
    from pathlib import Path

    def _kv(db, key, default=None):
        try:
            row = db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
            return json.loads(row[0]) if row else default
        except Exception:
            return default

    db_path = Path(f"data/specialists/{name}.db")

    if name == "ultron":
        wl, logs = [], []
        if db_path.exists():
            db = sqlite3.connect(str(db_path))
            wl   = _kv(db, "watchlist", [])
            logs = db.execute(
                "SELECT COUNT(*) FROM logs WHERE severity='alert' AND status='open'"
            ).fetchone()[0]
            db.close()
        threats = f"{logs} open threat{'s' if logs != 1 else ''}" if logs else "no open threats"
        wl_str  = f"{len(wl)} target{'s' if len(wl) != 1 else ''}" if wl else "no targets"
        return (f"Ultron online, sir. "
                f"Monitoring {wl_str} on the watchlist. "
                f"Security status: {threats}. "
                f"Tool vault and breach scanner are ready.")

    if name == "vision":
        events, plans = [], []
        if db_path.exists():
            db = sqlite3.connect(str(db_path))
            events = _kv(db, "cached_events", []) or []
            plans  = _kv(db, "plans", []) or []
            db.close()
        today = [e for e in events if e.get("today")]
        upcoming = events[:3]
        e_str = f"{len(today)} event{'s' if len(today) != 1 else ''} today" if today else "no events today"
        p_str = f"{len(plans)} plan{'s' if len(plans) != 1 else ''} in the vault" if plans else "no saved plans"
        next_e = f"Next up: {upcoming[0]['title']} at {upcoming[0].get('start','')[:16]}. " if upcoming else ""
        return (f"Vision reporting. "
                f"I have {e_str} and {p_str}. "
                f"{next_e}"
                f"Calendar and intelligence systems are ready.")

    if name == "friday":
        papers, blogs = [], []
        if db_path.exists():
            db = sqlite3.connect(str(db_path))
            papers = _kv(db, "papers", []) or []
            blogs  = _kv(db, "blogs",  []) or []
            db.close()
        paper_str = f"Today's Gazette is published — {papers[0].get('date','')}." if papers else "No edition published yet."
        blog_str  = f"{len(blogs)} blog post{'s' if len(blogs) != 1 else ''} in the archive." if blogs else "No blogs yet."
        return (f"FRIDAY here, sir. "
                f"{paper_str} "
                f"{blog_str} "
                f"News feeds and content systems are ready.")

    if name == "gresz":
        projects, pipeline, clients = [], [], []
        if db_path.exists():
            db = sqlite3.connect(str(db_path))
            projects = _kv(db, "projects", []) or []
            pipeline = _kv(db, "pipeline", []) or []
            clients  = _kv(db, "clients",  []) or []
            db.close()
        active  = [p for p in projects if p.get("status") == "active"]
        overdue = [p for p in projects if p.get("overdue")]
        pipe_v  = sum(
            float(str(d.get("value","0")).replace("$","").replace(",","").split()[0] or 0)
            for d in pipeline if d.get("value")
        )
        a_str = f"{len(active)} active project{'s' if len(active) != 1 else ''}"
        o_str = f", {len(overdue)} overdue" if overdue else ""
        p_str = f"Pipeline value: ${pipe_v:,.0f} across {len(pipeline)} deal{'s' if len(pipeline) != 1 else ''}." if pipeline else "No deals in pipeline."
        c_str = f"{len(clients)} client{'s' if len(clients) != 1 else ''} on file." if clients else ""
        return (f"GRESZ Industries online, sir. "
                f"I'm tracking {a_str}{o_str}. "
                f"{p_str} "
                f"{c_str} "
                f"Business intelligence systems ready.")

    return f"{name.title()} online."


def _deliver_greeting(name: str):
    """Wait for window to render, then speak the greeting. Runs in a thread."""
    time.sleep(1.8)   # Let the window finish loading
    try:
        # Mark as proactive speech so TTS playback does NOT open a conversation window
        # (the agent is speaking, not responding to a command, so we don't want
        # the mic to treat whatever comes next as a free-form reply)
        try:
            from voice.browser_listener import get_listener
            get_listener().skip_conversation_window()
        except Exception:
            pass
        from voice.speaker import speak
        speak(_build_greeting(name))
    except Exception as e:
        log.error(f"Greeting error for {name}: {e}")


# ── Window creation ───────────────────────────────────────────────────────────

def create_sub_window(name: str):
    """Create (or focus) a sub-app window. Safe to call from any thread."""
    import webview
    cfg = SUB_APPS.get(name)
    if not cfg:
        log.warning(f"Unknown sub-app: {name}")
        return

    url = f"http://{_HOST}:{_PORT}{cfg['path']}"

    with _lock:
        existing = _windows.get(name)
        if existing is not None:
            try:
                existing.evaluate_js("window.focus()")
                log.info(f"Focused existing sub-app window: {name}")
                # Re-activate voice for this agent if it's a voice agent
                if name in VOICE_AGENTS:
                    _set_active_agent(name)
                return
            except Exception:
                _windows.pop(name, None)

        try:
            w = webview.create_window(
                title            = cfg["title"],
                url              = url,
                width            = cfg["width"],
                height           = cfg["height"],
                background_color = cfg["bg"],
                text_select      = (name == "blog"),
                min_size         = (900, 600),
            )
            w.events.closed += lambda: _remove_window(name)
            _windows[name] = w
            log.info(f"Opened sub-app window: {name}")
        except Exception as e:
            log.error(f"Failed to open sub-app {name}: {e}")
            return

    # Voice takeover + greeting (outside lock, in a thread)
    if name in VOICE_AGENTS:
        _set_active_agent(name)
        threading.Thread(target=_deliver_greeting, args=(name,), daemon=True).start()


# ── JarvisAPI ─────────────────────────────────────────────────────────────────

class JarvisAPI:
    """
    Python object exposed to the JARVIS webview window via js_api.
    JS calls:  window.pywebview.api.open_app('ultron')
    """

    def open_app(self, name: str) -> dict:
        """Open or focus a specialist app window."""
        threading.Thread(
            target=create_sub_window, args=(name,), daemon=True
        ).start()
        return {"status": "opening", "app": name}

    def open_url(self, url: str) -> dict:
        """Open a URL in the system default browser."""
        if url and url.startswith(("http://", "https://")):
            threading.Thread(
                target=webbrowser.open, args=(url,), daemon=True
            ).start()
            return {"status": "opening", "url": url}
        return {"status": "blocked", "reason": "invalid url"}

    def open_newspaper(self) -> dict:
        """Open (or focus) the Gazette newspaper window."""
        threading.Thread(
            target=create_sub_window, args=("newspaper",), daemon=True
        ).start()
        return {"status": "opening", "app": "newspaper"}

    def open_blog(self, blog_id) -> dict:
        """Open a blog post in its own reader window."""
        def _open():
            import webview
            cfg_b = SUB_APPS["blog"]
            url   = f"http://{_HOST}:{_PORT}{cfg_b['path']}?id={blog_id}"
            key   = f"blog_{blog_id}"
            with _lock:
                existing = _windows.get(key)
                if existing is not None:
                    try:
                        existing.evaluate_js("window.focus()")
                        return
                    except Exception:
                        _windows.pop(key, None)
                try:
                    w = webview.create_window(
                        title            = cfg_b["title"],
                        url              = url,
                        width            = cfg_b["width"],
                        height           = cfg_b["height"],
                        background_color = cfg_b["bg"],
                        text_select      = True,
                        min_size         = (700, 500),
                    )
                    w.events.closed += lambda: _remove_window(key)
                    _windows[key] = w
                    log.info(f"Opened blog reader: {key}")
                except Exception as e:
                    log.error(f"Failed to open blog reader: {e}")
        threading.Thread(target=_open, daemon=True).start()
        return {"status": "opening", "blog_id": blog_id}
