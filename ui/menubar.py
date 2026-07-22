"""macOS menu bar app — always visible status + quick actions."""
import threading
import rumps
from core.memory import Memory
from core.config import env


class JarvisMenuBar(rumps.App):
    def __init__(self, orchestrator):
        super().__init__("⬡ JARVIS", quit_button=None)
        self._orch = orchestrator
        self._mem  = Memory()
        self.menu  = [
            rumps.MenuItem("Status: Online", callback=None),
            None,
            rumps.MenuItem("Daily Briefing",    callback=self.briefing),
            rumps.MenuItem("Check Email",        callback=self.check_email),
            rumps.MenuItem("Today's Calendar",   callback=self.check_calendar),
            rumps.MenuItem("Weather",            callback=self.check_weather),
            rumps.MenuItem("Top News",           callback=self.check_news),
            None,
            rumps.MenuItem("Open Dashboard",     callback=self.open_dashboard),
            None,
            rumps.MenuItem("Quit JARVIS",        callback=rumps.quit_application),
        ]

    def _run_async(self, coro):
        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(coro)
        loop.close()
        return result

    def _ask(self, query: str):
        threading.Thread(
            target=lambda: self._run_async(self._speak_result(query)),
            daemon=True,
        ).start()

    async def _speak_result(self, query: str):
        from voice.speaker import speak
        response = await self._orch.process(query)
        speak(response)

    @rumps.clicked("Daily Briefing")
    def briefing(self, _):
        self._ask("Generate my daily briefing.")

    @rumps.clicked("Check Email")
    def check_email(self, _):
        self._ask("Check my unread emails and summarize the most important ones.")

    @rumps.clicked("Today's Calendar")
    def check_calendar(self, _):
        self._ask("What's on my calendar today?")

    @rumps.clicked("Weather")
    def check_weather(self, _):
        self._ask("What's the current weather?")

    @rumps.clicked("Top News")
    def check_news(self, _):
        self._ask("Give me the top 5 news headlines.")

    @rumps.clicked("Open Dashboard")
    def open_dashboard(self, _):
        import subprocess
        subprocess.Popen(["open", "http://localhost:8765"])

    @rumps.timer(60)
    def update_status(self, _):
        unread = self._mem.get_fact("gmail_unread_count") or 0
        self.menu["Status: Online"].title = f"⬡ Online | ✉ {unread} unread"


def start_menubar(orchestrator):
    app = JarvisMenuBar(orchestrator)
    app.run()
