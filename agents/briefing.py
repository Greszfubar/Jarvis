"""BriefingAgent — compiles and delivers the daily morning briefing."""
import asyncio
import logging
from datetime import datetime

from agents.base import BaseAgent
from core.memory import Memory

log = logging.getLogger("jarvis.briefing")
mem = Memory()


class BriefingAgent(BaseAgent):
    name = "briefing"

    def tools(self):
        return [
            self._tool("generate_briefing", "Generate a full daily briefing covering weather, calendar, email, news, and tasks.", {}),
        ]

    async def execute(self, method: str, params: dict):
        if method == "generate_briefing":
            return await self._compile()
        return {"error": f"Unknown method: {method}"}

    async def _compile(self) -> dict:
        weather = mem.get_fact("weather_current") or {}
        calendar = mem.get_fact("calendar_upcoming") or []
        news_general = mem.get_fact("news_general") or {}
        tasks = mem.get_fact("tasks_pending") or []
        unread = mem.get_fact("gmail_unread_count") or 0

        return {
            "date": datetime.now().strftime("%A, %B %d %Y"),
            "weather": weather,
            "events_today": calendar[:5],
            "top_news": (news_general.get("articles") or [])[:4],
            "tasks_pending": tasks[:5],
            "unread_emails": unread,
        }

    async def tick(self):
        """Deliver briefing once per day at configured time."""
        now = datetime.now().strftime("%H:%M")
        wake_time = mem.get_fact("briefing_scheduled", "08:00")
        delivered = mem.get_fact("briefing_delivered_date", "")
        today = datetime.now().strftime("%Y-%m-%d")

        if now >= wake_time and delivered != today:
            mem.set_fact("briefing_delivered_date", today)
            briefing = await self._compile()
            from core.bus import bus
            await bus.publish("jarvis.briefing", {"data": briefing})
            log.info("Daily briefing compiled and published")
