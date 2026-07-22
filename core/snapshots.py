"""
The rollback spine — snapshot before every self-modification, auto-revert on
failure. This is what makes Patch (the agent that edits JARVIS's own code)
safe to build: no change lands without a known-good state to fall back to.

Pattern for any self-editing agent:

    from core.snapshots import guarded_change

    report = guarded_change("fix voice threshold", apply_fn)
    # apply_fn() makes the edits. If the post-change health check fails,
    # the working tree is reverted to the pre-change snapshot and the
    # report says so. Every outcome produces a report for JARVIS to read
    # aloud or pull onto the Stage.
"""
import json
import logging
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path

log = logging.getLogger("jarvis.snapshots")

REPO = Path(__file__).resolve().parent.parent
LAST_GOOD_FILE = REPO / "data" / "last_good_snapshot.json"

# Modules whose importability defines "JARVIS is healthy"
HEALTH_IMPORTS = ["core.orchestrator", "core.bus", "core.governor",
                  "core.permissions", "ui.web", "hands.gestures"]


def _git(*args, check=True) -> str:
    r = subprocess.run(["git", "-C", str(REPO), *args],
                       capture_output=True, text=True, timeout=60)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:300]}")
    return r.stdout.strip()


def snapshot(label: str) -> str:
    """Commit the current tree as a snapshot; returns the commit sha."""
    _git("add", "-A")
    # --allow-empty: a snapshot is meaningful even with no pending changes
    _git("commit", "--allow-empty", "-q", "-m", f"snapshot: {label}")
    sha = _git("rev-parse", "HEAD")
    log.info(f"Snapshot [{label}] → {sha[:10]}")
    return sha


def health_check() -> tuple:
    """
    Is JARVIS's code alive? Byte-compile everything, then import the spine
    modules in a fresh interpreter. Returns (ok, detail).
    """
    py = str(REPO / ".venv" / "bin" / "python")
    r = subprocess.run(
        [py, "-m", "compileall", "-q", "core", "agents", "ui", "voice", "hands", "main.py"],
        capture_output=True, text=True, timeout=120, cwd=str(REPO),
    )
    if r.returncode != 0:
        return False, f"compile failed: {(r.stderr or r.stdout).strip()[:400]}"
    imports = "; ".join(f"import {m}" for m in HEALTH_IMPORTS)
    r = subprocess.run([py, "-c", imports], capture_output=True, text=True,
                       timeout=120, cwd=str(REPO))
    if r.returncode != 0:
        return False, f"import failed: {r.stderr.strip()[:400]}"
    return True, "compile + spine imports OK"


def revert_to(sha: str):
    """Hard-revert the working tree to a snapshot."""
    _git("reset", "--hard", sha)
    log.warning(f"Reverted working tree to {sha[:10]}")


def mark_last_good(sha: str):
    LAST_GOOD_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_GOOD_FILE.write_text(json.dumps({"sha": sha, "ts": time.time()}))


def last_good() -> str:
    try:
        return json.loads(LAST_GOOD_FILE.read_text())["sha"]
    except Exception:
        return ""


@dataclass
class ChangeReport:
    label: str
    ok: bool
    snapshot_sha: str
    detail: str
    reverted: bool = False

    def spoken(self) -> str:
        if self.ok:
            return f"Change applied and healthy: {self.label}."
        if self.reverted:
            return (f"The change '{self.label}' failed its health check — "
                    f"I reverted to the last good snapshot. Detail: {self.detail}")
        return f"The change '{self.label}' failed and could not be reverted: {self.detail}"


def guarded_change(label: str, apply_fn) -> ChangeReport:
    """
    The one true way to modify JARVIS's own code:
    snapshot → apply → health check → (commit | revert) → report.
    """
    pre_sha = snapshot(f"pre-change: {label}")
    try:
        apply_fn()
    except Exception as e:
        revert_to(pre_sha)
        return ChangeReport(label, False, pre_sha, f"apply raised: {e}", reverted=True)

    ok, detail = health_check()
    if not ok:
        revert_to(pre_sha)
        return ChangeReport(label, False, pre_sha, detail, reverted=True)

    _git("add", "-A")
    _git("commit", "--allow-empty", "-q", "-m", f"change: {label}")
    new_sha = _git("rev-parse", "HEAD")
    mark_last_good(new_sha)
    return ChangeReport(label, True, pre_sha, detail)
