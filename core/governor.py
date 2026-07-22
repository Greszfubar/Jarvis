"""
The budget governor — every model call is accounted; caps are enforced.

Ledger lives in data/governor.db. Two caps, both configurable via env:
    JARVIS_BUDGET_MONTHLY_GBP   (default 5000 — the hard ceiling)
    JARVIS_BUDGET_NIGHTLY_GBP   (default 15  — the night cycle is designed
                                 never to approach it)
    JARVIS_GBP_PER_USD          (default 0.79 — CLI reports costs in USD)

Contract: call `check()` before a model call (raises nothing, returns a
verdict), `record()` after it with the actual cost. At 80% of a cap the
verdict carries a warning JARVIS should say out loud; at 100% calls are
refused until the window resets.
"""
import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from pathlib import Path

from core.config import env

log = logging.getLogger("jarvis.governor")

_DB_PATH = Path("data/governor.db")

NIGHT_START_HOUR = 23   # night window: 23:00 → 08:00
NIGHT_END_HOUR   = 8


def _db() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS model_calls (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            ts       TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            source   TEXT NOT NULL,
            model    TEXT DEFAULT '',
            cost_usd REAL NOT NULL DEFAULT 0,
            note     TEXT DEFAULT ''
        )
    """)
    conn.commit()
    return conn


def _gbp(usd: float) -> float:
    return usd * float(env("JARVIS_GBP_PER_USD", "0.79"))


def monthly_cap_gbp() -> float:
    return float(env("JARVIS_BUDGET_MONTHLY_GBP", "5000"))


def nightly_cap_gbp() -> float:
    return float(env("JARVIS_BUDGET_NIGHTLY_GBP", "15"))


def spent_month_gbp() -> float:
    month_start = date.today().replace(day=1).isoformat()
    db = _db()
    row = db.execute(
        "SELECT COALESCE(SUM(cost_usd),0) FROM model_calls WHERE ts >= ?",
        (month_start,),
    ).fetchone()
    db.close()
    return _gbp(row[0])


def spent_night_gbp() -> float:
    """Spend inside the current night window (23:00 yesterday/today → now)."""
    now = datetime.now()
    if now.hour >= NIGHT_START_HOUR:
        night_start = now.replace(hour=NIGHT_START_HOUR, minute=0, second=0)
    elif now.hour < NIGHT_END_HOUR:
        night_start = (now - timedelta(days=1)).replace(hour=NIGHT_START_HOUR, minute=0, second=0)
    else:
        return 0.0   # daytime — nightly cap not in play
    db = _db()
    row = db.execute(
        "SELECT COALESCE(SUM(cost_usd),0) FROM model_calls WHERE ts >= ?",
        (night_start.strftime("%Y-%m-%d %H:%M:%S"),),
    ).fetchone()
    db.close()
    return _gbp(row[0])


@dataclass
class Verdict:
    allowed: bool
    warning: str = ""    # non-empty → JARVIS should say this out loud


def check(source: str = "") -> Verdict:
    month = spent_month_gbp()
    m_cap = monthly_cap_gbp()
    if month >= m_cap:
        log.error(f"Budget governor: MONTHLY CAP HIT (£{month:.2f}/£{m_cap:.0f}) — refusing {source}")
        return Verdict(False, f"Monthly budget ceiling reached: £{month:.0f} of £{m_cap:.0f}. "
                              f"Model calls are paused until next month or a cap change.")

    night = spent_night_gbp()
    n_cap = nightly_cap_gbp()
    if night >= n_cap:
        log.error(f"Budget governor: NIGHTLY CAP HIT (£{night:.2f}/£{n_cap:.0f}) — refusing {source}")
        return Verdict(False, f"Nightly budget cap reached (£{night:.2f}). Resuming at 8 AM.")

    if month >= 0.8 * m_cap:
        return Verdict(True, f"Heads up: monthly spend is at £{month:.0f} of the £{m_cap:.0f} ceiling.")
    if night and night >= 0.8 * n_cap:
        return Verdict(True, f"Heads up: tonight's spend is at £{night:.2f} of the £{n_cap:.0f} cap.")
    return Verdict(True)


def record(source: str, cost_usd: float, model: str = "", note: str = ""):
    if cost_usd <= 0:
        return
    db = _db()
    db.execute(
        "INSERT INTO model_calls (source, model, cost_usd, note) VALUES (?,?,?,?)",
        (source, model, float(cost_usd), note[:200]),
    )
    db.commit()
    db.close()


def summary() -> dict:
    return {
        "month_gbp": round(spent_month_gbp(), 2),
        "month_cap_gbp": monthly_cap_gbp(),
        "night_gbp": round(spent_night_gbp(), 2),
        "night_cap_gbp": nightly_cap_gbp(),
    }
