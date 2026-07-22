"""
TaskBoardAgent — JARVIS's proactive to-do brain.

Stores tasks in SQLite with priority / status / owner.
Heartbeat runs every 5 minutes:
  - Surfaces overdue tasks
  - Auto-completes tasks JARVIS can do autonomously (web lookups, drafts, etc.)
  - Pushes alerts via bus when urgent items need attention
"""
import asyncio
import json
import logging
import sqlite3
import subprocess
import threading
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List

from agents.base import BaseAgent
from core.config import env
from core.memory import Memory

log = logging.getLogger("jarvis.taskboard")
mem = Memory()

DB_PATH = Path("data/taskboard.db")
CLAUDE_CMD = "claude"


def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority    TEXT DEFAULT 'medium',   -- low | medium | high | urgent
            status      TEXT DEFAULT 'todo',     -- todo | in_progress | done | blocked
            category    TEXT DEFAULT 'general',
            due_date    TEXT DEFAULT '',
            assignee    TEXT DEFAULT 'jarvis',   -- jarvis | human
            result      TEXT DEFAULT '',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_status   ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
    """)
    conn.commit()
    return conn


_conn_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None


def get_conn():
    global _conn
    if _conn is None:
        _conn = _db()
    return _conn


class TaskBoardAgent(BaseAgent):
    name = "taskboard"

    def tools(self):
        return [
            self._tool("add_task", "Add a task to JARVIS's task board.", {
                "title":       {"type": "string"},
                "description": {"type": "string"},
                "priority":    {"type": "string", "description": "low | medium | high | urgent"},
                "category":    {"type": "string"},
                "due_date":    {"type": "string", "description": "YYYY-MM-DD or empty"},
                "assignee":    {"type": "string", "description": "jarvis (auto) | human (needs you)"},
            }, required=["title"]),
            self._tool("get_tasks", "Get tasks from the board.", {
                "status":   {"type": "string", "description": "todo | in_progress | done | all"},
                "priority": {"type": "string", "description": "Filter by priority"},
            }),
            self._tool("complete_task", "Mark a task as done.", {
                "task_id": {"type": "integer"},
                "result":  {"type": "string", "description": "What was done"},
            }, required=["task_id"]),
            self._tool("update_task", "Update a task's status or priority.", {
                "task_id":  {"type": "integer"},
                "status":   {"type": "string"},
                "priority": {"type": "string"},
                "result":   {"type": "string"},
            }, required=["task_id"]),
            self._tool("get_board_summary", "Get a quick summary of the task board.", {}),
        ]

    async def execute(self, method: str, params: dict):
        if method == "add_task":       return await asyncio.to_thread(self._add, params)
        if method == "get_tasks":      return await asyncio.to_thread(self._get, params)
        if method == "complete_task":  return await asyncio.to_thread(self._complete, params)
        if method == "update_task":    return await asyncio.to_thread(self._update, params)
        if method == "get_board_summary": return await asyncio.to_thread(self._summary)
        return {"error": f"Unknown: {method}"}

    # ── DB ops ─────────────────────────────────────────────────────────────────

    def _add(self, p: dict) -> dict:
        now = datetime.utcnow().isoformat()
        with _conn_lock:
            c = get_conn()
            cur = c.execute(
                "INSERT INTO tasks(title,description,priority,status,category,due_date,assignee,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (p["title"], p.get("description",""), p.get("priority","medium"),
                 "todo", p.get("category","general"), p.get("due_date",""),
                 p.get("assignee","jarvis"), now, now)
            )
            c.commit()
            task_id = cur.lastrowid
        log.info(f"Task added: [{task_id}] {p['title']}")
        return {"status": "added", "task_id": task_id, "title": p["title"]}

    def _get(self, p: dict) -> dict:
        status = p.get("status", "todo")
        with _conn_lock:
            c = get_conn()
            if status == "all":
                rows = c.execute("SELECT * FROM tasks ORDER BY priority DESC, created_at DESC").fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM tasks WHERE status=? ORDER BY priority DESC, created_at DESC",
                    (status,)
                ).fetchall()
        tasks = [dict(r) for r in rows]
        if p.get("priority"):
            tasks = [t for t in tasks if t["priority"] == p["priority"]]
        return {"tasks": tasks, "count": len(tasks)}

    def _complete(self, p: dict) -> dict:
        now = datetime.utcnow().isoformat()
        with _conn_lock:
            c = get_conn()
            c.execute(
                "UPDATE tasks SET status='done', result=?, updated_at=? WHERE id=?",
                (p.get("result",""), now, p["task_id"])
            )
            c.commit()
        return {"status": "done", "task_id": p["task_id"]}

    def _update(self, p: dict) -> dict:
        now = datetime.utcnow().isoformat()
        with _conn_lock:
            c = get_conn()
            fields, vals = [], []
            for col in ("status", "priority", "result"):
                if col in p:
                    fields.append(f"{col}=?"); vals.append(p[col])
            fields.append("updated_at=?"); vals.append(now)
            vals.append(p["task_id"])
            c.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id=?", vals)
            c.commit()
        return {"status": "updated", "task_id": p["task_id"]}

    def _summary(self) -> dict:
        with _conn_lock:
            c = get_conn()
            counts = {r["status"]: r["cnt"] for r in
                      c.execute("SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status").fetchall()}
            urgent = [dict(r) for r in
                      c.execute("SELECT * FROM tasks WHERE priority='urgent' AND status!='done' LIMIT 5").fetchall()]
            overdue = [dict(r) for r in
                       c.execute("SELECT * FROM tasks WHERE due_date!='' AND due_date<? AND status!='done'",
                                 (date.today().isoformat(),)).fetchall()]
        return {
            "counts": counts,
            "urgent": urgent,
            "overdue": overdue,
            "total_open": counts.get("todo", 0) + counts.get("in_progress", 0),
        }

    # ── Heartbeat ──────────────────────────────────────────────────────────────

    async def tick(self):
        summary = await asyncio.to_thread(self._summary)

        # Alert on urgent or overdue
        if summary["overdue"]:
            titles = ", ".join(t["title"] for t in summary["overdue"][:3])
            from core.bus import bus
            await bus.publish("jarvis.alert", {
                "source": "taskboard",
                "message": f"Overdue tasks: {titles}",
            })

        # Auto-work jarvis-assigned todo tasks
        jarvis_tasks = await asyncio.to_thread(self._get_jarvis_todos)
        for task in jarvis_tasks[:2]:   # max 2 autonomous tasks per tick
            await self._auto_work(task)

    def _get_jarvis_todos(self) -> list:
        with _conn_lock:
            c = get_conn()
            rows = c.execute(
                "SELECT * FROM tasks WHERE assignee='jarvis' AND status='todo' "
                "ORDER BY priority DESC LIMIT 3"
            ).fetchall()
        return [dict(r) for r in rows]

    async def _auto_work(self, task: dict):
        """Let Claude attempt to complete a jarvis-assigned task autonomously."""
        log.info(f"Auto-working task [{task['id']}]: {task['title']}")
        system = (
            "You are JARVIS completing an autonomous task. "
            "Be concise. Output the result directly — no preamble."
        )
        prompt = (
            f"Complete this task: {task['title']}\n"
            f"Details: {task['description']}\n"
            "Provide the result or output."
        )
        import os
        clean_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        try:
            result_proc = await asyncio.to_thread(
                subprocess.run,
                [CLAUDE_CMD, "-p", prompt, "--system-prompt", system, "--output-format", "text"],
                capture_output=True, text=True, timeout=60, env=clean_env,
            )
            result_text = result_proc.stdout.strip()
            if result_text:
                await asyncio.to_thread(self._complete, {"task_id": task["id"], "result": result_text})
                log.info(f"Auto-completed task [{task['id']}]")
                from core.bus import bus
                await bus.publish("taskboard.completed", {
                    "task_id": task["id"],
                    "title": task["title"],
                    "result": result_text[:200],
                })
        except Exception as e:
            log.error(f"Auto-work failed for task {task['id']}: {e}")


# ── HTTP endpoints (imported by web.py) ───────────────────────────────────────

def get_all_tasks_json() -> list:
    try:
        with _conn_lock:
            c = get_conn()
            rows = c.execute("SELECT * FROM tasks ORDER BY priority DESC, created_at DESC").fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
