"""
JARVIS — Personal AI Operating System
# ── Thread-count caps — must be set BEFORE any ML/numeric library is imported.
# ctranslate2 4.x on Apple Silicon (arm64) sends SIGTERM to itself during
# OpenMP thread-pool init when semaphore limits are exceeded under Python 3.9.
import os as _os
_os.environ.setdefault("OMP_NUM_THREADS",        "1")
_os.environ.setdefault("OPENBLAS_NUM_THREADS",   "1")
_os.environ.setdefault("MKL_NUM_THREADS",        "1")
_os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")   # macOS Accelerate
_os.environ.setdefault("NUMEXPR_NUM_THREADS",    "1")
Entry point: starts web server + browser listener in STANDBY, then fully
initialises only after the launch trigger (double-clap + "wake up jarvis").

macOS threading model:
  - Main thread  → pywebview (WKWebView / NSWindow requirement)
  - Bg thread    → asyncio event loop (web server, voice, agents)

Startup sequence:
  1. main thread calls open_window(_run_async)
  2. pywebview creates window, calls _boot() in a thread
  3. _boot() starts uvicorn + async loop, waits for server ready, loads URL
  4. Async loop sits in STANDBY — web server + browser listener only
  5. User does double-clap + "wake up jarvis"
  6. _full_init() fires: agents, scheduler, Telegram, greeting
"""
import asyncio
import logging
import sys
import threading
from pathlib import Path

# ── Logging ───────────────────────────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/jarvis.log"),
    ],
)
log = logging.getLogger("jarvis")

# ── Bootstrap ─────────────────────────────────────────────────────────────────
from core.config import cfg, env

import shutil
if not shutil.which("claude"):
    log.error("'claude' CLI not found on PATH. Install Claude Code: https://claude.ai/code")
    sys.exit(1)

from core.orchestrator import orchestrator
from core.scheduler import get_scheduler, start as start_scheduler
from core.bus import bus
from voice.speaker import speak, start as start_speaker

from agents.weather        import WeatherAgent
from agents.news           import NewsAgent
from agents.calendar_agent import CalendarAgent
from agents.gmail_agent    import GmailAgent
from agents.desktop        import DesktopAgent
from agents.tasks          import TaskAgent
from agents.briefing       import BriefingAgent
from agents.consolidation  import ConsolidationAgent
from agents.taskboard      import TaskBoardAgent
from agents.ultron_agent   import UltronAgent
from agents.vision_agent   import VisionAgent
from agents.friday_agent   import FridayAgent
from agents.gresz_agent    import GreszAgent

# Shared state
_loop: asyncio.AbstractEventLoop = None
_initialised:    bool                      = False   # True after _full_init runs


# ── Agent registration ────────────────────────────────────────────────────────

def register_agents():
    agents = [
        WeatherAgent(), NewsAgent(), CalendarAgent(),
        GmailAgent(), DesktopAgent(), TaskAgent(), BriefingAgent(),
        ConsolidationAgent(), TaskBoardAgent(),
        UltronAgent(), VisionAgent(), FridayAgent(), GreszAgent(),
    ]
    for a in agents:
        orchestrator.register_agent(a)
    return agents


def schedule_agents(agents):
    sched = get_scheduler()
    intervals = {
        "weather":       cfg["agents"]["weather"]["refresh_interval_min"],
        "news":          cfg["agents"]["news"]["refresh_interval_min"],
        "calendar":      cfg["agents"]["calendar"]["refresh_interval_min"],
        "gmail":         cfg["agents"]["gmail"]["refresh_interval_min"],
        "tasks":         cfg["agents"]["tasks"]["refresh_interval_min"],
        "briefing":      1,
        "consolidation": 5,
        "taskboard":     5,
        "ultron":        30,   # watchlist scan every 30 min
        "vision":        15,   # upcoming event awareness every 15 min
        "friday":        30,   # news cache refresh every 30 min
        "gresz":         60,   # overdue project checks every hour
    }
    for agent in agents:
        interval = intervals.get(agent.name, 60)
        sched.add_job(agent.tick, trigger="interval", minutes=interval,
                      id=f"tick_{agent.name}", replace_existing=True)
        log.info(f"Scheduled {agent.name} every {interval}m")
    sched.add_job(orchestrator.run_proactive, trigger="interval",
                  minutes=5, id="proactive_sweep")

    # ── Daily newspaper at 11:00 AM ───────────────────────────────────────────
    friday_agent = next((a for a in agents if a.name == "friday"), None)
    if friday_agent:
        sched.add_job(
            lambda: asyncio.run_coroutine_threadsafe(
                friday_agent.auto_daily_newspaper(), _loop
            ),
            trigger="cron", hour=11, minute=0,
            id="daily_newspaper", replace_existing=True,
        )
        log.info("Scheduled daily newspaper at 11:00")

        # ── Daily blog at 08:30 AM ────────────────────────────────────────────
        sched.add_job(
            lambda: asyncio.run_coroutine_threadsafe(
                friday_agent.auto_daily_blog(), _loop
            ),
            trigger="cron", hour=8, minute=30,
            id="daily_blog", replace_existing=True,
        )
        log.info("Scheduled daily blog at 08:30")


# ── Bus handlers ──────────────────────────────────────────────────────────────
# Telegram is NEVER pushed proactively — it only responds to incoming messages
# or an explicit "send me a Telegram saying X" voice/text command.

async def handle_alert(payload):
    msg = payload.get("message", str(payload))
    speak(msg)

async def handle_briefing(payload):
    data = payload.get("data", {})
    summary = await orchestrator.process(
        f"Deliver my morning briefing from this data: {data}. "
        "Cover weather, calendar, email, and top news. Be concise."
    )
    speak(summary)

async def handle_gmail_new(payload):
    n   = payload.get("new_count", 0)
    msg = f"You have {n} new email{'s' if n != 1 else ''}."
    speak(msg)

async def handle_task_completed(payload):
    title = payload.get("title", "task")
    speak(f"Task complete: {title}")

def _safe_dispatch(coro_fn, payload):
    """Schedule a coroutine on _loop, guarding against loop-not-ready."""
    if _loop is None or _loop.is_closed():
        log.warning(f"Bus event dropped — event loop not ready: {coro_fn.__name__}")
        return
    asyncio.run_coroutine_threadsafe(coro_fn(payload), _loop)

def setup_bus_handlers():
    bus.subscribe("jarvis.alert",        lambda p: _safe_dispatch(handle_alert,          p))
    bus.subscribe("jarvis.briefing",     lambda p: _safe_dispatch(handle_briefing,       p))
    bus.subscribe("gmail.new",           lambda p: _safe_dispatch(handle_gmail_new,      p))
    bus.subscribe("taskboard.completed", lambda p: _safe_dispatch(handle_task_completed, p))


# ── Voice ─────────────────────────────────────────────────────────────────────

def setup_browser_voice():
    """
    Wire callbacks into the browser listener.
    Called after _full_init so orchestrator is ready.
    """
    import random
    from voice.browser_listener import get_listener

    _ACK = ["Yes sir.", "Yes sir, how can I help?",
            "At your service.", "Ready, sir.", "Yes, go ahead."]

    def on_wake():
        """Bare 'Jarvis' — chirp + spoken acknowledgement."""
        from voice.speaker import play_chirp
        play_chirp("wake")
        speak(random.choice(_ACK))

    def on_wake_quiet():
        """'Jarvis + command' bundled — chirp only, no speech (don't interrupt)."""
        from voice.speaker import play_chirp
        play_chirp("wake")

    def on_command(text: str):
        """
        Called synchronously from within _handle_utterance (an async task on
        uvicorn's event loop).  We schedule _dispatch_voice as a new task on
        whatever loop is currently running — no cross-loop scheduling, no _loop
        dependency, no race conditions.
        """
        log.info(f"Voice command received: '{text}'")
        try:
            asyncio.ensure_future(_dispatch_voice(text))
        except Exception as e:
            log.error(f"on_command failed to schedule: {e}", exc_info=True)
            # Make sure _processing is cleared so the next command isn't blocked
            from voice.browser_listener import get_listener as _gl
            _gl()._processing = False

    async def _dispatch_voice(text: str):
        """
        Voice routing — two modes only:

        1. A Layer-2 window is open  → send to that agent directly.
           The user opened Ultron/Vision/Friday/Gresz and is talking to it.
           JARVIS is silent; voice returns to JARVIS when the window closes.

        2. No Layer-2 window open    → send to JARVIS orchestrator.
           JARVIS decides internally which agents to call; the user never
           has to address agents by name.
        """
        from voice.browser_listener import get_listener as _get_listener

        try:
            # ── Which mode are we in? ────────────────────────────────────────
            try:
                from ui.sub_apps import get_active_agent
                active = get_active_agent()
            except Exception as e:
                log.error(f"get_active_agent failed: {e}")
                active = None

            if active:
                # ── Layer-2 agent window is open: speak directly to it ───────
                log.info(f"Layer-2 '{active}' owns voice → '{text}'")
                agent = orchestrator._agents.get(active)
                if not agent:
                    log.warning(f"Agent '{active}' not registered — falling back to JARVIS")
                    active = None  # fall through to JARVIS below
                else:
                    try:
                        result  = await agent.execute("command", {"text": text})
                        message = result.get("message") or result.get("response") or ""
                        if not message:
                            # Agent returned a raw dict — narrate it briefly
                            message = await _narrate(active, text, result)
                        log.info(f"{active} reply: '{message[:80]}'")
                        _get_listener().skip_conversation_window()
                        speak(message)
                    except Exception as e:
                        log.error(f"Agent dispatch error [{active}]: {e}", exc_info=True)
                        _get_listener().skip_conversation_window()
                        speak(f"There was an issue with {active.title()}.")
                    return

            # ── No active window: JARVIS handles everything ──────────────────
            log.info(f"JARVIS orchestrator ← '{text}'")
            try:
                response = await orchestrator.process(text)
            except Exception as e:
                log.error(f"Orchestrator error: {e}", exc_info=True)
                speak("Sorry, I ran into a problem processing that.")
                return
            if response:
                speak(response)
            else:
                log.warning("Orchestrator returned empty response")
                speak("I didn't get a response. Please try again.")

        except Exception as e:
            log.error(f"_dispatch_voice unhandled error: {e}", exc_info=True)
            speak("Something went wrong. Please try again.")
        finally:
            lnr = _get_listener()
            lnr._processing = False
            # If another command arrived while we were processing, run it now
            queued = lnr._queued_command
            if queued:
                lnr._queued_command = ""
                log.info(f"Running queued command: '{queued}'")
                lnr._processing = True
                asyncio.ensure_future(_dispatch_voice(queued))

    async def _narrate(agent_name: str, query: str, result: dict) -> str:
        """Ask JARVIS to turn a raw agent result dict into a spoken sentence."""
        try:
            return await orchestrator.process(
                f"Summarise this {agent_name.upper()} result in one spoken sentence "
                f"for query '{query}': {result}"
            )
        except Exception:
            return f"{agent_name.title()} completed the request."

    listener = get_listener()
    listener.configure(on_wake=on_wake, on_command=on_command, on_wake_quiet=on_wake_quiet)
    log.info("Browser voice listener voice callbacks configured")


# ── Startup briefing ─────────────────────────────────────────────────────────

def _build_startup_briefing() -> str:
    """
    Build a full spoken launch briefing by reading live data from every agent's
    SQLite store.  Covers: greeting, weather, calendar, email, security (Ultron),
    business (Gresz), content (Friday).  Works entirely from cached DB state so
    it's fast and doesn't block on any network calls.
    """
    import json
    import sqlite3
    import datetime
    from pathlib import Path

    user = env("USER_NAME", "Sir")
    hour = datetime.datetime.now().hour
    if hour < 12:
        salutation = "Good morning"
    elif hour < 18:
        salutation = "Good afternoon"
    else:
        salutation = "Good evening"

    parts = [f"{salutation}, {user}. JARVIS is online."]

    # ── Helper: read jarvis.db facts (weather, Gmail) ────────────────────────
    def _fact(key, default=None):
        try:
            db = sqlite3.connect("data/jarvis.db")
            row = db.execute(
                "SELECT value FROM facts WHERE key=?", (key,)
            ).fetchone()
            db.close()
            return json.loads(row[0]) if row else default
        except Exception:
            return default

    # ── Helper: read a specialist KV ─────────────────────────────────────────
    def _kv(name, key, default=None):
        try:
            db_path = Path(f"data/specialists/{name}.db")
            if not db_path.exists():
                return default
            db = sqlite3.connect(str(db_path))
            row = db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
            db.close()
            return json.loads(row[0]) if row else default
        except Exception:
            return default

    # ── Weather ───────────────────────────────────────────────────────────────
    try:
        wx = _fact("weather_current")
        if wx:
            city      = wx.get("city", "")
            temp      = wx.get("temp", "")
            feels     = wx.get("feels_like", "")
            condition = wx.get("condition", "")
            city_str  = f" in {city}" if city else ""
            parts.append(
                f"Weather{city_str}: {condition}, {temp}°, feels like {feels}°."
            )
    except Exception:
        pass

    # ── Calendar — today's events (Vision) ───────────────────────────────────
    try:
        events = _kv("vision", "cached_events", []) or []
        today_str = datetime.date.today().isoformat()
        today_events = [
            e for e in events
            if (e.get("start") or "").startswith(today_str)
               or e.get("today")
        ]
        if today_events:
            count = len(today_events)
            next_e = today_events[0]
            title  = next_e.get("title", "an event")
            start  = (next_e.get("start") or "")
            # Extract HH:MM from ISO string
            time_str = start[11:16] if len(start) >= 16 else ""
            time_part = f" at {time_str}" if time_str else ""
            parts.append(
                f"You have {count} event{'s' if count != 1 else ''} today. "
                f"First up: {title}{time_part}."
            )
        else:
            parts.append("Your calendar is clear today.")
    except Exception:
        pass

    # ── Email ─────────────────────────────────────────────────────────────────
    try:
        unread = _fact("gmail_unread_count")
        if unread is not None and int(unread) > 0:
            parts.append(
                f"{int(unread)} unread email{'s' if int(unread) != 1 else ''} in your inbox."
            )
    except Exception:
        pass

    # ── Tasks ─────────────────────────────────────────────────────────────────
    try:
        tasks = _fact("tasks_pending") or []
        if tasks:
            due_today = [t for t in tasks if (t.get("due") or "").startswith(datetime.date.today().isoformat())]
            overdue_t = [t for t in tasks if t.get("overdue")]
            if due_today:
                parts.append(
                    f"{len(due_today)} task{'s' if len(due_today) != 1 else ''} due today."
                )
            elif overdue_t:
                parts.append(
                    f"{len(overdue_t)} overdue task{'s' if len(overdue_t) != 1 else ''} need your attention."
                )
            elif tasks:
                parts.append(
                    f"{len(tasks)} task{'s' if len(tasks) != 1 else ''} pending."
                )
    except Exception:
        pass

    # ── Security — Ultron ────────────────────────────────────────────────────
    try:
        db_path = Path("data/specialists/ultron.db")
        if db_path.exists():
            db = sqlite3.connect(str(db_path))
            open_threats = db.execute(
                "SELECT COUNT(*) FROM logs WHERE severity='alert' AND status='open'"
            ).fetchone()[0]
            db.close()
            wl = _kv("ultron", "watchlist", []) or []
            if open_threats:
                parts.append(
                    f"Security alert: {open_threats} open threat{'s' if open_threats != 1 else ''} "
                    f"detected. Ultron is monitoring {len(wl)} target{'s' if len(wl) != 1 else ''}."
                )
            elif wl:
                parts.append(
                    f"Security clear. Monitoring {len(wl)} watchlist target{'s' if len(wl) != 1 else ''}."
                )
    except Exception:
        pass

    # ── Business — Gresz ─────────────────────────────────────────────────────
    try:
        projects = _kv("gresz", "projects", []) or []
        pipeline = _kv("gresz", "pipeline", []) or []
        active   = [p for p in projects if p.get("status") == "active"]
        overdue  = [p for p in projects if p.get("overdue")]
        pipe_v   = sum(
            float(str(d.get("value", "0")).replace("$", "").replace(",", "").split()[0] or 0)
            for d in pipeline if d.get("value")
        )
        if active or pipeline:
            biz_parts = []
            if active:
                biz_parts.append(
                    f"{len(active)} active project{'s' if len(active) != 1 else ''}"
                )
            if overdue:
                biz_parts.append(f"{len(overdue)} overdue")
            if pipeline:
                biz_parts.append(
                    f"pipeline at ${pipe_v:,.0f} across {len(pipeline)} deal{'s' if len(pipeline) != 1 else ''}"
                )
            parts.append("Gresz Industries: " + ", ".join(biz_parts) + ".")
    except Exception:
        pass

    # ── Content — Friday ─────────────────────────────────────────────────────
    try:
        papers = _kv("friday", "papers", []) or []
        blogs  = _kv("friday", "blogs",  []) or []
        if papers:
            edition_date = papers[0].get("date", "")
            parts.append(
                f"Today's Gazette is ready — edition {edition_date}. "
                f"{len(blogs)} blog post{'s' if len(blogs) != 1 else ''} in the archive."
            )
        elif blogs:
            parts.append(
                f"Friday: {len(blogs)} blog post{'s' if len(blogs) != 1 else ''} in the archive. No newspaper published yet today."
            )
    except Exception:
        pass

    parts.append("All systems operational. How can I help you?")
    return " ".join(parts)


# ── Full initialisation (triggered by launch phrase) ─────────────────────────

async def _full_init():
    """
    Runs once after the double-clap + 'wake up jarvis' launch trigger.
    Starts all agents, scheduler, Telegram, and speaks the greeting.
    """
    global _initialised
    if _initialised:
        return
    _initialised = True

    log.info("=" * 60)
    log.info("  J.A.R.V.I.S  —  Initialising…")
    log.info("=" * 60)

    agents = register_agents()
    start_scheduler()
    schedule_agents(agents)
    setup_bus_handlers()

    # Wire voice callbacks (model already loaded in standby setup)
    setup_browser_voice()

    # Initial data refresh
    log.info("Running initial data refresh…")
    await asyncio.gather(*[a.tick() for a in agents], return_exceptions=True)

    # Startup greeting — suppress conversation window (don't let ambient noise reply)
    from voice.browser_listener import get_listener
    listener = get_listener()
    listener.skip_conversation_window()
    speak(_build_startup_briefing())
    log.info("Ready.")


def _on_launch_phrase():
    """Called from browser_listener thread when launch trigger detected."""
    asyncio.run_coroutine_threadsafe(_full_init(), _loop)


async def manual_activate():
    """
    Called by /api/standby/activate when user unlocks via password on the standby screen.
    Activates the listener and runs full init, same as the voice trigger.
    """
    from voice.browser_listener import get_listener
    get_listener().activate()
    await _full_init()


# ── Web server ────────────────────────────────────────────────────────────────

def start_web():
    from ui.web import start_web as _start
    _start()


# ── Async engine ─────────────────────────────────────────────────────────────

async def async_main():
    # _loop is already set by _run_async() before this coroutine starts.
    # Call bus.set_loop() now that we're inside the running loop.
    bus.set_loop(_loop)

    log.info("JARVIS — standing by. Waiting for: double-clap + 'wake up jarvis'")

    start_speaker()

    # Web server in its own thread
    threading.Thread(target=start_web, daemon=True, name="web").start()

    # Browser listener starts in STANDBY mode, watching for the launch trigger
    if cfg["voice"]["enabled"]:
        from voice.browser_listener import get_listener
        listener = get_listener()
        listener.set_launch_callback(_on_launch_phrase)
        threading.Thread(
            target=listener.load_model, daemon=True, name="whisper-load"
        ).start()

    while True:
        await asyncio.sleep(60)


def _run_async():
    global _loop
    # Create and register the loop BEFORE asyncio.run() so that any code
    # which reads _loop from another thread (on_command, bus handlers,
    # _on_launch_phrase) sees a valid loop object immediately — not None.
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    try:
        _loop.run_until_complete(async_main())
    except Exception as e:
        log.error(f"Async loop crashed: {e}", exc_info=True)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os, signal, time as _time

    _PID_FILE = Path("jarvis.pid")
    if _PID_FILE.exists():
        try:
            old_pid = int(_PID_FILE.read_text().strip())
            my_pid  = os.getpid()
            if old_pid != my_pid:
                try:
                    os.kill(old_pid, 0)          # check it's actually alive first
                    os.kill(old_pid, signal.SIGTERM)
                    for _ in range(10):
                        _time.sleep(0.5)
                        try:
                            os.kill(old_pid, 0)
                        except ProcessLookupError:
                            break
                    log.info(f"Stopped previous JARVIS instance (pid {old_pid})")
                except ProcessLookupError:
                    pass   # already gone — stale PID file, safe to ignore
        except ValueError:
            pass   # corrupt PID file
    _PID_FILE.write_text(str(os.getpid()))

    import atexit
    atexit.register(lambda: _PID_FILE.unlink(missing_ok=True))

    log.info("Starting JARVIS (standby mode)…")
    from ui.app_window import open_window
    open_window(_run_async)
