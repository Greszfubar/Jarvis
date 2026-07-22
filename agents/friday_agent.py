"""
FRIDAY — Content & Media specialist agent (Layer 2).

Capabilities:
  - Live news feed: NewsAPI + RSS fallback, multi-category
  - Daily newspaper: multi-section broadsheet with personal interest topics
    (AI/Claude/ChatGPT, One Piece, AiOS, Liam Ottley, Automation)
  - Auto-publish newspaper every day at 11:00
  - Auto-generate one deep-dive blog post per day
  - Blog post management: stored in SQLite, status tracking
  - Content generation: outlines, drafts, social posts via Claude
"""
import asyncio
import logging
from datetime import datetime

import feedparser
import requests

from agents.base_specialist import BaseSpecialist, SEVERITY_INFO, SEVERITY_WATCH
from core.config import cfg, env

log = logging.getLogger("jarvis.friday")

# ── RSS sources ───────────────────────────────────────────────────────────────
_RSS = {
    "tech":       ["https://feeds.feedburner.com/TechCrunch",
                   "https://www.wired.com/feed/rss",
                   "https://www.theverge.com/rss/index.xml"],
    "business":   ["https://feeds.a.dj.com/rss/RSSBusinessNews.xml"],
    "general":    ["https://feeds.bbci.co.uk/news/rss.xml",
                   "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"],
    "science":    ["https://www.sciencedaily.com/rss/all.xml"],
    "ai":         ["https://www.artificialintelligence-news.com/feed/",
                   "https://machinelearningmastery.com/blog/feed/",
                   "https://feeds.feedburner.com/TechCrunch"],
    "automation": ["https://www.automationworld.com/rss.xml",
                   "https://feeds.feedburner.com/TechCrunch"],
    "anime":      ["https://www.animenewsnetwork.com/all/rss.xml?ann-edition=us"],
}

_CATEGORIES = ["general", "tech", "business", "science"]

# ── Blog topic rotation for daily auto-generation ─────────────────────────────
_BLOG_TOPICS = [
    ("The Future of Personal AI: Building Your Own JARVIS", "Deep-dive into AiOS architecture, personal AI agents, and how JARVIS-style systems will change how we work. Include GreszTech's approach."),
    ("Claude vs ChatGPT vs Gemini: The Real-World Developer Battle", "Honest comparison for developers and AI builders. Which excels at code, reasoning, creativity? GreszTech perspective."),
    ("One Piece and the Art of Long-Form Storytelling in 2025", "What Oda's masterwork teaches us about patience, world-building, and narrative in the age of instant content."),
    ("Liam Ottley's AI Agency Blueprint: What Actually Works", "Breaking down the AI agency model, what's working in 2025, pricing strategies, and the tools that matter."),
    ("Automation That Actually Saves Time: The 10x Workflow Stack", "The automations that compound — Claude, n8n, Zapier, custom agents. Real setups that free up 10+ hours a week."),
    ("The GreszTech Vision: Building AI Infrastructure for the Future", "How GreszTech is approaching AI tooling, why the agent-first approach beats copilots, and where this goes."),
    ("Why Every Developer Needs a Personal AI OS in 2025", "From voice commands to proactive agents — the case for building your own AI operating system rather than relying on chat interfaces."),
    ("Claude's Extended Thinking: When It Changes Everything", "Deep-dive into Claude's chain-of-thought reasoning, when to use it, real performance differences, and what it means for agent builders."),
    ("One Piece Chapter Analysis: The Final Saga Decoded", "Breaking down the narrative threads, foreshadowing, and what the Final Saga tells us about Oda's endgame vision."),
    ("The $100K AI Agency: Liam Ottley's Model vs Reality", "Honest analysis of the AI agency opportunity, market saturation, what niches still work, and alternative paths."),
    ("n8n vs Zapier vs Make: The Automation Platform Showdown 2025", "Real comparison for builders — pricing, complexity, Claude integration, and which to choose for different use cases."),
    ("Building Multi-Agent Systems That Don't Break", "Architecture patterns for reliable multi-agent systems — error handling, state management, and orchestration lessons from JARVIS."),
    ("The One Piece Economy: How Oda Built a $21B Franchise", "Business and brand analysis of the world's best-selling manga — licensing, merchandise, global expansion."),
    ("Anthropic's Safety-First Approach: Does It Make Claude Better?", "Constitutional AI, RLHF, and why Anthropic's constraints might actually produce more useful AI than pure RLHF approaches."),
    ("Personal Knowledge Management with AI: The 2025 Stack", "How to build a second brain using Claude, Obsidian, and custom agents. GreszTech's knowledge architecture."),
]


# ── News helpers ──────────────────────────────────────────────────────────────

def _newsapi_fetch(category: str, count: int = 8, query: str = "") -> list[dict]:
    key = env("NEWSAPI_KEY") or env("NEWS_API_KEY")
    if not key:
        return []
    cat_map = {"tech": "technology", "general": "general",
               "business": "business", "science": "science",
               "ai": "technology", "automation": "technology", "anime": "entertainment"}
    params: dict = {"pageSize": count, "language": "en", "apiKey": key}
    if query:
        params["q"] = query
        params["sortBy"] = "publishedAt"
        url = "https://newsapi.org/v2/everything"
    else:
        params["category"] = cat_map.get(category, "general")
        url = "https://newsapi.org/v2/top-headlines"
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        return [
            {
                "title":   a["title"],
                "source":  a["source"]["name"],
                "summary": (a.get("description") or "")[:200],
                "url":     a.get("url", ""),
                "time":    (a.get("publishedAt") or "")[:16].replace("T", " "),
            }
            for a in r.json().get("articles", [])[:count]
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]
    except Exception as e:
        log.warning(f"NewsAPI error ({category}): {e}")
        return []


def _rss_fetch(category: str, count: int = 8) -> list[dict]:
    sources = _RSS.get(category, _RSS["general"])
    articles = []
    for url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                articles.append({
                    "title":   entry.get("title", ""),
                    "source":  feed.feed.get("title", url),
                    "summary": (entry.get("summary") or "")[:200],
                    "url":     entry.get("link", ""),
                    "time":    "",
                })
                if len(articles) >= count:
                    return articles
        except Exception as e:
            log.warning(f"RSS error {url}: {e}")
    return articles[:count]


def fetch_news(category: str = "general", count: int = 8) -> list[dict]:
    articles = _newsapi_fetch(category, count)
    if not articles:
        articles = _rss_fetch(category, count)
    return articles


def fetch_all_categories(count_each: int = 5) -> dict[str, list]:
    return {cat: fetch_news(cat, count_each) for cat in _CATEGORIES}


def fetch_topic_news() -> dict[str, list]:
    """Fetch news for each of the personal interest topic sections."""
    topics = {}
    # AI / Claude / ChatGPT
    ai = _newsapi_fetch("ai", 6, query="Claude AI OR ChatGPT OR Anthropic OR OpenAI OR Gemini")
    if not ai:
        ai = _rss_fetch("ai", 5)
    topics["ai"] = ai

    # Automation / Agents
    auto = _newsapi_fetch("automation", 4, query="AI automation OR AI agents OR n8n OR workflow automation")
    if not auto:
        auto = _rss_fetch("automation", 4)
    topics["automation"] = auto

    # Anime / One Piece
    anime = _newsapi_fetch("anime", 4, query="One Piece OR Oda OR manga OR anime")
    if not anime:
        anime = _rss_fetch("anime", 4)
    topics["anime"] = anime

    # Liam Ottley / AI business
    liam = _newsapi_fetch("business", 4, query="AI agency OR Liam Ottley OR AI business OR AI entrepreneur")
    if not liam:
        liam = fetch_news("business", 4)
    topics["liam"] = liam

    # General tech
    topics["tech"] = fetch_news("tech", 6)

    return topics


# ── Claude content generation ─────────────────────────────────────────────────

async def _ask_claude(prompt: str, max_tokens: int = 800) -> str:
    """Call Claude via the CLI (same pattern as the JARVIS orchestrator)."""
    import os, subprocess
    clean_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["claude", "-p", prompt, "--output-format", "text"],
            capture_output=True, text=True, timeout=120, env=clean_env,
        )
        if result.returncode != 0:
            log.error(f"Claude CLI error: {result.stderr[:200]}")
            return "[Content generation failed — check logs]"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[Content generation timed out]"
    except Exception as e:
        log.error(f"Claude error: {e}")
        return f"[Content generation unavailable: {e}]"


async def generate_newspaper(articles: list[dict]) -> str:
    """
    Generate a full multi-section broadsheet newspaper.
    Fetches topic-specific feeds and produces structured text
    with ===SECTION:..=== markers that the newspaper viewer parses.
    """
    import asyncio as _asyncio
    topic_news = await _asyncio.get_event_loop().run_in_executor(None, fetch_topic_news)

    def fmt_headlines(arts: list, n: int = 5) -> str:
        return "\n".join(f"  • {a['title']} ({a['source']})" for a in arts[:n]) or "  • [No headlines fetched]"

    today = datetime.now().strftime("%A, %d %B %Y")
    prompt = f"""You are FRIDAY, chief editor of THE GRESZ GAZETTE — GreszTech's daily broadsheet newspaper.
Today is {today}.

Write a complete newspaper edition using EXACTLY this format (section markers must match precisely):

===HEADLINE===
[One punchy, compelling main headline — the biggest story today across all topics]

===SUBHEADLINE===
[One-sentence deck below the main headline]

===EDITORIAL===
[2–3 sharp sentences: today's editorial voice — what matters, why, and what GreszTech's lens says about it]

===SECTION: AI & MACHINE INTELLIGENCE===
STORY:
[Headline]
[3–4 sentences covering the most important AI development from the headlines below. Sharp, informative, no fluff.]
SOURCE: [publication name]

STORY:
[Second AI headline]
[Body 2–3 sentences]
SOURCE: [source]

===SECTION: ONE PIECE & ANIME===
STORY:
[Headline about One Piece, manga, anime, or Oda — use the latest chapter/arc/news or a strong analytical angle]
[3–4 sentences. Could be a chapter review, theory breakdown, industry news.]
SOURCE: Shonen Jump Intelligence

STORY:
[Second anime/One Piece story]
[Body]
SOURCE: [source]

===SECTION: AUTOMATION & AGENTS===
STORY:
[Headline about AI agents, automation, n8n, workflow, or agent-building]
[3–4 sentences on automation development.]
SOURCE: [source]

STORY:
[Second automation story]
[Body]
SOURCE: [source]

===SECTION: AiOS & PERSONAL AI===
STORY:
[Headline about personal AI, JARVIS-style systems, AiOS, voice AI, or home AI]
[3–4 sentences. GreszTech AiOS perspective — how this affects personal AI builders.]
SOURCE: GreszTech Intelligence

===SECTION: LIAM OTTLEY & AI BUSINESS===
STORY:
[Headline about AI agencies, Liam Ottley, AI entrepreneurship, or the AI business landscape]
[3–4 sentences on the AI business/agency space.]
SOURCE: [source]

STORY:
[Second business/agency story]
[Body]
SOURCE: [source]

===QUOTE===
[One powerful quote — real or synthesised — relevant to today's themes. Format: "Quote text" — Attribution]

Real headlines to draw from:

AI & Tech:
{fmt_headlines(topic_news.get('ai', []))}

Automation:
{fmt_headlines(topic_news.get('automation', []))}

One Piece / Anime:
{fmt_headlines(topic_news.get('anime', []))}

AI Business / Liam Ottley:
{fmt_headlines(topic_news.get('liam', []))}

General Tech:
{fmt_headlines(topic_news.get('tech', []))}

Write tight, confident journalism. Every sentence earns its place. No filler. This is a premium publication."""

    return await _ask_claude(prompt, max_tokens=2000)


async def generate_blog_draft(title: str, notes: str = "") -> str:
    prompt = (
        f"You are a senior technology journalist writing for GreszTech's editorial blog. "
        f"Write a deep-dive blog post titled: '{title}'. "
        f"{'Context and angle: ' + notes if notes else ''} "
        f"Length: 900–1200 words. Structure: compelling lede (2-3 sentences), then 4–5 sections with "
        f"subheadings (use ## for headers). Each section should add real insight, not just overview. "
        f"Be specific, opinionated, and direct. Avoid generic advice. "
        f"End with a strong 'So What?' conclusion section. "
        f"Do NOT write a title — start with the lede paragraph."
    )
    return await _ask_claude(prompt, max_tokens=1800)


async def generate_daily_blog() -> dict:
    """Auto-generate a daily deep-dive blog on rotating topics."""
    import random, time
    existing_count = 0  # will be set by caller after checking DB
    topic_idx = datetime.now().timetuple().tm_yday % len(_BLOG_TOPICS)
    title, notes = _BLOG_TOPICS[topic_idx]
    content = await generate_blog_draft(title, notes)
    return {
        "id":      int(time.time()),
        "title":   title,
        "notes":   notes,
        "content": content,
        "status":  "published",
        "words":   len(content.split()),
        "created": datetime.utcnow().isoformat()[:10],
        "auto":    True,
    }


async def generate_social(title: str, platform: str = "twitter") -> str:
    limits = {"twitter": "280 characters", "linkedin": "3 short paragraphs", "instagram": "caption with hashtags"}
    prompt = (
        f"Write a {platform} post for: '{title}'. "
        f"Limit: {limits.get(platform, '280 characters')}. No emojis unless very natural."
    )
    return await _ask_claude(prompt, max_tokens=200)


# ── Agent ─────────────────────────────────────────────────────────────────────

class FridayAgent(BaseSpecialist):
    name = "friday"

    async def tick(self):
        self._mark_run()
        # Cache latest news in KV
        try:
            cats = await asyncio.get_event_loop().run_in_executor(
                None, fetch_all_categories, 5
            )
            for cat, articles in cats.items():
                self.set_state(f"news_{cat}", articles)
            self.set_state("news_refreshed", datetime.utcnow().isoformat())
        except Exception as e:
            log.error(f"Friday tick error: {e}")

    def _get_blogs(self) -> list:
        return self.get_state("blogs", [])

    def _save_blogs(self, blogs: list):
        self.set_state("blogs", blogs)

    async def auto_daily_newspaper(self):
        """Called by scheduler at 11:00 — generate and persist the daily paper."""
        log.info("Auto-generating daily newspaper…")
        try:
            articles = await asyncio.get_event_loop().run_in_executor(None, fetch_news, "general", 10)
            content  = await generate_newspaper(articles)
            papers   = self.get_state("papers", [])
            paper    = {
                "id":       len(papers),
                "date":     datetime.now().strftime("%d %B %Y"),
                "content":  content,
                "headline": self._extract_headline(content),
                "sources":  list({a["source"] for a in articles[:5]}),
                "sections": self._parse_sections(content),
            }
            papers.insert(0, paper)
            papers = papers[:60]
            self.set_state("papers", papers)
            self.add_log(title=f"Daily newspaper published: {paper['headline'][:50]}",
                         severity=SEVERITY_INFO, category="content")
            log.info("Daily newspaper published.")
            return paper
        except Exception as e:
            log.error(f"auto_daily_newspaper error: {e}")
            return None

    async def auto_daily_blog(self):
        """Called by scheduler at 08:30 — generate and persist a daily blog post."""
        log.info("Auto-generating daily blog post…")
        try:
            blog = await generate_daily_blog()
            blogs = self._get_blogs()
            # Don't double-generate on same day
            today = datetime.utcnow().isoformat()[:10]
            if any(b.get("created") == today and b.get("auto") for b in blogs):
                log.info("Daily blog already generated today — skipping.")
                return None
            blogs.insert(0, blog)
            self._save_blogs(blogs)
            self.add_log(title=f"Daily blog published: {blog['title'][:50]}",
                         severity=SEVERITY_INFO, category="content")
            log.info(f"Daily blog published: {blog['title']}")
            return blog
        except Exception as e:
            log.error(f"auto_daily_blog error: {e}")
            return None

    @staticmethod
    def _extract_headline(content: str) -> str:
        """Pull the headline from ===HEADLINE=== marker."""
        lines = content.split("\n")
        in_headline = False
        for line in lines:
            if line.strip() == "===HEADLINE===":
                in_headline = True
                continue
            if in_headline:
                if line.startswith("==="):
                    break
                if line.strip():
                    return line.strip()
        # Fallback: first non-empty line
        for line in lines:
            if line.strip() and not line.startswith("==="):
                return line.strip()[:120]
        return "Today's Edition"

    @staticmethod
    def _parse_sections(content: str) -> list[dict]:
        """Parse ===SECTION: title=== markers into structured sections."""
        sections = []
        current = None
        for line in content.split("\n"):
            if line.startswith("===SECTION:"):
                if current:
                    sections.append(current)
                title = line.replace("===SECTION:", "").replace("===", "").strip()
                current = {"title": title, "stories": [], "_buf": ""}
            elif line.startswith("===") and current:
                sections.append(current)
                current = None
            elif current is not None:
                current["_buf"] = current.get("_buf", "") + line + "\n"
        if current:
            sections.append(current)
        # Parse stories within each section
        for sec in sections:
            buf = sec.pop("_buf", "")
            stories = []
            for chunk in buf.split("STORY:"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                lines = [l for l in chunk.split("\n") if l.strip()]
                headline = lines[0] if lines else ""
                source = ""
                body_lines = []
                for l in lines[1:]:
                    if l.startswith("SOURCE:"):
                        source = l.replace("SOURCE:", "").strip()
                    else:
                        body_lines.append(l)
                body = " ".join(body_lines).strip()
                if headline:
                    stories.append({"headline": headline, "body": body, "source": source})
            sec["stories"] = stories
        return sections

    async def execute(self, method: str, params: dict) -> dict:

        # ── News ──────────────────────────────────────────────────────────────
        if method == "news":
            cat   = params.get("category", "general")
            count = int(params.get("count", 8))
            cached = self.get_state(f"news_{cat}")
            refreshed = self.get_state("news_refreshed", "")
            if cached and refreshed:
                age_mins = (datetime.utcnow() - datetime.fromisoformat(refreshed)).total_seconds() / 60
                if age_mins < 30:
                    return {"category": cat, "articles": cached[:count], "cached": True}
            articles = await asyncio.get_event_loop().run_in_executor(None, fetch_news, cat, count)
            self.set_state(f"news_{cat}", articles)
            self.set_state("news_refreshed", datetime.utcnow().isoformat())
            return {"category": cat, "articles": articles}

        if method == "news_all":
            cats = await asyncio.get_event_loop().run_in_executor(None, fetch_all_categories, 5)
            return {"categories": cats}

        # ── Newspaper generation ──────────────────────────────────────────────
        if method == "generate_paper":
            paper = await self.auto_daily_newspaper()
            if not paper:
                return {"error": "Generation failed"}
            return {"paper": paper}

        if method == "papers_get":
            return {"papers": self.get_state("papers", [])}

        # ── Blog posts ────────────────────────────────────────────────────────
        if method == "blogs_get":
            return {"blogs": self._get_blogs()}

        if method == "blog_get":
            bid   = params.get("id")
            blogs = self._get_blogs()
            blog  = next((b for b in blogs if b["id"] == bid), None)
            return {"blog": blog} if blog else {"error": "not found"}

        if method == "blog_add":
            title   = params.get("title", "Untitled")
            notes   = params.get("notes", "")
            content = params.get("content", "")
            import time
            blog = {
                "id":      int(time.time()),
                "title":   title,
                "notes":   notes,
                "content": content,
                "status":  "draft",
                "words":   len(content.split()) if content else 0,
                "created": datetime.utcnow().isoformat()[:10],
            }
            blogs = self._get_blogs()
            blogs.insert(0, blog)
            self._save_blogs(blogs)
            return {"blog": blog}

        if method == "blog_update":
            bid   = params.get("id")
            blogs = self._get_blogs()
            for b in blogs:
                if b["id"] == bid:
                    for k, v in params.items():
                        if k != "id":
                            b[k] = v
                    if "content" in params:
                        b["words"] = len(params["content"].split())
            self._save_blogs(blogs)
            return {"blogs": blogs}

        if method == "blog_delete":
            bid   = params.get("id")
            blogs = [b for b in self._get_blogs() if b["id"] != bid]
            self._save_blogs(blogs)
            return {"blogs": blogs}

        if method == "blog_generate":
            title   = params.get("title", "Untitled Post")
            notes   = params.get("notes", "")
            content = await generate_blog_draft(title, notes)
            import time
            blog = {
                "id":      int(time.time()),
                "title":   title,
                "notes":   notes,
                "content": content,
                "status":  "draft",
                "words":   len(content.split()),
                "created": datetime.utcnow().isoformat()[:10],
            }
            blogs = self._get_blogs()
            blogs.insert(0, blog)
            self._save_blogs(blogs)
            self.add_log(title=f"Blog draft generated: {title[:40]}", severity=SEVERITY_INFO, category="content")
            return {"blog": blog}

        if method == "daily_blog":
            blog = await self.auto_daily_blog()
            return {"blog": blog} if blog else {"message": "Already generated today"}

        # ── Social ────────────────────────────────────────────────────────────
        if method == "social":
            title    = params.get("title", "")
            platform = params.get("platform", "twitter")
            text     = await generate_social(title, platform)
            return {"platform": platform, "text": text}

        # ── Voice command routing ─────────────────────────────────────────────
        if method == "command":
            text  = params.get("text", "")
            lower = text.lower().strip()

            # ── Category news ─────────────────────────────────────────────────
            # "tech news" / "show me business headlines" / "latest AI news"
            cat_map = {
                "tech": "tech", "technology": "tech", "ai": "tech",
                "business": "business", "finance": "business",
                "science": "science",
                "general": "general", "world": "general",
            }
            for word, cat in cat_map.items():
                if word in lower and any(k in lower for k in ("news", "headlines", "stories", "latest")):
                    result = await self.execute("news", {"category": cat, "count": 5})
                    arts   = result.get("articles", [])
                    if not arts:
                        return {"message": f"No {cat} news available right now."}
                    return {"message": f"Top {cat} headlines: " + "; ".join(a['title'] for a in arts[:3])}

            # generic news
            if any(k in lower for k in ("news", "headlines", "latest")):
                result = await self.execute("news", {"category": "general", "count": 5})
                arts   = result.get("articles", [])
                if not arts:
                    return {"message": "No news available right now."}
                return {"message": "Today's headlines: " + "; ".join(a['title'] for a in arts[:3])}

            # ── Newspaper ─────────────────────────────────────────────────────
            if any(k in lower for k in ("paper", "newspaper", "gazette", "today's edition", "generate paper")):
                if any(k in lower for k in ("generate", "create", "make", "publish", "write")):
                    result = await self.execute("generate_paper", {})
                    paper  = result.get("paper", {})
                    return {"message": f"Publishing today's Gazette. Leading with: {paper.get('headline', 'edition complete')}."}
                papers = self.get_state("papers", [])
                if papers:
                    return {"message": f"Latest edition: {papers[0].get('date','')}. Leading with: {papers[0].get('headline','')[:120]}"}
                return {"message": "No editions yet. Say 'generate newspaper' to publish today's Gazette."}

            # ── Blog ──────────────────────────────────────────────────────────
            # "write a blog about AI agents" / "draft a post on One Piece"
            import re as _re
            m = _re.search(r'(?:write|draft|create|generate)\s+(?:a\s+)?(?:blog|post|article)\s+(?:about|on|covering)?\s*(.+)', lower)
            if m:
                title  = m.group(1).strip().title()
                result = await self.execute("blog_generate", {"title": title})
                return {"message": f"Blog draft ready: {result['blog']['title']}. Open Friday to read it."}

            # "show blogs" / "my posts" / "blog archive"
            if any(k in lower for k in ("blog", "post", "article", "archive")):
                blogs = self._get_blogs()
                if not blogs:
                    return {"message": "No blog posts yet. Say 'write a blog about X' to start."}
                latest = blogs[:3]
                return {"message": f"{len(blogs)} posts in the archive. Latest: " + "; ".join(b['title'] for b in latest)}

            # ── Daily blog ────────────────────────────────────────────────────
            if any(k in lower for k in ("daily blog", "auto blog", "generate blog")):
                result = await self.execute("daily_blog", {})
                if result.get("blog"):
                    return {"message": f"Daily blog published: {result['blog']['title']}"}
                return {"message": "Daily blog already generated for today."}

            return {"message": "Ask me for news, to generate today's newspaper, or to write a blog post on any topic."}

        return {"error": f"Unknown method: {method}"}
