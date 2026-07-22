"""JARVIS Web Dashboard — cinematic redesign with audio core, modals, crypto, news."""
import asyncio
import json
import logging
import sqlite3 as _sqlite3
from datetime import datetime
from pathlib import Path as _Path
from typing import List

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core.bus import bus
from core.memory import Memory

log = logging.getLogger("jarvis.web")
app = FastAPI(title="JARVIS")
mem = Memory()
_clients: List[WebSocket] = []

# ── Persistent DB helpers ─────────────────────────────────────────────────────

_SPECIALIST_DIR = _Path("data/specialists")
_SPECIALIST_DIR.mkdir(parents=True, exist_ok=True)

def _db(name: str) -> _sqlite3.Connection:
    """
    Return an open SQLite connection for the named specialist.
    Creates the file + schema on first call — works before JARVIS full-init.
    """
    path = _SPECIALIST_DIR / f"{name}.db"
    conn = _sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = _sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kv (
            key   TEXT PRIMARY KEY,
            value TEXT,
            ts    TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts        TEXT    NOT NULL DEFAULT (datetime('now')),
            severity  TEXT    NOT NULL DEFAULT 'info',
            category  TEXT    NOT NULL DEFAULT 'general',
            title     TEXT    NOT NULL,
            detail    TEXT,
            status    TEXT    NOT NULL DEFAULT 'open',
            progress  INTEGER DEFAULT 0,
            url       TEXT
        )
    """)
    conn.commit()
    return conn

def _kv_get(name: str, key: str, default=None):
    """Read a JSON value from a specialist's KV store."""
    db = _db(name)
    row = db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
    db.close()
    if row is None:
        return default
    try:
        return json.loads(row["value"])
    except Exception:
        return default

def _kv_set(name: str, key: str, value):
    """Write a JSON value to a specialist's KV store."""
    db = _db(name)
    db.execute(
        "INSERT OR REPLACE INTO kv (key,value,ts) VALUES (?,?,datetime('now'))",
        (key, json.dumps(value))
    )
    db.commit()
    db.close()


# ── JARVIS OS (MK II) pages + endpoints ──────────────────────────────────────
from ui.os_routes import register_os
register_os(app, lambda kind, payload: _broadcast(kind, payload))


@app.on_event("startup")
async def _setup_bus():
    bus.subscribe("jarvis.alert",        lambda p: asyncio.create_task(_broadcast("alert",     p)))
    bus.subscribe("jarvis.briefing",     lambda p: asyncio.create_task(_broadcast("briefing",  p)))
    bus.subscribe("gmail.new",           lambda p: asyncio.create_task(_broadcast("gmail",     p)))
    bus.subscribe("calendar.upcoming",   lambda p: asyncio.create_task(_broadcast("calendar",  p)))
    bus.subscribe("taskboard.completed", lambda p: asyncio.create_task(_broadcast("task_done", p)))
    # Speaking state — mutes browser mic capture while JARVIS speaks + sends text
    bus.subscribe("jarvis.speaking", lambda p: asyncio.create_task(
        _broadcast("speaking", {"text": p.get("text", "")}) if p.get("speaking")
        else _broadcast("speaking_done", {})))


async def _broadcast(kind: str, payload: dict):
    dead = []
    for ws in list(_clients):
        try:
            await ws.send_text(json.dumps({"kind": kind, "ts": datetime.utcnow().isoformat(), **payload}))
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _clients:
            _clients.remove(ws)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    _clients.append(ws)
    try:
        while True:
            data = await ws.receive_text()
            if not data.strip():
                continue
            await ws.send_text(json.dumps({"kind": "typing"}))
            try:
                from core.orchestrator import orchestrator
                response = await orchestrator.process(data)
            except Exception as e:
                response = f"Error: {e}"
            await ws.send_text(json.dumps({"kind": "response", "text": response}))
            # Speak every response aloud — JARVIS is an audio agent
            try:
                from voice.speaker import speak
                import threading
                threading.Thread(target=speak, args=(response,), daemon=True).start()
            except Exception:
                pass
    except WebSocketDisconnect:
        if ws in _clients:
            _clients.remove(ws)


@app.websocket("/ws/audio")
async def ws_audio_endpoint(ws: WebSocket):
    """Receives raw Int16 PCM at 16 kHz from browser JS. Feeds BrowserListener."""
    await ws.accept()
    log.info("Browser audio stream connected")
    try:
        from voice.browser_listener import get_listener
        listener = get_listener()

        async def notify(kind: str, payload: dict):
            await _broadcast(kind, payload)

        listener._notify = notify

        while True:
            data = await ws.receive_bytes()
            await listener.process_chunk(data)
    except WebSocketDisconnect:
        log.info("Browser audio stream disconnected")
    except Exception as e:
        log.error(f"Audio WS error: {e}")


@app.get("/api/status")
async def api_status():
    weather = mem.get_fact("weather_current") or {}
    return {
        "weather":  weather,
        "unread":   mem.get_fact("gmail_unread_count") or 0,
        "tasks":    len(mem.get_fact("tasks_pending") or []),
        "events":   len(mem.get_fact("calendar_upcoming") or []),
        "news":     (mem.get_fact("news_general") or {}).get("articles", [])[:12],
        "calendar": (mem.get_fact("calendar_upcoming") or [])[:20],
        "forecast": mem.get_fact("weather_forecast") or [],
    }


@app.get("/api/tasks")
async def api_tasks():
    try:
        from agents.taskboard import get_all_tasks_json
        return {"tasks": get_all_tasks_json()}
    except Exception as e:
        return {"tasks": [], "error": str(e)}


class TaskCreate(BaseModel):
    title:    str
    priority: str = "medium"
    category: str = "general"
    assignee: str = "human"

class TaskStatusUpdate(BaseModel):
    status: str

@app.patch("/api/tasks/{task_id}/status")
async def api_update_task_status(task_id: int, body: TaskStatusUpdate):
    try:
        from agents.taskboard import _db
        db = _db()
        db.execute("UPDATE tasks SET status=?, updated=datetime('now') WHERE id=?",
                   (body.status, task_id))
        db.commit()
        return {"status": "updated"}
    except Exception as e:
        return {"error": str(e)}

@app.delete("/api/tasks/{task_id}")
async def api_delete_task(task_id: int):
    try:
        from agents.taskboard import _db
        db = _db()
        db.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        db.commit()
        return {"status": "deleted"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/tasks")
async def api_add_task(body: TaskCreate):
    try:
        from agents.taskboard import TaskBoardAgent
        agent = TaskBoardAgent()
        result = await agent.execute("add_task", {
            "title":    body.title,
            "priority": body.priority,
            "category": body.category,
            "assignee": body.assignee,
        })
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/memory")
async def api_memory():
    history = mem.get_history(limit=50)
    facts_raw = mem._db.execute(
        "SELECT key, value, updated FROM facts ORDER BY updated DESC LIMIT 60"
    ).fetchall()
    facts = [{"key": r["key"], "value": r["value"][:200], "updated": r["updated"]} for r in facts_raw]
    return {"history": history, "facts": facts}


@app.get("/api/para")
async def api_para():
    from core.para_memory import LIFE_DIR, get_profile
    entities = []
    for cat in ("projects", "areas", "resources"):
        cat_dir = LIFE_DIR / cat
        if cat_dir.exists():
            for e in cat_dir.iterdir():
                s = e / "summary.md"
                if s.exists():
                    entities.append({"category": cat, "name": e.name,
                                     "summary": s.read_text()[:300]})
    daily_dir = LIFE_DIR / "daily"
    notes = sorted(daily_dir.glob("*.md"), reverse=True)[:7] if daily_dir.exists() else []
    note_list = [{"date": n.stem, "preview": n.read_text()[:400]} for n in notes]
    return {"entities": entities, "daily_notes": note_list, "profile": get_profile()}


@app.get("/api/crypto")
async def api_crypto():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "bitcoin,ethereum,solana,cardano,dogecoin",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                }
            )
            return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/mute")
async def api_mute(body: dict = {}):
    muted = body.get("muted", True)
    try:
        from voice.browser_listener import get_listener
        get_listener().set_muted(muted)
        # Suppress conversation window when user manually mutes/unmutes
        if not muted:
            get_listener().skip_conversation_window()
    except Exception:
        pass
    return {"muted": muted}


@app.get("/api/reminders")
async def api_reminders():
    """Fetch Apple Reminders via osascript."""
    script = """
    tell application "Reminders"
        set output to {}
        set allReminders to every reminder whose completed is false
        repeat with r in allReminders
            set rName to name of r
            set rDue to ""
            try
                set rDue to due date of r as string
            end try
            set end of output to rName & "|||" & rDue
        end repeat
        return output
    end tell
    """
    try:
        result = await asyncio.to_thread(
            lambda: __import__("subprocess").run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=10
            )
        )
        items = []
        if result.returncode == 0:
            raw = result.stdout.strip()
            if raw:
                for line in raw.split(", "):
                    line = line.strip()
                    if "|||" in line:
                        name, due = line.split("|||", 1)
                        items.append({"title": name.strip(), "due": due.strip()})
                    elif line:
                        items.append({"title": line, "due": ""})
        return {"reminders": items}
    except Exception as e:
        return {"reminders": [], "error": str(e)}


# Set JARVIS_TOOLS_PASSWORD in config/.env — the tools panel is disabled without it.
# (The old hardcoded password is burned: it shipped in a public repo.)
def _tools_password() -> str:
    from core.config import env as _env
    return _env("JARVIS_TOOLS_PASSWORD", "")

TOOL_CATALOG = [
    {"key": "ANTHROPIC_API_KEY",    "name": "Claude AI",         "desc": "Core AI engine (Anthropic)",          "required": True,  "docs": "https://console.anthropic.com"},
    {"key": "TELEGRAM_BOT_TOKEN",   "name": "Telegram Bot",      "desc": "Remote control via Telegram",         "required": False, "docs": "https://t.me/BotFather"},
    {"key": "TELEGRAM_CHAT_ID",     "name": "Telegram Chat ID",  "desc": "Your Telegram numeric chat ID",       "required": False, "docs": "https://t.me/BotFather"},
    {"key": "NEWSAPI_KEY",          "name": "NewsAPI",           "desc": "Live news headlines feed",            "required": False, "docs": "https://newsapi.org"},
    {"key": "ELEVENLABS_API_KEY",   "name": "ElevenLabs TTS",    "desc": "High-quality voice synthesis",        "required": False, "docs": "https://elevenlabs.io"},
    {"key": "ELEVENLABS_VOICE_ID",  "name": "ElevenLabs Voice",  "desc": "Voice ID for ElevenLabs TTS",         "required": False, "docs": "https://elevenlabs.io"},
    {"key": "OPENWEATHERMAP_KEY",   "name": "OpenWeatherMap",    "desc": "Alternate weather provider",          "required": False, "docs": "https://openweathermap.org/api"},
    {"key": "GOOGLE_CLIENT_ID",     "name": "Google OAuth",      "desc": "Gmail & Calendar access",             "required": False, "docs": "https://console.cloud.google.com"},
    {"key": "WEATHER_CITY",         "name": "Weather Location",  "desc": "City name for weather (no country)",  "required": True,  "docs": ""},
    {"key": "USER_NAME",            "name": "Your Name",         "desc": "How JARVIS addresses you",            "required": True,  "docs": ""},
    {"key": "TTS_ENGINE",           "name": "TTS Engine",        "desc": "macos_say or elevenlabs",             "required": True,  "docs": ""},
    {"key": "MACOS_VOICE",          "name": "macOS Voice",       "desc": "e.g. Daniel, Samantha, Alex",         "required": False, "docs": ""},
    {"key": "HIBP_API_KEY",         "name": "HaveIBeenPwned",    "desc": "Email breach checking (ULTRON)",       "required": False, "docs": "https://haveibeenpwned.com/API/Key"},
]

def _read_env_file() -> dict:
    from pathlib import Path
    env_path = Path("config/.env")
    vals = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                vals[k.strip()] = v.strip()
    return vals

def _write_env_key(key: str, value: str):
    from pathlib import Path
    env_path = Path("config/.env")
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}=") or line.strip().startswith(f"{key} ="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")
    env_path.write_text("\n".join(new_lines) + "\n")

@app.get("/api/tools")
async def api_tools(password: str = ""):
    expected = _tools_password()
    if not expected or password != expected:
        return {"error": "unauthorized"}
    env_vals = _read_env_file()
    tools = []
    for t in TOOL_CATALOG:
        val = env_vals.get(t["key"], "")
        # Never return raw secrets — masked preview only (last 4 chars)
        sensitive = any(w in t["key"].upper() for w in ("KEY", "TOKEN", "SECRET", "PASSWORD"))
        masked = ("•" * 8 + val[-4:]) if val and len(val) > 4 and sensitive else val
        tools.append({**t, "value": "" if sensitive else val, "masked": masked, "configured": bool(val)})
    return {"tools": tools}

class ToolUpdate(BaseModel):
    password: str
    key:      str
    value:    str

@app.post("/api/tools")
async def api_tools_update(body: ToolUpdate):
    expected = _tools_password()
    if not expected or body.password != expected:
        return {"error": "unauthorized"}
    _write_env_key(body.key, body.value)
    return {"status": "saved"}


@app.post("/api/standby/activate")
async def standby_activate():
    """Manual unlock — called when user enters the correct password on the standby screen."""
    try:
        from main import manual_activate
        await manual_activate()
        return {"status": "activated"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    from ui.dashboard import DASHBOARD_HTML as _DASH
    return HTMLResponse(_DASH)


@app.post("/api/tasks/jarvis-auto")
async def jarvis_auto_task():
    """Called every 20 minutes by the UI to have JARVIS generate an autonomous task."""
    import time as _time
    try:
        from agents.taskboard import TaskBoardAgent
        agent = TaskBoardAgent()
        tasks_result = await agent.execute("list_tasks", {})
        current = tasks_result.get("tasks", [])
        jarvis_open = [t for t in current if t.get("assignee") == "jarvis" and t.get("status") not in ("done", "blocked")]
        # Cap at 5 autonomous JARVIS tasks at once
        if len(jarvis_open) >= 5:
            return {"status": "skipped", "reason": "task queue full", "count": len(jarvis_open)}
        # Use Claude to suggest the next task
        try:
            import anthropic
            from core.config import env
            client = anthropic.Anthropic(api_key=env("ANTHROPIC_API_KEY", ""))
            existing_titles = [t["title"] for t in jarvis_open[:3]]
            msg = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=80,
                messages=[{"role": "user", "content":
                    f"You are JARVIS, an autonomous AI assistant. Today is {datetime.now().strftime('%A %d %B %Y %H:%M')}. "
                    f"Current open tasks: {existing_titles}. "
                    f"Suggest ONE specific self-management task you should do right now to be helpful and proactive. "
                    f"Reply with ONLY the task title, 5-10 words, actionable. No explanation, no quotes."}])
            task_title = msg.content[0].text.strip().strip('"\'')
        except Exception:
            # Fallback task catalogue if Claude unavailable
            import random
            fallbacks = [
                "Review and summarise today's news headlines",
                "Check for new security alerts and breaches",
                "Update strategic plans with today's context",
                "Analyse upcoming calendar events and prepare briefs",
                "Check weather forecast and flag outdoor conflicts",
            ]
            task_title = random.choice([t for t in fallbacks if t not in [x["title"] for x in jarvis_open]] or fallbacks)
        result = await agent.execute("add_task", {
            "title": task_title,
            "priority": "medium",
            "category": "autonomous",
            "assignee": "jarvis",
        })
        return {"status": "created", "task": result.get("task", {})}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Sub-app routes ────────────────────────────────────────────────────────────

@app.get("/ultron", response_class=HTMLResponse)
async def ultron_app():
    from ui.apps.ultron import HTML
    return HTMLResponse(HTML)


@app.get("/vision", response_class=HTMLResponse)
async def vision_app():
    from ui.apps.vision import HTML
    plans = _kv_get("vision", "plans", [])
    plans_json = json.dumps(plans).replace("</", "<\\/")
    injected = f'<script>window._serverPlans={plans_json};</script>'
    return HTMLResponse(HTML.replace('</head>', injected + '</head>'))


@app.get("/friday", response_class=HTMLResponse)
async def friday_app():
    from ui.apps.friday import HTML
    return HTMLResponse(HTML)


@app.get("/gresz", response_class=HTMLResponse)
async def gresz_app():
    from ui.apps.gresz import HTML
    return HTMLResponse(HTML)


@app.get("/newspaper", response_class=HTMLResponse)
async def newspaper_app():
    from ui.apps.newspaper import HTML
    # Inject papers data server-side so the page renders immediately
    # without needing a second fetch round-trip (which can fail in webview)
    papers = _kv_get("friday", "papers", [])
    papers_json = json.dumps(papers).replace("</", "<\\/")
    injected = f'<script>window._serverPapers={papers_json};</script>'
    return HTMLResponse(HTML.replace('</head>', injected + '</head>'))


@app.get("/blog", response_class=HTMLResponse)
async def blog_reader_app():
    from ui.apps.blog_reader import HTML
    return HTMLResponse(HTML)


# ── Utility endpoints ────────────────────────────────────────────────────────

@app.get("/api/voice/active")
async def voice_active():
    """Which Layer 2 agent currently owns the voice pipeline (if any)."""
    from ui.sub_apps import get_active_agent
    return {"agent": get_active_agent()}


@app.post("/api/open_url")
async def api_open_url(body: dict):
    """
    Open a URL in the system default browser.
    Used by sub-app windows that don't have pywebview js_api attached.
    """
    import webbrowser, threading
    url = body.get("url", "")
    if url and url.startswith(("http://", "https://")):
        threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
        return {"status": "opening"}
    return {"status": "blocked"}


@app.post("/api/open_app")
async def api_open_app(body: dict):
    """
    Open a native sub-app window from any window (including sub-apps).
    body: {app: 'newspaper'} or {app: 'blog', id: 1234567}
    """
    from ui.sub_apps import create_sub_window
    import threading
    app_name = body.get("app", "")
    blog_id  = body.get("id")

    if app_name == "blog" and blog_id is not None:
        # Blog windows get dynamic URLs — use the JarvisAPI helper
        from ui.sub_apps import JarvisAPI
        JarvisAPI().open_blog(blog_id)
        return {"status": "opening", "app": "blog", "id": blog_id}

    if app_name:
        threading.Thread(target=create_sub_window, args=(app_name,), daemon=True).start()
        return {"status": "opening", "app": app_name}

    return {"status": "error", "reason": "no app specified"}


# ── Chat HTTP endpoint (used by sub-app windows) ─────────────────────────────

@app.post("/api/chat")
async def chat_http(body: dict):
    """HTTP POST chat — for specialist sub-app command bars (Vision, FRIDAY, GRESZ)."""
    text = (body.get("message") or body.get("text") or "").strip()
    if not text:
        return {"response": ""}
    try:
        from core.orchestrator import orchestrator
        response = await orchestrator.process(text)
    except Exception as e:
        log.error(f"chat_http error: {e}")
        response = f"Error: {e}"
    return {"response": response}


# ── Brain / Hard Drive API ────────────────────────────────────────────────────

@app.get("/api/brain/hardrive")
async def brain_hardrive_get():
    """Return hard drive items. Bootstrap from profile + filtered facts on first call."""
    import time as _time
    items = _kv_get("jarvis", "brain_hardrive", [])
    if not items:
        items = _bootstrap_hardrive()
    return {"items": items}


@app.post("/api/brain/hardrive")
async def brain_hardrive_save(body: dict):
    """Save an item to the hard drive (called when JARVIS flags something important)."""
    import time as _time
    items = _kv_get("jarvis", "brain_hardrive", [])
    item = {
        "id":      int(_time.time() * 1000),
        "tab":     body.get("tab", "memories"),
        "title":   body.get("title", ""),
        "content": body.get("content", ""),
        "tags":    body.get("tags", []),
        "ts":      datetime.utcnow().isoformat(),
        "source":  body.get("source", "jarvis"),
    }
    # Avoid duplicate titles
    if not any(x.get("title") == item["title"] for x in items):
        items.append(item)
        _kv_set("jarvis", "brain_hardrive", items)
    return {"item": item, "items": items}


def _bootstrap_hardrive() -> list:
    """Build a first-run hard drive from config, tasks, and conversation history.

    Skips ALL ephemeral cache keys (weather, news, geo, briefing dates, etc.).
    Intelligently extracts goals/exams from tasks_pending.
    Scans recent conversation for personal facts worth keeping.
    """
    from core.config import env
    import time as _time
    import json as _json
    ts = datetime.utcnow().isoformat()
    items: list = []
    seen_titles: set = set()

    def _add(tab, title, content, tags=None, source="config"):
        if not content or not title:
            return
        t = str(title).strip()
        c = str(content).strip()[:240]
        if not t or not c or t in seen_titles:
            return
        seen_titles.add(t)
        items.append({
            "id":     int(_time.time() * 1000) + len(items),
            "tab":    tab,
            "title":  t,
            "content": c,
            "tags":   tags or [],
            "ts":     ts,
            "source": source,
        })

    # ── Identity from config ───────────────────────────────────────────────────
    name = env("USER_NAME", "")
    if name:
        _add("info", "Name", name, ["identity", "personal"])
    _add("info", "Home", "Petersfield, Hampshire, UK", ["location", "home"])

    # ── Parse tasks_pending for meaningful deadlines / goals ──────────────────
    try:
        tasks_raw = mem.get_fact("tasks_pending") or []
        for t in tasks_raw:
            title = (t.get("title") or "").strip()
            due   = (t.get("due") or "").strip()
            if not title or len(title) < 4:
                continue
            # Skip today-slot markers like "Today: Maths 09:30"
            if title.lower().startswith("today:"):
                slot = title[6:].strip()
                if slot:
                    _add("info", f"Daily slot: {slot}", f"Regular session — {slot}", ["schedule", "study"], "tasks")
                continue
            # Classify exam/deadline entries
            tl = title.lower()
            if any(w in tl for w in ("exam", "igcse", "alevel", "a-level", "gcse", "test", "assessment")):
                content = f"Exam: {title}" + (f" — due {due}" if due and due != "—" else "")
                _add("goals", title, content, ["exam", "deadline"], "tasks")
            elif any(w in tl for w in ("deadline", "submit", "due", "assignment", "coursework")):
                content = f"Deadline: {title}" + (f" — {due}" if due else "")
                _add("goals", title, content, ["deadline"], "tasks")
            elif len(title) > 6:
                content = title + (f" — due {due}" if due and due != "—" else "")
                _add("memories", title, content, ["task"], "tasks")
    except Exception:
        pass

    # ── Filtered persistent facts (skip ALL ephemeral/cache keys) ─────────────
    # Anything in this set (substring match) is noise — skip it entirely.
    SKIP_SUBSTRINGS = {
        "weather", "news", "gmail", "crypto", "forecast", "geo_",
        "temp", "humidity", "wind", "city_id", "calendar_upcoming",
        "tasks_pending", "news_general", "news_technology",
        "briefing_delivered", "delivered_date", "unread_prev",
        "unread_count", "city_id", "uptime", "last_scan",
    }
    try:
        rows = mem._db.execute(
            "SELECT key, value, updated FROM facts ORDER BY updated DESC LIMIT 80"
        ).fetchall()
        for row in rows:
            k = row["key"]
            kl = k.lower()
            if any(s in kl for s in SKIP_SUBSTRINGS):
                continue
            v = row["value"]
            if not v or v in ("null", "{}", "[]", ""):
                continue
            try:
                pv = _json.loads(v)
                # Skip dicts/lists — too noisy. Keep primitives only.
                if isinstance(pv, (dict, list)):
                    continue
                v_str = str(pv).strip()
            except Exception:
                v_str = str(v).strip()
            if len(v_str) < 3 or len(v_str) > 240:
                continue
            label = k.replace("_", " ").title()
            if any(w in kl for w in ("goal", "plan", "want", "objective", "project")):
                _add("goals",     label, v_str, [k], "memory")
            elif any(w in kl for w in ("person", "contact", "relation", "friend", "family", "company")):
                _add("relations", label, v_str, [k], "memory")
            elif any(w in kl for w in ("remember", "event", "happened", "said", "told", "prefer", "like", "dislike")):
                _add("memories",  label, v_str, [k], "memory")
            else:
                _add("info",      label, v_str, [k], "memory")
    except Exception:
        pass

    # ── Scan recent conversation for personal facts ────────────────────────────
    # Look for strong signals: exam dates, preferences, names, goals stated by user
    try:
        rows = mem._db.execute(
            "SELECT role, content FROM conversation ORDER BY ts DESC LIMIT 60"
        ).fetchall()
        import re as _re
        for row in rows:
            if row["role"] != "user":
                continue
            txt = str(row["content"] or "")[:500]
            # Exam / deadline pattern: "Biology exam May 12", "maths on the 9th"
            exam_m = _re.search(
                r'(?i)([\w\s]+?)\s+exam\s+(?:on\s+)?([\w\s,]+?\d{1,2})',
                txt
            )
            if exam_m:
                subj = exam_m.group(1).strip()[:40]
                date = exam_m.group(2).strip()[:30]
                if len(subj) > 2:
                    _add("goals", f"{subj.title()} Exam", f"Exam on {date}", ["exam", "deadline"], "conversation")
            # "I want to / I'm trying to / my goal is"
            goal_m = _re.search(
                r'(?i)(?:i want to|i\'m trying to|my goal is|i need to|i\'m working on)\s+(.{8,60}?)(?:[.!?]|$)',
                txt
            )
            if goal_m:
                g = goal_m.group(1).strip().rstrip(".,!?")
                if len(g) > 6:
                    _add("goals", g[:60].title(), g, ["goal", "aspiration"], "conversation")
    except Exception:
        pass

    if items:
        _kv_set("jarvis", "brain_hardrive", items)
    return items


@app.delete("/api/brain/hardrive")
async def brain_hardrive_clear():
    """Reset hard drive so it re-bootstraps on next GET."""
    _kv_set("jarvis", "brain_hardrive", [])
    return {"status": "cleared"}


# ── Specialist agent API ──────────────────────────────────────────────────────

@app.post("/api/specialist/{name}/command")
async def specialist_command(name: str, body: dict):
    """
    Generic command endpoint — routes a free-text command to the named
    specialist agent's execute("command", ...) method.
    Used by JARVIS orchestrator's [ACTION:agent:name|text] handler.
    """
    text = (body.get("text") or body.get("message") or "").strip()
    if not text:
        return {"message": "No command provided."}
    try:
        # Lazy-import so this works before full agent boot
        agent_map = {
            "vision":  ("agents.vision_agent",  "VisionAgent"),
            "ultron":  ("agents.ultron_agent",  "UltronAgent"),
            "friday":  ("agents.friday_agent",  "FridayAgent"),
            "gresz":   ("agents.gresz_agent",   "GreszAgent"),
        }
        if name not in agent_map:
            return {"error": f"Unknown agent: {name}"}
        module_path, class_name = agent_map[name]
        import importlib
        mod   = importlib.import_module(module_path)
        cls   = getattr(mod, class_name)
        agent = cls()
        result = await agent.execute("command", {"text": text})
        return result
    except Exception as e:
        log.error(f"specialist_command [{name}] error: {e}")
        return {"message": f"Agent {name} encountered an error: {e}"}


@app.get("/api/specialist/{name}/logs")
async def specialist_logs(name: str, limit: int = 50, severity: str = ""):
    db = _db(name)
    q = "SELECT * FROM logs"
    params: list = []
    if severity:
        q += " WHERE severity=?"
        params.append(severity)
    q += " ORDER BY ts DESC LIMIT ?"
    params.append(limit)
    rows = db.execute(q, params).fetchall()
    db.close()
    return {"logs": [dict(r) for r in rows]}


@app.post("/api/specialist/{name}/logs")
async def specialist_add_log(name: str, body: dict):
    """Manually add a log entry (e.g. from UI)."""
    db = _db(name)
    cur = db.execute(
        "INSERT INTO logs (title, detail, severity, category, url) VALUES (?,?,?,?,?)",
        (body.get("title",""), body.get("detail",""),
         body.get("severity","info"), body.get("category","general"),
         body.get("url",""))
    )
    db.commit()
    lid = cur.lastrowid
    db.close()
    return {"id": lid, "status": "created"}


@app.get("/api/specialist/vision/events")
async def vision_events(hours: int = 168):
    from agents.vision_agent import get_events
    events = await asyncio.get_event_loop().run_in_executor(None, get_events, hours)
    return {"events": events}


@app.get("/api/specialist/vision/today")
async def vision_today():
    from agents.vision_agent import get_today_events
    events = await asyncio.get_event_loop().run_in_executor(None, get_today_events)
    return {"events": events}


@app.get("/api/specialist/vision/plans")
async def vision_plans_get():
    return {"plans": _kv_get("vision", "plans", [])}


@app.post("/api/specialist/vision/plans")
async def vision_plans_save(body: dict):
    """body: {plans: [...]} — full replace"""
    plans = body.get("plans", [])
    _kv_set("vision", "plans", plans)
    return {"plans": plans}


@app.get("/api/specialist/friday/news")
async def friday_news(category: str = "general", count: int = 8):
    from agents.friday_agent import fetch_news
    articles = await asyncio.get_event_loop().run_in_executor(
        None, fetch_news, category, count
    )
    return {"category": category, "articles": articles}


@app.get("/api/specialist/friday/news/all")
async def friday_news_all():
    from agents.friday_agent import fetch_all_categories
    cats = await asyncio.get_event_loop().run_in_executor(None, fetch_all_categories, 5)
    return {"categories": cats}


@app.get("/api/specialist/friday/papers")
async def friday_papers_get():
    return {"papers": _kv_get("friday", "papers", [])}


@app.post("/api/specialist/friday/papers/generate")
async def friday_generate_paper():
    """Generate a full multi-section newspaper via the FridayAgent."""
    from core.orchestrator import orchestrator
    agent = next(
        (a for a in orchestrator._agents.values() if getattr(a, 'name', '') == 'friday'),
        None
    )
    if agent:
        paper = await agent.auto_daily_newspaper()
        if paper:
            return {"paper": paper}
    # Fallback: direct generation (static methods — no instantiation needed)
    import time as _time
    from agents.friday_agent import fetch_news, generate_newspaper, FridayAgent
    articles = await asyncio.get_event_loop().run_in_executor(None, fetch_news, "general", 10)
    content  = await generate_newspaper(articles)
    paper = {
        "id":       int(_time.time()),
        "date":     datetime.now().strftime("%d %B %Y"),
        "content":  content,
        "headline": FridayAgent._extract_headline(content),
        "sources":  list({a["source"] for a in articles[:5]}),
        "sections": FridayAgent._parse_sections(content),
    }
    papers = _kv_get("friday", "papers", [])
    papers.insert(0, paper)
    _kv_set("friday", "papers", papers[:60])
    return {"paper": paper}


@app.get("/api/specialist/friday/blogs")
async def friday_blogs_get():
    return {"blogs": _kv_get("friday", "blogs", [])}


@app.post("/api/specialist/friday/blogs")
async def friday_blogs_save(body: dict):
    """body: {blogs: [...]} full replace, or {action:'generate', title, notes}"""
    import time
    if body.get("action") == "generate":
        from agents.friday_agent import generate_blog_draft
        title   = body.get("title", "Untitled")
        notes   = body.get("notes", "")
        content = await generate_blog_draft(title, notes)
        blog = {
            "id":      int(time.time()),
            "title":   title,
            "notes":   notes,
            "content": content,
            "status":  "draft",
            "words":   len(content.split()),
            "created": datetime.utcnow().isoformat()[:10],
        }
        blogs = _kv_get("friday", "blogs", [])
        blogs.insert(0, blog)
        _kv_set("friday", "blogs", blogs)
        return {"blog": blog}

    blogs = body.get("blogs", [])
    _kv_set("friday", "blogs", blogs)
    return {"blogs": blogs}


@app.get("/api/specialist/friday/blogs/{blog_id}")
async def friday_blog_by_id(blog_id: int):
    """Fetch a single blog post by its integer ID."""
    blogs = _kv_get("friday", "blogs", [])
    blog  = next((b for b in blogs if b.get("id") == blog_id), None)
    return {"blog": blog} if blog else {"error": "not found"}


@app.get("/api/specialist/gresz/data")
async def gresz_data():
    """Return all Gresz business data in one call."""
    projects = _kv_get("gresz", "projects", [])
    clients  = _kv_get("gresz", "clients",  [])
    pipeline = _kv_get("gresz", "pipeline", [])
    pipe_val = sum(
        float(str(d.get("value","0")).replace("$","").replace(",","").split()[0] or 0)
        for d in pipeline if d.get("value")
    )
    kpis = {
        "active_projects": len([p for p in projects if p.get("status") == "active"]),
        "total_clients":   len([c for c in clients  if c.get("tier") not in ("PROSPECT", "")]),
        "pipeline_value":  f"${pipe_val:,.0f}",
        "overdue":         len([p for p in projects if p.get("overdue")]),
    }
    return {"projects": projects, "clients": clients, "pipeline": pipeline, "kpis": kpis}


@app.post("/api/specialist/gresz/save")
async def gresz_save(body: dict):
    """body: {collection: 'projects'|'clients'|'pipeline', data: [...]}"""
    col  = body.get("collection")
    data = body.get("data", [])
    if col not in ("projects", "clients", "pipeline"):
        return {"error": "invalid collection"}
    _kv_set("gresz", col, data)
    return {"saved": col, "count": len(data)}


@app.post("/api/specialist/gresz/briefing")
async def gresz_briefing():
    from agents.gresz_agent import _ask_claude
    projects = _kv_get("gresz", "projects", [])
    pipeline = _kv_get("gresz", "pipeline", [])
    active   = [p for p in projects if p.get("status") == "active"]
    closing  = [d for d in pipeline  if d.get("stage") == "closing"]
    pipe_v   = sum(float(str(d.get("value","0")).replace("$","").replace(",","").split()[0] or 0) for d in pipeline)
    overdue  = len([p for p in projects if p.get("overdue")])
    prompt = (
        f"You are GRESZ, an AI business intelligence agent for GreszTech. "
        f"Today is {datetime.now().strftime('%A, %d %B %Y')}. "
        f"Write a concise executive briefing (3–4 sentences):\n"
        f"- {len(active)} active projects, {overdue} overdue\n"
        f"- Pipeline: ${pipe_v:,.0f}, {len(closing)} deals closing\n"
        f"Active: {', '.join(p['name'] for p in active[:5]) or 'none'}\n"
        f"Be direct and actionable."
    )
    text = await _ask_claude(prompt, 300)
    return {"briefing": text}


@app.get("/api/specialist/ultron/scan")
async def ultron_scan(target: str = ""):
    if not target:
        return {"error": "target required"}
    from agents.ultron_agent import scan_target
    result = await asyncio.get_event_loop().run_in_executor(None, scan_target, target)
    # Persist threats to Ultron's log (creates DB if not yet initialised)
    if not result.get("safe") and not result.get("error"):
        db = _db("ultron")
        db.execute(
            "INSERT INTO logs (title, detail, severity, category) VALUES (?,?,?,?)",
            (f"Scan alert: {target}", "\n".join(result.get("threats", [])), "alert", "scan")
        )
        db.commit()
        db.close()
    return result


@app.get("/api/specialist/ultron/breach")
async def ultron_breach(email: str = ""):
    if not email or "@" not in email:
        return {"error": "valid email required"}
    from agents.ultron_agent import check_email_breach
    from core.config import env
    key = env("HIBP_API_KEY", "")
    return await asyncio.get_event_loop().run_in_executor(
        None, check_email_breach, email, key
    )


@app.get("/api/specialist/ultron/watchlist")
async def ultron_watchlist_get():
    return {"watchlist": _kv_get("ultron", "watchlist", [])}


@app.post("/api/specialist/ultron/watchlist")
async def ultron_watchlist_update(body: dict):
    """body: {action: 'add'|'remove', target: str}"""
    action = body.get("action", "add")
    target = body.get("target", "").strip()
    if not target:
        return {"error": "target required"}
    wl = _kv_get("ultron", "watchlist", [])
    if action == "add" and target not in wl:
        wl.append(target)
    elif action == "remove":
        wl = [t for t in wl if t != target]
    _kv_set("ultron", "watchlist", wl)
    return {"watchlist": wl}


def start_web():
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8765,
        log_level="warning",
        # Single-process, asyncio loop — avoids multiprocessing semaphore leaks
        # on macOS arm64 + Python 3.9 + ctranslate2.
        workers=1,
        loop="asyncio",
        timeout_keep_alive=5,
    )


