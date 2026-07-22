"""
BaseSpecialist — extended base class for Layer 2 agents.

Layer 2 agents (Ultron, Vision, Friday, Gresz) extend this instead of
BaseAgent so they get:
  - Persistent SQLite log store (one DB per agent)
  - Standardised JARVIS→agent command routing
  - Status reporting (for the agent network view)
  - Event broadcasting to the JARVIS UI
"""
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from agents.base import BaseAgent

DATA_DIR = Path("data/specialists")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Log severity levels
SEVERITY_INFO    = "info"     # blue  — informational
SEVERITY_WATCH   = "watch"    # yellow — needs review
SEVERITY_ALERT   = "alert"    # red   — urgent / exposed
SEVERITY_RESOLVED = "resolved" # green  — fixed


class BaseSpecialist(BaseAgent):
    """
    Base class for Layer 2 specialist agents.
    Subclasses must set `name` and implement `tick()` and `execute()`.
    """

    def __init__(self):
        db_path = DATA_DIR / f"{self.name}.db"
        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("""
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
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS kv (
                key   TEXT PRIMARY KEY,
                value TEXT,
                ts    TEXT DEFAULT (datetime('now'))
            )
        """)
        self._db.commit()
        self.log = logging.getLogger(f"jarvis.{self.name}")

    # ── BaseAgent abstract method (specialists use CLI, not Anthropic tool-use) ──

    def tools(self) -> list:
        """Specialist agents drive Claude via CLI — no Anthropic tool definitions needed."""
        return []

    # ── Log helpers ───────────────────────────────────────────────────────────

    def add_log(self, title: str, detail: str = "", severity: str = SEVERITY_INFO,
                category: str = "general", url: str = "") -> int:
        cur = self._db.execute(
            "INSERT INTO logs (title, detail, severity, category, url) VALUES (?,?,?,?,?)",
            (title, detail, severity, category, url)
        )
        self._db.commit()
        self._broadcast_log(cur.lastrowid)
        return cur.lastrowid

    def resolve_log(self, log_id: int, progress: int = 100):
        status = "resolved" if progress >= 100 else "resolving"
        self._db.execute(
            "UPDATE logs SET status=?, progress=? WHERE id=?",
            (status, progress, log_id)
        )
        self._db.commit()

    def get_logs(self, limit: int = 50, severity: Optional[str] = None) -> list:
        q = "SELECT * FROM logs"
        params: list = []
        if severity:
            q += " WHERE severity=?"
            params.append(severity)
        q += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        rows = self._db.execute(q, params).fetchall()
        return [dict(r) for r in rows]

    # ── KV store (simple agent state) ────────────────────────────────────────

    def set_state(self, key: str, value):
        self._db.execute(
            "INSERT OR REPLACE INTO kv (key, value, ts) VALUES (?,?,datetime('now'))",
            (key, json.dumps(value))
        )
        self._db.commit()

    def get_state(self, key: str, default=None):
        row = self._db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except Exception:
            return default

    # ── JARVIS command routing ────────────────────────────────────────────────

    async def handle_jarvis_command(self, command: str) -> str:
        """
        Override in subclass to handle voice/text commands routed from JARVIS.
        Default: pass to execute() with method='command'.
        """
        return await self.execute("command", {"text": command})

    # ── Status for agent network view ─────────────────────────────────────────

    def get_status(self) -> dict:
        """Return a status dict for the JARVIS agent network panel."""
        recent = self.get_logs(limit=5)
        alerts = [l for l in recent if l["severity"] == SEVERITY_ALERT and l["status"] == "open"]
        return {
            "name":     self.name,
            "online":   True,
            "alerts":   len(alerts),
            "last_run": self.get_state("last_run", "never"),
        }

    def _mark_run(self):
        self.set_state("last_run", datetime.utcnow().isoformat())

    # ── Internal bus broadcast ────────────────────────────────────────────────

    def _broadcast_log(self, log_id: int):
        try:
            from core.bus import bus
            row = self._db.execute("SELECT * FROM logs WHERE id=?", (log_id,)).fetchone()
            if row:
                bus.publish_sync(f"{self.name}.log", dict(row))
        except Exception:
            pass
