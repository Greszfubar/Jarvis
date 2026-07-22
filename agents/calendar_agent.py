"""CalendarAgent — reads/writes macOS Calendar + Google Calendar."""
import asyncio
import logging
import subprocess
from datetime import datetime, timedelta

from agents.base import BaseAgent
from core.memory import Memory

log = logging.getLogger("jarvis.calendar")
mem = Memory()


class CalendarAgent(BaseAgent):
    name = "calendar"

    def tools(self):
        return [
            self._tool("get_events", "Get upcoming calendar events.", {
                "hours_ahead": {"type": "integer", "description": "Hours to look ahead (default 24)"},
            }),
            self._tool("add_event", "Add a new calendar event.", {
                "title":    {"type": "string"},
                "start":    {"type": "string", "description": "ISO datetime e.g. 2026-04-25T14:00:00"},
                "end":      {"type": "string", "description": "ISO datetime"},
                "calendar": {"type": "string", "description": "Calendar name (default: Home)"},
                "notes":    {"type": "string"},
            }, required=["title", "start", "end"]),
            self._tool("delete_event", "Delete a calendar event by title.", {
                "title": {"type": "string"},
            }, required=["title"]),
        ]

    async def execute(self, method: str, params: dict):
        if method == "get_events":
            return await asyncio.to_thread(self._get_events, params.get("hours_ahead", 24))
        if method == "add_event":
            return await asyncio.to_thread(self._add_event, params)
        if method == "delete_event":
            return await asyncio.to_thread(self._delete_event, params["title"])
        return {"error": f"Unknown method: {method}"}

    def _get_events(self, hours_ahead: int) -> dict:
        now = datetime.now()
        end = now + timedelta(hours=hours_ahead)
        script = f"""
        set output to ""
        set startDate to current date
        set endDate to startDate + {hours_ahead * 3600} * seconds
        tell application "Calendar"
            set allCals to every calendar
            repeat with aCal in allCals
                set evts to (every event of aCal whose start date >= startDate and start date <= endDate)
                repeat with e in evts
                    set output to output & (summary of e) & "|" & (start date of e as string) & "|" & (end date of e as string) & "||"
                end repeat
            end repeat
        end tell
        return output
        """
        try:
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
            raw = result.stdout.strip()
            events = []
            for chunk in raw.split("||"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                parts = chunk.split("|")
                if len(parts) >= 2:
                    events.append({"title": parts[0], "start": parts[1], "end": parts[2] if len(parts) > 2 else ""})
            mem.set_fact("calendar_upcoming", events)
            return {"events": events, "count": len(events)}
        except Exception as e:
            log.error(f"Calendar read error: {e}")
            return {"error": str(e)}

    def _add_event(self, params: dict) -> dict:
        title = params["title"]
        start = params["start"]
        end = params["end"]
        cal_name = params.get("calendar", "Home")
        notes = params.get("notes", "")
        script = f"""
        tell application "Calendar"
            tell calendar "{cal_name}"
                set startD to date "{start}"
                set endD to date "{end}"
                make new event with properties {{summary:"{title}", start date:startD, end date:endD, description:"{notes}"}}
            end tell
        end tell
        return "created"
        """
        try:
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return {"status": "created", "title": title, "start": start}
            return {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}

    def _delete_event(self, title: str) -> dict:
        script = f"""
        tell application "Calendar"
            set allCals to every calendar
            repeat with aCal in allCals
                set evts to (every event of aCal whose summary is "{title}")
                repeat with e in evts
                    delete e
                end repeat
            end repeat
        end tell
        return "deleted"
        """
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
            return {"status": "deleted", "title": title}
        except Exception as e:
            return {"error": str(e)}

    async def tick(self):
        """Check for imminent events and publish alerts."""
        result = await asyncio.to_thread(self._get_events, 2)
        events = result.get("events", [])
        if events:
            from core.bus import bus
            await bus.publish("calendar.upcoming", {"events": events})
