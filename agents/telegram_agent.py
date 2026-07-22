"""
TelegramAgent — control JARVIS from your phone anywhere.

Security model (Felix-inspired):
- Only your Telegram chat ID can issue commands. Everyone else gets ignored.
- Telegram is the ONLY authenticated remote command channel.
- All other channels (email, Twitter, web strangers) are information-only.

Setup:
1. Message @BotFather on Telegram → /newbot → copy the token
2. Start a chat with your bot, then visit:
   https://api.telegram.org/bot<TOKEN>/getUpdates
   Copy your numeric chat_id from the response.
3. Add to config/.env:
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_numeric_id
"""
import asyncio
import logging
import threading
from datetime import datetime
from typing import Optional

from agents.base import BaseAgent
from core.config import env
from core.memory import Memory

log = logging.getLogger("jarvis.telegram")
mem = Memory()

# Will be set once the agent is started
_bot_app = None
_send_queue: asyncio.Queue = None  # for pushing messages to Telegram


class TelegramAgent(BaseAgent):
    name = "telegram"

    def __init__(self):
        self._token       = env("TELEGRAM_BOT_TOKEN")
        self._allowed_id  = env("TELEGRAM_CHAT_ID")
        self._app         = None
        self._loop        = None
        self._orchestrator = None   # injected after init

    def set_orchestrator(self, orch):
        self._orchestrator = orch

    # ── BaseAgent interface ───────────────────────────────────────────────────

    def tools(self):
        return [
            self._tool("send_message", "Send a message to the user's Telegram.", {
                "text": {"type": "string"},
            }, required=["text"]),
        ]

    async def execute(self, method: str, params: dict):
        if method == "send_message":
            await self.push(params["text"])
            return {"status": "sent"}
        return {"error": f"Unknown method: {method}"}

    async def tick(self):
        pass   # Telegram bot runs its own loop

    # ── Bot lifecycle ─────────────────────────────────────────────────────────

    def start(self, loop: asyncio.AbstractEventLoop):
        if not self._token or not self._allowed_id:
            log.warning(
                "Telegram not configured — add TELEGRAM_BOT_TOKEN and "
                "TELEGRAM_CHAT_ID to config/.env to enable phone control."
            )
            return
        self._loop = loop
        t = threading.Thread(
            target=lambda: asyncio.run(self._run_bot()),
            daemon=True,
            name="telegram-bot",
        )
        t.start()
        log.info(f"Telegram bot started — only chat_id {self._allowed_id} can command JARVIS")

    async def _run_bot(self):
        from telegram import Update
        from telegram.ext import Application, MessageHandler, CommandHandler, filters

        self._app = (
            Application.builder()
            .token(self._token)
            .build()
        )

        # Register handlers
        self._app.add_handler(CommandHandler("start",   self._cmd_start))
        self._app.add_handler(CommandHandler("status",  self._cmd_status))
        self._app.add_handler(CommandHandler("brief",   self._cmd_brief))
        self._app.add_handler(CommandHandler("stop",    self._cmd_stop))
        self._app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))

        global _bot_app
        _bot_app = self._app

        log.info("Telegram polling started")
        await self._app.initialize()

        # Kill any lingering long-poll from a previous process.
        # getMe always succeeds so we use a lightweight getUpdates(timeout=0)
        # as the real probe — a 409 means another session is still alive.
        for attempt in range(10):
            try:
                await self._app.bot.delete_webhook(drop_pending_updates=True)
                # Real slot check: timeout=0 returns immediately, throws 409 if busy
                await self._app.bot.get_updates(timeout=0, limit=1, offset=-1)
                log.info("Telegram slot acquired")
                break
            except Exception as e:
                from telegram.error import Conflict
                if isinstance(e, Conflict):
                    wait = min(2 ** attempt, 30)
                    log.warning(f"Telegram slot busy, retrying in {wait}s… (attempt {attempt+1}/10)")
                    await asyncio.sleep(wait)
                else:
                    # Non-conflict error — don't retry indefinitely
                    log.error(f"Telegram init error: {e}")
                    break

        await self._app.start()
        await self._app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"],
            error_callback=self._on_poll_error,
        )
        # Keep running
        await asyncio.Event().wait()

    _last_409_log: float = 0.0   # rate-limit 409 log spam to once per 30 s

    def _on_poll_error(self, error: Exception):
        """Suppress repetitive 409 log spam."""
        import time
        from telegram.error import Conflict
        if isinstance(error, Conflict):
            now = time.monotonic()
            if now - self._last_409_log > 30:
                log.warning("Telegram 409: another instance still active, waiting it out…")
                self._last_409_log = now
            # Don't log again for 30 s — Telegram resolves these on its own
        else:
            log.error(f"Telegram poll error: {error}")

    def _is_authorized(self, update) -> bool:
        chat_id = str(update.effective_chat.id)
        if chat_id != self._allowed_id:
            log.warning(f"Unauthorized Telegram access attempt from chat_id={chat_id}")
            return False
        return True

    async def _cmd_start(self, update, context):
        if not self._is_authorized(update):
            return
        await update.message.reply_text(
            "JARVIS online. Send me any command — I'm listening."
        )

    async def _cmd_status(self, update, context):
        if not self._is_authorized(update):
            return
        weather = mem.get_fact("weather_current") or {}
        unread  = mem.get_fact("gmail_unread_count") or 0
        tasks   = mem.get_fact("tasks_pending") or []
        events  = mem.get_fact("calendar_upcoming") or []
        msg = (
            f"⬡ *JARVIS STATUS* — {datetime.now().strftime('%H:%M')}\n\n"
            f"🌡 {weather.get('temp','--')}° {weather.get('condition','--')}\n"
            f"✉ {unread} unread emails\n"
            f"✅ {len(tasks)} pending tasks\n"
            f"📅 {len(events)} upcoming events"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def _cmd_brief(self, update, context):
        if not self._is_authorized(update):
            return
        await update.message.reply_text("Generating briefing…")
        response = await self._ask("Give me a concise morning briefing.")
        await update.message.reply_text(response)

    async def _cmd_stop(self, update, context):
        if not self._is_authorized(update):
            return
        await update.message.reply_text("Acknowledged. Shutting down.")
        import os, signal
        os.kill(os.getpid(), signal.SIGTERM)

    async def _on_message(self, update, context):
        if not self._is_authorized(update):
            return
        text = update.message.text.strip()
        if not text:
            return
        log.info(f"Telegram command: {text[:80]}")
        await update.message.reply_text("Processing…")
        mem.log_event("telegram", "command", {"text": text})
        response = await self._ask(text)
        await update.message.reply_text(response)

    async def _ask(self, text: str) -> str:
        if self._orchestrator:
            return await self._orchestrator.process(text)
        return "Orchestrator not available."

    # ── Push notifications to Telegram ───────────────────────────────────────

    async def push(self, message: str):
        """Send a proactive message to the user's Telegram."""
        if not self._app or not self._allowed_id:
            return
        try:
            await self._app.bot.send_message(
                chat_id=int(self._allowed_id),
                text=message,
            )
        except Exception as e:
            log.error(f"Telegram push failed: {e}")
