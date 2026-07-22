"""Central memory layer: SQLite for structured data, ChromaDB for semantic search."""
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions


class Memory:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        from core.config import cfg
        db_path = Path(cfg["memory"]["db_path"])
        chroma_path = Path(cfg["memory"]["chroma_path"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        chroma_path.mkdir(parents=True, exist_ok=True)

        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db_lock = threading.Lock()
        self._setup_db()

        self._chroma = chromadb.PersistentClient(path=str(chroma_path))
        ef = embedding_functions.DefaultEmbeddingFunction()
        self._semantic = self._chroma.get_or_create_collection(
            "jarvis_memory", embedding_function=ef
        )

        self._initialized = True

    def _setup_db(self):
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                ts       TEXT NOT NULL,
                agent    TEXT NOT NULL,
                kind     TEXT NOT NULL,
                payload  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS facts (
                key      TEXT PRIMARY KEY,
                value    TEXT NOT NULL,
                updated  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversation (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                ts       TEXT NOT NULL,
                role     TEXT NOT NULL,
                content  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_events_agent ON events(agent);
            CREATE INDEX IF NOT EXISTS idx_events_kind  ON events(kind);
        """)
        self._db.commit()

    # ── Structured ────────────────────────────────────────

    def log_event(self, agent: str, kind: str, payload: Any):
        with self._db_lock:
            self._db.execute(
                "INSERT INTO events(ts,agent,kind,payload) VALUES(?,?,?,?)",
                (datetime.utcnow().isoformat(), agent, kind, json.dumps(payload, default=str)),
            )
            self._db.commit()

    def set_fact(self, key: str, value: Any):
        with self._db_lock:
            self._db.execute(
                "INSERT OR REPLACE INTO facts(key,value,updated) VALUES(?,?,?)",
                (key, json.dumps(value, default=str), datetime.utcnow().isoformat()),
            )
            self._db.commit()

    def get_fact(self, key: str, default=None) -> Any:
        row = self._db.execute("SELECT value FROM facts WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    def recent_events(self, agent: str = None, kind: str = None, limit: int = 20):
        q = "SELECT * FROM events"
        params, clauses = [], []
        if agent:
            clauses.append("agent=?"); params.append(agent)
        if kind:
            clauses.append("kind=?"); params.append(kind)
        if clauses:
            q += " WHERE " + " AND ".join(clauses)
        q += f" ORDER BY id DESC LIMIT {limit}"
        return [dict(r) for r in self._db.execute(q, params).fetchall()]

    # ── Conversation history ──────────────────────────────

    def add_message(self, role: str, content: str):
        with self._db_lock:
            self._db.execute(
                "INSERT INTO conversation(ts,role,content) VALUES(?,?,?)",
                (datetime.utcnow().isoformat(), role, content),
            )
            self._db.commit()

    def get_history(self, limit: int = 20) -> list[dict]:
        rows = self._db.execute(
            "SELECT role,content FROM conversation ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    # ── Semantic ──────────────────────────────────────────

    def remember(self, text: str, metadata: dict = None):
        doc_id = f"mem_{datetime.utcnow().timestamp()}"
        meta = {"ts": datetime.utcnow().isoformat()}
        if metadata:
            meta.update(metadata)
        self._semantic.add(
            documents=[text],
            metadatas=[meta],
            ids=[doc_id],
        )

    def recall(self, query: str, n: int = 5) -> list[str]:
        try:
            results = self._semantic.query(query_texts=[query], n_results=n)
            return results["documents"][0] if results["documents"] else []
        except Exception:
            return []
