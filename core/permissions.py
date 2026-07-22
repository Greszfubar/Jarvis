"""
The permission gate — the single chokepoint for consequential actions.

Any agent (JARVIS included) that wants to perform an external or destructive
action calls `request_permission()`. The gate:

  1. classifies the action (SAFE actions pass straight through),
  2. publishes a "permission.request" bus event → the OS shows a confirm
     overlay and JARVIS asks out loud,
  3. waits for Evan's answer — spoken ("yes"/"go ahead"/"no") or pinched
     on the overlay buttons — and times out to DENY.

CVV entry and final payment-page acceptance are never automated at all;
they aren't even representable here.
"""
import asyncio
import logging
import re
import time
import uuid

from core.bus import bus

log = logging.getLogger("jarvis.permissions")

# Action classes that require explicit confirmation
GATED_ACTIONS = {
    "send_email":     "send an email",
    "calendar_write": "modify the calendar",
    "git_push":       "push code to GitHub",
    "install_agent":  "install a new agent with machine access",
    "shell_danger":   "run a destructive shell command",
    "self_edit":      "edit JARVIS's own code",
    "purchase":       "make a purchase",
}

# Shell commands that must go through the gate
_DANGEROUS_SHELL_RE = re.compile(
    r"\b(rm\s+-rf?|rm\s+|rmdir|mkfs|dd\s+|shutdown|reboot|killall|"
    r"git\s+push|git\s+reset\s+--hard|>\s*/dev/|sudo\s)", re.IGNORECASE)

_AFFIRM_RE = re.compile(
    r"^(yes|yeah|yep|confirm|confirmed|go ahead|do it|proceed|approved?|affirmative)\b",
    re.IGNORECASE)
_DENY_RE = re.compile(
    r"^(no|nope|cancel|deny|denied|stop|don'?t|negative|abort)\b", re.IGNORECASE)

TIMEOUT_SECS = 45.0


class PermissionGate:
    def __init__(self):
        self._pending: dict = None   # {id, action, description, future, ts}

    # ── Requesting side (agents / orchestrator) ───────────────────────────────

    async def request(self, action: str, description: str) -> bool:
        """
        Ask Evan for permission. Returns True only on explicit approval.
        One pending request at a time; a second request queues behind the
        bus timeout of the first.
        """
        if action not in GATED_ACTIONS:
            # Unknown action classes are gated by default — safety over convenience
            log.warning(f"Unknown action class '{action}' — gating anyway")

        while self._pending is not None:
            await asyncio.sleep(0.5)

        req_id = uuid.uuid4().hex[:8]
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self._pending = {"id": req_id, "action": action,
                         "description": description, "future": fut,
                         "ts": time.monotonic()}
        log.info(f"Permission request [{req_id}] {action}: {description}")
        await bus.publish("permission.request", {
            "id": req_id, "action": action, "description": description,
            "label": GATED_ACTIONS.get(action, action),
        })
        try:
            return await asyncio.wait_for(fut, timeout=TIMEOUT_SECS)
        except asyncio.TimeoutError:
            log.info(f"Permission request [{req_id}] timed out → DENIED")
            await bus.publish("permission.resolved", {"id": req_id, "allowed": False, "how": "timeout"})
            return False
        finally:
            self._pending = None

    # ── Answering side (voice pipeline / OS overlay) ──────────────────────────

    @property
    def pending(self) -> dict:
        return self._pending

    def try_voice_answer(self, text: str) -> bool:
        """
        Called by the orchestrator for every utterance while a request is
        pending. Returns True if the utterance resolved the request (and was
        therefore consumed — it should not go to the model).
        """
        if not self._pending:
            return False
        t = text.strip()
        if _AFFIRM_RE.match(t):
            self._resolve(True, "voice")
            return True
        if _DENY_RE.match(t):
            self._resolve(False, "voice")
            return True
        return False

    def resolve_ui(self, req_id: str, allowed: bool) -> bool:
        """Called from the OS overlay buttons."""
        if self._pending and self._pending["id"] == req_id:
            self._resolve(allowed, "ui")
            return True
        return False

    def _resolve(self, allowed: bool, how: str):
        p = self._pending
        if p and not p["future"].done():
            p["future"].set_result(allowed)
            log.info(f"Permission [{p['id']}] {'APPROVED' if allowed else 'DENIED'} via {how}")
            asyncio.create_task(bus.publish("permission.resolved", {
                "id": p["id"], "allowed": allowed, "how": how,
            }))


def is_dangerous_shell(cmd: str) -> bool:
    return bool(_DANGEROUS_SHELL_RE.search(cmd))


gate = PermissionGate()
