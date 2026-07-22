"""
VISION — Intelligence & Planning specialist agent (Layer 2).

Capabilities (Phase 2):
  - Pull and categorise Apple Calendar events (delegates to CalendarAgent)
  - Strategic plan management stored in SQLite KV
  - Produce daily + weekly briefings for the Vision UI
  - Upcoming-event awareness: flags events in the next 24 h
"""
import asyncio
import json
import logging
import subprocess
from datetime import datetime, timedelta

from agents.base_specialist import BaseSpecialist, SEVERITY_INFO, SEVERITY_WATCH

log = logging.getLogger("jarvis.vision")


# ── Calendar helpers (no dependency on CalendarAgent instance) ─────────────────

def _osascript(script: str, timeout: int = 10) -> str:
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception as e:
        log.error(f"osascript error: {e}")
        return ""


def get_events(hours_ahead: int = 168) -> list[dict]:
    """Fetch calendar events for the next N hours (default 7 days)."""
    script = f"""
    set output to ""
    set startDate to current date
    set endDate to startDate + {hours_ahead * 3600} * seconds
    tell application "Calendar"
        set allCals to every calendar
        repeat with aCal in allCals
            set calName to name of aCal
            set evts to (every event of aCal whose start date >= startDate and start date <= endDate)
            repeat with e in evts
                set output to output & (summary of e) & "|" & (start date of e as string) & "|" & (end date of e as string) & "|" & calName & "||"
            end repeat
        end repeat
    end tell
    return output
    """
    raw = _osascript(script)
    events = []
    for chunk in raw.split("||"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split("|")
        if len(parts) >= 2:
            # Parse macOS date string  e.g. "Sunday, 27 April 2026 at 14:00:00"
            start_raw = parts[1].strip()
            end_raw   = parts[2].strip() if len(parts) > 2 else ""
            cal_name  = parts[3].strip() if len(parts) > 3 else ""
            start_dt  = _parse_mac_date(start_raw)
            end_dt    = _parse_mac_date(end_raw)
            events.append({
                "title":    parts[0].strip(),
                "start":    start_raw,
                "end":      end_raw,
                "calendar": cal_name,
                "date":     start_dt.strftime("%-d %B %Y") if start_dt else start_raw[:10],
                "time":     start_dt.strftime("%H:%M") if start_dt else "",
                "end_time": end_dt.strftime("%H:%M") if end_dt else "",
                "type":     _classify_event(parts[0].strip(), cal_name),
                "_dt":      start_dt.isoformat() if start_dt else "",
            })
    # Sort by start time
    events.sort(key=lambda e: e["_dt"] or "")
    for e in events:
        e.pop("_dt", None)
    return events


def _parse_mac_date(s: str):
    """Try to parse macOS date strings into datetime objects."""
    fmts = [
        "%A, %d %B %Y at %H:%M:%S",
        "%A, %d %B %Y at %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
    ]
    s = s.strip()
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def _classify_event(title: str, calendar: str) -> str:
    t = (title + " " + calendar).lower()
    if any(k in t for k in ["meet", "call", "zoom", "teams", "standup", "sync", "interview"]):
        return "meeting"
    if any(k in t for k in ["deadline", "due", "submit", "launch", "ship", "release"]):
        return "deadline"
    if any(k in t for k in ["gym", "run", "doctor", "dentist", "haircut", "personal", "birthday", "family"]):
        return "personal"
    return "work"


def get_today_events() -> list[dict]:
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    hours = int((midnight - now).total_seconds() / 3600) + 1
    return [e for e in get_events(hours_ahead=max(hours, 2))]


# ── Plan store (SQLite KV) ─────────────────────────────────────────────────────

def _plans_key() -> str:
    return "plans"


class VisionAgent(BaseSpecialist):
    name = "vision"

    async def tick(self):
        self._mark_run()
        events = await asyncio.get_event_loop().run_in_executor(None, get_events, 24)
        # Flag events in the next 2 hours
        now = datetime.now()
        for e in events:
            if not e.get("time"):
                continue
            try:
                evt_dt = _parse_mac_date(e["start"])
                if evt_dt and timedelta(0) <= (evt_dt - now) <= timedelta(hours=2):
                    existing = self._db.execute(
                        "SELECT id FROM logs WHERE title=? AND status='open'",
                        (f"Upcoming: {e['title']}",)
                    ).fetchone()
                    if not existing:
                        self.add_log(
                            title=f"Upcoming: {e['title']}",
                            detail=f"{e['time']} — {e.get('calendar','')}",
                            severity=SEVERITY_WATCH,
                            category="calendar",
                        )
            except Exception:
                pass

    async def execute(self, method: str, params: dict) -> dict:
        if method == "events":
            hours = int(params.get("hours", 168))
            events = await asyncio.get_event_loop().run_in_executor(
                None, get_events, hours
            )
            return {"events": events}

        if method == "today":
            events = await asyncio.get_event_loop().run_in_executor(
                None, get_today_events
            )
            return {"events": events}

        if method == "plans_get":
            return {"plans": self.get_state(_plans_key(), [])}

        if method == "plans_add":
            title = params.get("title", "Untitled")
            phase = params.get("phase", "PLANNING")
            due   = params.get("due", "TBD")
            plans = self.get_state(_plans_key(), [])
            plan  = {"id": len(plans), "title": title, "phase": phase, "due": due, "notes": ""}
            plans.insert(0, plan)
            self.set_state(_plans_key(), plans)
            self.add_log(title=f"New plan: {title}", severity=SEVERITY_INFO, category="planning")
            # Broadcast so Vision UI picks up the change on next poll
            try:
                from core.bus import bus
                bus.publish_sync("vision.plans_updated", {"plans": plans})
            except Exception:
                pass
            return {"plan": plan, "plans": plans}

        if method == "plans_update":
            plan_id = params.get("id")
            plans   = self.get_state(_plans_key(), [])
            for p in plans:
                if p["id"] == plan_id:
                    p.update({k: v for k, v in params.items() if k != "id"})
            self.set_state(_plans_key(), plans)
            return {"plans": plans}

        if method == "plans_delete":
            plan_id = params.get("id")
            plans   = [p for p in self.get_state(_plans_key(), []) if p["id"] != plan_id]
            self.set_state(_plans_key(), plans)
            return {"plans": plans}

        if method == "command":
            text  = params.get("text", "")
            lower = text.lower().strip()

            # ── Today's schedule ──────────────────────────────────────────────
            if any(k in lower for k in ("today", "this morning", "this afternoon", "my day", "schedule")):
                result = await self.execute("today", {})
                events = result.get("events", [])
                if not events:
                    return {"message": "Your calendar is clear today."}
                lines = [f"• {e.get('time','')} — {e['title']}" for e in events[:5]]
                return {"message": f"You have {len(events)} event{'s' if len(events)!=1 else ''} today: " + "; ".join(e['title'] for e in events[:3])}

            # ── This week / upcoming ──────────────────────────────────────────
            if any(k in lower for k in ("week", "upcoming", "next", "soon", "coming up", "calendar")):
                hrs = 72 if "tomorrow" in lower else 168
                result = await self.execute("events", {"hours": hrs})
                events = result.get("events", [])
                if not events:
                    return {"message": "Nothing on the calendar for the next week."}
                lines = [f"• {e.get('date','')} {e.get('time','')} — {e['title']}" for e in events[:5]]
                return {"message": f"{len(events)} upcoming event{'s' if len(events)!=1 else ''}: " + "; ".join(e['title'] for e in events[:3])}

            # ── Next event ────────────────────────────────────────────────────
            if any(k in lower for k in ("next event", "next meeting", "what's next", "whats next")):
                result = await self.execute("events", {"hours": 168})
                events = result.get("events", [])
                if not events:
                    return {"message": "Nothing coming up on the calendar."}
                e = events[0]
                return {"message": f"Your next event is {e['title']} on {e.get('date','')} at {e.get('time','')}."}

            # ── Plans — save ─────────────────────────────────────────────────
            # "save a plan", "add a plan called X", "create plan: study for exams"
            # "record my study plan", "my plan is X"
            _save_kws = ("save", "add", "create", "record", "store", "note", "remember", "set")
            if any(k in lower for k in _save_kws) and any(k in lower for k in ("plan", "goal", "roadmap", "strategy", "objective")):
                import re as _re
                # Two-step extraction:
                # Step 1: strip leading "hey Vision, save [a/my/the]"
                # Step 2: if result starts with a bare plan-type word + connector, strip that too
                t = _re.sub(
                    r"(?i)^(?:hey\s+vision\s*,?\s*)?"
                    r"(?:save|add|create|record|store|note|remember|set)\s+"
                    r"(?:a\s+|my\s+|the\s+)?",
                    "", text, count=1
                ).strip()
                # Now t might be "study plan before exams" or "plan to learn Python"
                # or "strategic plan for Q3" or "goal: finish X"
                # Strip a BARE plan-type word only when it's followed by
                # a connector (to/for/:) or stands alone — but keep it when
                # preceded by a modifier (e.g. "study plan" or "Q3 plan")
                bare_m = _re.match(
                    r"(?i)^(?:strategic\s+)?(?:plan|goal|roadmap|strategy|objective)"
                    r"\s*(?:to\s+|for\s+|:\s*|called\s+|named\s+|titled\s+)(.+)$",
                    t
                )
                title = bare_m.group(1).strip(" ,.!?") if bare_m else t.strip(" ,.!?")
                if not title:
                    title = text.strip()
                result = await self.execute("plans_add", {"title": title or "New Plan", "phase": "PLANNING", "due": "TBD"})
                plan   = result.get("plan", {})
                return {"message": f"Got it. I've saved '{plan.get('title', title)}' to your strategic plans."}

            # ── Plans — view ─────────────────────────────────────────────────
            if any(k in lower for k in ("plan", "goals", "roadmap", "strategy", "objective")):
                result = await self.execute("plans_get", {})
                plans  = result.get("plans", [])
                if not plans:
                    return {"message": "No strategic plans saved yet. Say 'save a plan called X' to add one."}
                lines = [f"{p.get('title','Untitled')} — {p.get('phase','')}" for p in plans[:4]]
                return {"message": f"You have {len(plans)} plan{'s' if len(plans)!=1 else ''}: " + "; ".join(lines)}

            # ── Upcoming events ───────────────────────────────────────────────
            if any(k in lower for k in ("event", "meeting", "appointment")):
                result = await self.execute("events", {"hours": 48})
                events = result.get("events", [])
                if not events:
                    return {"message": "No events in the next 48 hours."}
                return {"message": f"{len(events)} event{'s' if len(events)!=1 else ''} in the next 48 hours. Next: {events[0]['title']} at {events[0].get('time','')}."}

            return {"message": "Ask me about your calendar today, this week, upcoming events, or your strategic plans."}

        return {"error": f"Unknown method: {method}"}
