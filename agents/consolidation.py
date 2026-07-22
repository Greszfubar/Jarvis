"""
ConsolidationAgent — nightly knowledge base update (runs at 2 AM).

Reads today's conversation log from daily notes, extracts:
- New facts about people, projects, companies
- Decisions made
- Action items completed/pending
- Updated user preferences

Then updates the PARA knowledge graph accordingly.
Mirrors Felix's nightly consolidation job.
"""
import asyncio
import logging
import subprocess
from datetime import datetime, date

from agents.base import BaseAgent
from core.config import env
from core.memory import Memory
from core.para_memory import (
    get_recent_daily_notes, append_note_section,
    upsert_entity, LIFE_DIR
)

log = logging.getLogger("jarvis.consolidation")
mem = Memory()

CLAUDE_CMD = "claude"


class ConsolidationAgent(BaseAgent):
    name = "consolidation"

    def tools(self):
        return [
            self._tool("run_consolidation", "Manually trigger the nightly knowledge consolidation.", {}),
            self._tool("get_knowledge_summary", "Get a summary of what JARVIS knows about a topic or person.", {
                "query": {"type": "string"},
            }, required=["query"]),
        ]

    async def execute(self, method: str, params: dict):
        if method == "run_consolidation":
            return await self._consolidate()
        if method == "get_knowledge_summary":
            return await asyncio.to_thread(self._search_knowledge, params["query"])
        return {"error": f"Unknown method: {method}"}

    async def tick(self):
        """Run at 2 AM."""
        now = datetime.now()
        if now.hour == 2 and now.minute < 5:
            already_ran = mem.get_fact(f"consolidation_{date.today().isoformat()}")
            if not already_ran:
                log.info("Running nightly consolidation…")
                await self._consolidate()

    async def _consolidate(self) -> dict:
        notes = get_recent_daily_notes(days=2)
        if not notes or len(notes) < 100:
            return {"status": "skipped", "reason": "Not enough content to consolidate"}

        system = """You are a knowledge extraction system. Analyze conversation logs and extract structured information.

Output a JSON object with this structure:
{
  "entities": [
    {"category": "projects|areas|resources", "name": "...", "summary": "...", "facts": [{"key": "...", "value": "..."}]}
  ],
  "decisions": ["..."],
  "action_items": ["..."],
  "user_insights": ["..."],
  "daily_summary": "2-3 sentence summary of the day"
}

Only include entities that are clearly significant. Be precise and factual."""

        prompt = f"Extract knowledge from these conversation logs:\n\n{notes[:6000]}"

        raw = await asyncio.to_thread(self._call_claude, prompt, system)

        # Parse and apply
        try:
            import json, re
            # Extract JSON from response
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if not m:
                raise ValueError("No JSON found")
            data = json.loads(m.group())

            # Upsert entities
            for entity in data.get("entities", []):
                upsert_entity(
                    entity["category"],
                    entity["name"],
                    entity.get("summary", ""),
                    entity.get("facts", []),
                )

            # Append summary to today's note
            summary = data.get("daily_summary", "")
            if summary:
                append_note_section("Daily Summary", summary)

            decisions = data.get("decisions", [])
            if decisions:
                append_note_section("Key Decisions", "\n".join(f"- {d}" for d in decisions))

            mem.set_fact(f"consolidation_{date.today().isoformat()}", True)
            log.info(f"Consolidation complete: {len(data.get('entities',[]))} entities updated")

            # Notify via Telegram if configured
            from core.bus import bus
            await bus.publish("jarvis.alert", {
                "source": "consolidation",
                "message": f"Nightly consolidation complete. {len(data.get('entities',[]))} knowledge entries updated.",
            })

            return {"status": "complete", "entities_updated": len(data.get("entities", []))}

        except Exception as e:
            log.error(f"Consolidation parse error: {e}\nRaw: {raw[:300]}")
            return {"status": "error", "error": str(e)}

    def _search_knowledge(self, query: str) -> dict:
        from core.para_memory import search_entities
        results = search_entities(query)
        return {"query": query, "results": results[:5]}

    def _call_claude(self, prompt: str, system: str) -> str:
        import os
        clean_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        try:
            result = subprocess.run(
                [CLAUDE_CMD, "-p", prompt, "--system-prompt", system, "--output-format", "text"],
                capture_output=True, text=True, timeout=120, env=clean_env,
            )
            return result.stdout.strip()
        except Exception as e:
            log.error(f"Claude call error: {e}")
            return ""
