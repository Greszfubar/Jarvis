"""TaskAgent — manages todos via macOS Reminders + internal task list."""
import asyncio
import logging
import subprocess
from datetime import datetime

from agents.base import BaseAgent
from core.memory import Memory

log = logging.getLogger("jarvis.tasks")
mem = Memory()


class TaskAgent(BaseAgent):
    name = "tasks"

    def tools(self):
        return [
            self._tool("get_tasks", "Get all pending tasks and reminders.", {
                "list_name": {"type": "string", "description": "Reminders list name (default: Reminders)"},
            }),
            self._tool("add_task", "Add a new task/reminder.", {
                "title":    {"type": "string"},
                "due_date": {"type": "string", "description": "ISO date e.g. 2026-04-26"},
                "notes":    {"type": "string"},
                "list_name":{"type": "string"},
            }, required=["title"]),
            self._tool("complete_task", "Mark a task as complete.", {
                "title": {"type": "string"},
            }, required=["title"]),
            self._tool("get_priorities", "Get high-priority tasks for today.", {}),
        ]

    async def execute(self, method: str, params: dict):
        if method == "get_tasks":
            return await asyncio.to_thread(self._get_tasks, params.get("list_name", "Reminders"))
        if method == "add_task":
            return await asyncio.to_thread(self._add_task, params)
        if method == "complete_task":
            return await asyncio.to_thread(self._complete_task, params["title"])
        if method == "get_priorities":
            return await asyncio.to_thread(self._get_tasks, "Reminders")
        return {"error": f"Unknown method: {method}"}

    def _get_tasks(self, list_name: str) -> dict:
        script = f"""
        tell application "Reminders"
            set output to ""
            set theList to list "{list_name}"
            set incompleteTasks to (reminders in theList whose completed is false)
            repeat with t in incompleteTasks
                set output to output & (name of t) & "|"
                try
                    set output to output & (due date of t as string)
                end try
                set output to output & "||"
            end repeat
            return output
        end tell
        """
        try:
            r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
            tasks = []
            for chunk in r.stdout.strip().split("||"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                parts = chunk.split("|")
                tasks.append({"title": parts[0], "due": parts[1] if len(parts) > 1 else ""})
            mem.set_fact("tasks_pending", tasks)
            return {"tasks": tasks, "count": len(tasks)}
        except Exception as e:
            return {"error": str(e)}

    def _add_task(self, params: dict) -> dict:
        title = params["title"]
        list_name = params.get("list_name", "Reminders")
        due = params.get("due_date", "")
        notes = params.get("notes", "")
        due_clause = f'set due date of newReminder to date "{due}"' if due else ""
        notes_clause = f'set body of newReminder to "{notes}"' if notes else ""
        script = f"""
        tell application "Reminders"
            set theList to list "{list_name}"
            set newReminder to make new reminder at end of theList with properties {{name:"{title}"}}
            {due_clause}
            {notes_clause}
        end tell
        return "created"
        """
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
            return {"status": "created", "title": title}
        except Exception as e:
            return {"error": str(e)}

    def _complete_task(self, title: str) -> dict:
        script = f"""
        tell application "Reminders"
            repeat with aList in every list
                set matchingReminders to (reminders in aList whose name is "{title}")
                repeat with r in matchingReminders
                    set completed of r to true
                end repeat
            end repeat
        end tell
        return "completed"
        """
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
            return {"status": "completed", "title": title}
        except Exception as e:
            return {"error": str(e)}

    async def tick(self):
        result = await asyncio.to_thread(self._get_tasks, "Reminders")
        tasks = result.get("tasks", [])
        overdue = [t for t in tasks if t.get("due") and t["due"] < datetime.now().isoformat()]
        if overdue:
            from core.bus import bus
            await bus.publish("tasks.overdue", {"tasks": overdue})
