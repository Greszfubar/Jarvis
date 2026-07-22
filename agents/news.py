"""NewsAgent — RSS + NewsAPI with Claude summarization."""
import asyncio
import logging
from datetime import datetime, timezone

import feedparser
import requests

from agents.base import BaseAgent
from core.config import cfg, env
from core.memory import Memory

log = logging.getLogger("jarvis.news")
mem = Memory()


class NewsAgent(BaseAgent):
    name = "news"

    def tools(self):
        return [
            self._tool(
                "get_headlines",
                "Fetch and summarize top news headlines.",
                {
                    "category": {
                        "type": "string",
                        "description": "News category: technology, business, science, sports, general",
                    },
                    "count": {"type": "integer", "description": "Number of stories (default 5)"},
                },
            ),
            self._tool(
                "search_news",
                "Search news for a specific topic or keyword.",
                {"query": {"type": "string", "description": "Search query"}},
                required=["query"],
            ),
        ]

    async def execute(self, method: str, params: dict):
        if method == "get_headlines":
            return await self._headlines(
                params.get("category", "general"), params.get("count", 5)
            )
        if method == "search_news":
            return await self._search(params["query"])
        return {"error": f"Unknown method: {method}"}

    async def _headlines(self, category: str, count: int) -> dict:
        key = env("NEWS_API_KEY")
        articles = []
        if key:
            try:
                r = await asyncio.to_thread(
                    requests.get,
                    "https://newsapi.org/v2/top-headlines",
                    params={"category": category, "pageSize": count, "language": "en", "apiKey": key},
                    timeout=8,
                )
                r.raise_for_status()
                for a in r.json().get("articles", [])[:count]:
                    articles.append({
                        "title": a["title"],
                        "source": a["source"]["name"],
                        "description": a.get("description", ""),
                        "url": a["url"],
                    })
            except Exception as e:
                log.warning(f"NewsAPI error: {e}")

        if not articles:
            articles = await self._rss_fetch(count)

        mem.set_fact(f"news_{category}", {"articles": articles, "fetched": datetime.utcnow().isoformat()})
        return {"category": category, "articles": articles}

    async def _search(self, query: str) -> dict:
        key = env("NEWS_API_KEY")
        if not key:
            return {"error": "NEWS_API_KEY not set"}
        r = await asyncio.to_thread(
            requests.get,
            "https://newsapi.org/v2/everything",
            params={"q": query, "pageSize": 5, "language": "en", "sortBy": "publishedAt", "apiKey": key},
            timeout=8,
        )
        r.raise_for_status()
        articles = [
            {"title": a["title"], "source": a["source"]["name"], "description": a.get("description", ""), "url": a["url"]}
            for a in r.json().get("articles", [])[:5]
        ]
        return {"query": query, "articles": articles}

    async def _rss_fetch(self, count: int) -> list:
        sources = cfg["agents"]["news"]["sources"]
        articles = []
        for url in sources[:3]:
            try:
                feed = await asyncio.to_thread(feedparser.parse, url)
                for entry in feed.entries[:count]:
                    articles.append({
                        "title": entry.get("title", ""),
                        "source": feed.feed.get("title", url),
                        "description": entry.get("summary", "")[:200],
                        "url": entry.get("link", ""),
                    })
                if len(articles) >= count:
                    break
            except Exception as e:
                log.warning(f"RSS error {url}: {e}")
        return articles[:count]

    async def tick(self):
        """Background refresh — cache latest headlines."""
        log.info("News tick: refreshing headlines")
        try:
            await self._headlines("general", 8)
            await self._headlines("technology", 5)
        except Exception as e:
            log.error(f"News tick error: {e}")
