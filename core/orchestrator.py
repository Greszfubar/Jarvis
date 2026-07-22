"""
JARVIS Orchestrator — uses the local `claude` CLI (no API key required).

Architecture:
- Agents run on schedules and write live data into Memory facts.
- Every user message gets a context block with that live data injected.
- Claude sees real, current data without needing a tool-call loop.
- Actions (send email, add event, open app) are detected in Claude's response
  and executed transparently.
"""
import asyncio
import json
import logging
import re
import subprocess
from datetime import datetime
from typing import Any, Optional

from core.bus import bus
from core.config import cfg, env
from core.memory import Memory
from core.para_memory import append_to_daily, get_profile, get_rules, init_profile

log = logging.getLogger("jarvis.orchestrator")

CLAUDE_CMD = "claude"

SYSTEM_PROMPT = """You are JARVIS — a personal AI operating system for {name}. You are calm, intelligent, precise, and slightly formal. You speak like a highly capable executive assistant who anticipates needs before they arise.

Personality:
- Concise and direct. No filler phrases like "Certainly!" or "Of course!".
- Address the user as "{name}".
- Use real data from the context block when answering. Never fabricate facts.
- When you perform an action, confirm it briefly.
- End with a forward-looking note when relevant.

Layer 2 Specialist Agents — your built-in sub-systems (do NOT treat these as unknown external services):
- VISION  — Intelligence & planning. Manages calendar events, strategic plans, briefings, scheduling.
             Commands: "show today's events", "add a plan called X", "what's on the calendar", etc.
- ULTRON  — Security & threat intelligence. Breach checks, domain scanning, watchlist monitoring.
- FRIDAY  — Content & research. News curation, blog generation, newspaper summaries.
- GRESZ   — Business intelligence. Projects, pipeline, clients, executive briefings.
All agents run locally as part of JARVIS. You can delegate to them and relay their responses.

Actions you can trigger by including them in your response:
- To open an app:      [ACTION:open_app:AppName]
- To send a reminder:  [ACTION:add_task:Task title]
- To open a URL:       [ACTION:open_url:https://...]
- To run shell:        [ACTION:shell:command]
- To notify:           [ACTION:notify:Title|Message]
- To save a fact to the Hard Drive memory store: [ACTION:save_to_hardrive:tab|title|content]
  where tab is one of: info, memories, goals, relations
  Example: [ACTION:save_to_hardrive:goals|Biology Exam|Biology IGCSE exam on 12 May 2026]
  Use this whenever the user mentions: exam dates, important deadlines, goals, key personal facts,
  people they mention, or anything they want remembered long-term.
- To show a banner on the JARVIS OS screen: [ACTION:os:banner|SHORT MESSAGE]
- To delegate to a specialist agent: [ACTION:agent:vision|command text]
  Replace 'vision' with: vision / ultron / friday / gresz
  Example: [ACTION:agent:vision|add a plan called Revision Week due June 18]
  Example: [ACTION:agent:vision|what events are on this week]
  The agent's reply will be shown to the user.
You may include one or more actions anywhere in your response. They will be executed silently.
""".format(name=env("USER_NAME", "Sir"))


class Orchestrator:
    def __init__(self):
        self._memory = Memory()
        self._agents: dict[str, Any] = {}
        init_profile(env("USER_NAME", "Evan"))

    def register_agent(self, agent):
        self._agents[agent.name] = agent
        log.info(f"Registered agent: {agent.name}")

    def _build_context(self) -> str:
        """Pull live facts from memory and format as a readable context block."""
        lines = [f"[LIVE CONTEXT — {datetime.now().strftime('%A %B %d, %Y %H:%M')}]"]

        weather = self._memory.get_fact("weather_current")
        if weather:
            lines.append(
                f"Weather: {weather.get('temp')}° {weather.get('units','')}, "
                f"{weather.get('condition')}, feels {weather.get('feels_like')}°, "
                f"humidity {weather.get('humidity')}%, wind {weather.get('wind')} mph — {weather.get('city')}"
            )

        events = self._memory.get_fact("calendar_upcoming")
        if events:
            ev_strs = [f"{e.get('title')} at {e.get('start','')[:16]}" for e in events[:4]]
            lines.append(f"Upcoming events: {'; '.join(ev_strs)}")

        tasks = self._memory.get_fact("tasks_pending")
        if tasks:
            t_strs = [t.get("title", "") for t in tasks[:5]]
            lines.append(f"Pending tasks: {', '.join(t_strs)}")

        unread = self._memory.get_fact("gmail_unread_count")
        if unread:
            lines.append(f"Unread email: {unread} messages")

        news = self._memory.get_fact("news_general") or self._memory.get_fact("news_technology")
        if news and news.get("articles"):
            headlines = [a.get("title", "") for a in news["articles"][:4]]
            lines.append(f"Top news: {' | '.join(headlines)}")

        return "\n".join(lines) if len(lines) > 1 else ""

    def _build_system(self) -> str:
        """Build the full system prompt: instructions + PARA profile + live context + history."""
        history = self._memory.get_history(limit=10)
        context = self._build_context()
        profile = get_profile()
        rules   = get_rules()
        parts   = [SYSTEM_PROMPT]
        if rules:
            parts.append(f"\n{rules}")
        if profile:
            parts.append(f"\n{profile}")
        if context:
            parts.append(context)
        if history:
            parts.append("\nConversation so far:")
            name = env("USER_NAME", "Sir")
            for msg in history:
                role = name if msg["role"] == "user" else "JARVIS"
                parts.append(f"{role}: {msg['content']}")
        return "\n".join(parts)

    async def process(self, user_input: str) -> str:
        self._memory.add_message("user", user_input)
        append_to_daily("user", user_input)          # write to daily note
        system = self._build_system()

        raw = await asyncio.to_thread(self._call_claude, user_input, system)
        if not raw:
            raw = "I didn't catch that. Could you repeat?"

        clean_response = await self._handle_actions(raw)

        self._memory.add_message("assistant", clean_response)
        append_to_daily("assistant", clean_response)  # write response to daily note
        self._memory.remember(f"User: {user_input}\nJARVIS: {clean_response}")
        await bus.publish("jarvis.response", {"text": clean_response})
        return clean_response

    def _call_claude(self, user_message: str, system_prompt: str) -> str:
        """
        Call the claude CLI correctly:
          -p <user_message>          positional arg — single-line user turn
          --system-prompt <system>   full system context (multi-line OK)

        We strip ANTHROPIC_API_KEY from the env so the CLI uses the
        logged-in OAuth session rather than the placeholder in .env.
        """
        import os
        clean_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        try:
            result = subprocess.run(
                [CLAUDE_CMD, "-p", user_message,
                 "--system-prompt", system_prompt,
                 "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=90,
                env=clean_env,
            )
            if result.returncode != 0:
                log.error(
                    f"claude CLI error (rc={result.returncode}) "
                    f"stderr={result.stderr[:300]!r} stdout={result.stdout[:300]!r}"
                )
                return "I encountered an issue — check logs."
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "Request timed out. I'm still here — try a simpler query."
        except FileNotFoundError:
            log.error("claude CLI not found on PATH")
            return "claude CLI not found. Please ensure Claude Code is installed."
        except Exception as e:
            log.error(f"Unexpected error calling claude: {e}")
            return "Something went wrong. Check logs for details."

    async def _handle_actions(self, response: str) -> str:
        """Extract [ACTION:type:value] tags, execute them, remove from text."""
        pattern = r'\[ACTION:(\w+):([^\]]+)\]'
        actions = re.findall(pattern, response)
        clean = re.sub(pattern, '', response).strip()

        for action_type, value in actions:
            try:
                await self._execute_action(action_type, value)
            except Exception as e:
                log.error(f"Action {action_type} failed: {e}")

        return clean

    async def _execute_action(self, action_type: str, value: str):
        import subprocess as sp
        if action_type == "open_app":
            await asyncio.to_thread(sp.Popen, ["open", "-a", value])
            log.info(f"Opened app: {value}")
        elif action_type == "add_task":
            agent = self._agents.get("tasks")
            if agent:
                await agent.execute("add_task", {"title": value})
        elif action_type == "open_url":
            await asyncio.to_thread(sp.Popen, ["open", value])
            log.info(f"Opened URL: {value}")
        elif action_type == "shell":
            result = await asyncio.to_thread(
                sp.run, value, shell=True, capture_output=True, text=True, timeout=10
            )
            log.info(f"Shell [{value}]: {result.stdout[:200]}")
        elif action_type == "notify":
            parts = value.split("|", 1)
            title = parts[0]
            msg = parts[1] if len(parts) > 1 else ""
            script = f'display notification "{msg}" with title "{title}"'
            await asyncio.to_thread(sp.run, ["osascript", "-e", script], timeout=5)
        elif action_type == "os":
            # Format: command|arg — drives the JARVIS OS screen via the bus
            parts = value.split("|", 1)
            await bus.publish("os.command", {
                "command": parts[0].strip().lower(),
                "arg": parts[1].strip() if len(parts) > 1 else "",
            })
        elif action_type == "agent":
            # Format: agent_name|command text
            # Delegate to a Layer 2 specialist agent and surface its reply
            try:
                parts   = value.split("|", 1)
                name    = parts[0].strip().lower()
                command = parts[1].strip() if len(parts) > 1 else ""
                if not command:
                    return
                import httpx as _httpx
                # Use the specialist /command endpoint (POST /api/chat routes through orchestrator,
                # but specialist agents have their own execute("command", ...) method)
                resp = await asyncio.to_thread(
                    lambda: _httpx.post(
                        f"http://127.0.0.1:8765/api/specialist/{name}/command",
                        json={"text": command},
                        timeout=20,
                    )
                )
                if resp.status_code == 200:
                    data = resp.json()
                    msg  = data.get("message") or data.get("response") or str(data)
                    log.info(f"Agent {name} replied: {msg[:120]}")
                    # Surface the reply in the conversation via the bus
                    await bus.publish("jarvis.response", {"text": f"[{name.upper()}]: {msg}"})
                else:
                    log.warning(f"Agent {name} returned {resp.status_code}")
            except Exception as e:
                log.warning(f"agent action failed ({value}): {e}")

        elif action_type == "save_to_hardrive":
            # Format: tab|title|content
            try:
                import httpx as _httpx
                parts = value.split("|", 2)
                tab     = parts[0].strip() if len(parts) > 0 else "memories"
                title   = parts[1].strip() if len(parts) > 1 else value[:60]
                content = parts[2].strip() if len(parts) > 2 else title
                if tab not in ("info", "memories", "goals", "relations"):
                    tab = "memories"
                await asyncio.to_thread(
                    lambda: _httpx.post(
                        "http://127.0.0.1:8765/api/brain/hardrive",
                        json={"tab": tab, "title": title, "content": content,
                              "tags": [tab], "source": "jarvis"},
                        timeout=5,
                    )
                )
                log.info(f"Saved to hard drive: [{tab}] {title}")
            except Exception as e:
                log.warning(f"save_to_hardrive failed: {e}")

    async def run_proactive(self):
        for agent in self._agents.values():
            try:
                await agent.tick()
            except Exception as e:
                log.error(f"Proactive tick [{agent.name}]: {e}")


orchestrator = Orchestrator()
