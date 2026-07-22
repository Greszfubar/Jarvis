"""
GRESZ INDUSTRIES — Business AiOS specialist agent (Layer 2).

Capabilities (Phase 4):
  - Project tracker: CRUD with status, progress, due dates
  - Client roster: stored in SQLite KV
  - Sales pipeline: deal tracking by stage
  - KPI snapshots: revenue, tasks, pipeline totals
  - Business briefing: Claude-generated executive summary
"""
import asyncio
import logging
from datetime import datetime

from agents.base_specialist import BaseSpecialist, SEVERITY_INFO, SEVERITY_WATCH
from core.config import env

log = logging.getLogger("jarvis.gresz")


async def _ask_claude(prompt: str, max_tokens: int = 600) -> str:
    """Call Claude via the CLI (same pattern as the JARVIS orchestrator)."""
    import asyncio, os, subprocess
    clean_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["claude", "-p", prompt, "--output-format", "text"],
            capture_output=True, text=True, timeout=90, env=clean_env,
        )
        if result.returncode != 0:
            log.error(f"Claude CLI error: {result.stderr[:200]}")
            return "[Briefing generation failed — check logs]"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[Briefing timed out]"
    except Exception as e:
        return f"[Briefing unavailable: {e}]"


class GreszAgent(BaseSpecialist):
    name = "gresz"

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _projects(self): return self.get_state("projects", [])
    def _clients(self):  return self.get_state("clients", [])
    def _pipeline(self): return self.get_state("pipeline", [])

    def _save_projects(self, d): self.set_state("projects", d)
    def _save_clients(self, d):  self.set_state("clients", d)
    def _save_pipeline(self, d): self.set_state("pipeline", d)

    def _kpis(self) -> dict:
        projects  = self._projects()
        clients   = self._clients()
        pipeline  = self._pipeline()
        active    = [p for p in projects if p.get("status") == "active"]
        overdue   = [p for p in projects if p.get("overdue")]
        pipe_val  = sum(self._parse_value(d.get("value","0")) for d in pipeline)
        return {
            "active_projects": len(active),
            "total_clients":   len([c for c in clients if c.get("tier") != "PROSPECT"]),
            "pipeline_value":  f"${pipe_val:,.0f}",
            "open_tasks":      sum(p.get("open_tasks", 0) for p in projects),
            "overdue":         len(overdue),
        }

    @staticmethod
    def _parse_value(s: str) -> float:
        import re
        nums = re.findall(r"[\d,.]+", str(s).replace(",", ""))
        return float(nums[0]) if nums else 0.0

    # ── Tick ─────────────────────────────────────────────────────────────────

    async def tick(self):
        self._mark_run()
        # Flag overdue projects
        projects = self._projects()
        today = datetime.now()
        for p in projects:
            due = p.get("due", "")
            if not due or due == "TBD":
                continue
            try:
                due_dt = datetime.strptime(due, "%b %d, %Y")
                if due_dt < today and p.get("status") == "active":
                    p["overdue"] = True
                    existing = self._db.execute(
                        "SELECT id FROM logs WHERE title=? AND status='open'",
                        (f"Overdue: {p['name']}",)
                    ).fetchone()
                    if not existing:
                        self.add_log(
                            title=f"Overdue: {p['name']}",
                            detail=f"Due {due} — still active",
                            severity=SEVERITY_WATCH,
                            category="projects",
                        )
            except Exception:
                pass
        self._save_projects(projects)

    # ── Execute ───────────────────────────────────────────────────────────────

    async def execute(self, method: str, params: dict) -> dict:

        # ── KPIs ──────────────────────────────────────────────────────────────
        if method == "kpis":
            return self._kpis()

        # ── Projects ──────────────────────────────────────────────────────────
        if method == "projects_get":
            return {"projects": self._projects()}

        if method == "project_add":
            p = {
                "id":         int(datetime.utcnow().timestamp()),
                "name":       params.get("name", "New Project"),
                "client":     params.get("client", "Internal"),
                "status":     params.get("status", "active"),
                "progress":   int(params.get("progress", 0)),
                "due":        params.get("due", "TBD"),
                "notes":      params.get("notes", ""),
                "open_tasks": 0,
                "overdue":    False,
            }
            projects = self._projects()
            projects.insert(0, p)
            self._save_projects(projects)
            self.add_log(title=f"New project: {p['name']}", severity=SEVERITY_INFO, category="projects")
            return {"project": p}

        if method == "project_update":
            pid      = params.get("id")
            projects = self._projects()
            for p in projects:
                if p["id"] == pid:
                    for k, v in params.items():
                        if k != "id":
                            p[k] = v
            self._save_projects(projects)
            return {"projects": projects}

        if method == "project_delete":
            pid      = params.get("id")
            projects = [p for p in self._projects() if p["id"] != pid]
            self._save_projects(projects)
            return {"projects": projects}

        # ── Clients ───────────────────────────────────────────────────────────
        if method == "clients_get":
            return {"clients": self._clients()}

        if method == "client_add":
            c = {
                "id":     int(datetime.utcnow().timestamp()),
                "name":   params.get("name", "New Client"),
                "tier":   params.get("tier", "PROSPECT"),
                "value":  params.get("value", "—"),
                "email":  params.get("email", ""),
                "notes":  params.get("notes", ""),
                "avatar": (params.get("name","?")[0]).upper(),
            }
            clients = self._clients()
            clients.insert(0, c)
            self._save_clients(clients)
            return {"client": c}

        if method == "client_update":
            cid     = params.get("id")
            clients = self._clients()
            for c in clients:
                if c["id"] == cid:
                    for k, v in params.items():
                        if k != "id":
                            c[k] = v
            self._save_clients(clients)
            return {"clients": clients}

        if method == "client_delete":
            cid     = params.get("id")
            clients = [c for c in self._clients() if c["id"] != cid]
            self._save_clients(clients)
            return {"clients": clients}

        # ── Pipeline ──────────────────────────────────────────────────────────
        if method == "pipeline_get":
            return {"pipeline": self._pipeline()}

        if method == "deal_add":
            d = {
                "id":      int(datetime.utcnow().timestamp()),
                "company": params.get("company", "New Deal"),
                "value":   params.get("value", "$0"),
                "stage":   params.get("stage", "lead"),
                "notes":   params.get("notes", ""),
                "contact": params.get("contact", ""),
            }
            pipeline = self._pipeline()
            pipeline.insert(0, d)
            self._save_pipeline(pipeline)
            return {"deal": d}

        if method == "deal_update":
            did      = params.get("id")
            pipeline = self._pipeline()
            for d in pipeline:
                if d["id"] == did:
                    for k, v in params.items():
                        if k != "id":
                            d[k] = v
            self._save_pipeline(pipeline)
            return {"pipeline": pipeline}

        if method == "deal_delete":
            did      = params.get("id")
            pipeline = [d for d in self._pipeline() if d["id"] != did]
            self._save_pipeline(pipeline)
            return {"pipeline": pipeline}

        # ── Business briefing ─────────────────────────────────────────────────
        if method == "briefing":
            kpis     = self._kpis()
            projects = self._projects()
            pipeline = self._pipeline()
            active   = [p for p in projects if p.get("status") == "active"]
            closing  = [d for d in pipeline if d.get("stage") == "closing"]
            prompt = (
                f"You are GRESZ, an AI business intelligence agent. "
                f"Today is {datetime.now().strftime('%A, %d %B %Y')}. "
                f"Generate a concise executive briefing (3–4 sentences) covering:\n"
                f"- {kpis['active_projects']} active projects, {kpis['overdue']} overdue\n"
                f"- {kpis['total_clients']} active clients\n"
                f"- Pipeline: {kpis['pipeline_value']}, {len(closing)} deals closing\n"
                f"Active projects: {', '.join(p['name'] for p in active[:5])}\n"
                f"Be direct and actionable. No fluff."
            )
            text = await _ask_claude(prompt, max_tokens=300)
            return {"briefing": text}

        # ── Voice command ─────────────────────────────────────────────────────
        if method == "command":
            text  = params.get("text", "")
            lower = text.lower().strip()

            # ── Projects ──────────────────────────────────────────────────────
            if any(k in lower for k in ("project", "active", "overdue", "work", "task")):
                ps = self._projects()
                if not ps:
                    return {"message": "No projects tracked yet."}
                active  = [p for p in ps if p.get("status") == "active"]
                overdue = [p for p in ps if p.get("overdue")]
                o_str   = f", {len(overdue)} overdue" if overdue else ""
                names   = ", ".join(p['name'] for p in active[:3])
                return {"message": f"{len(active)} active project{'s' if len(active)!=1 else ''}{o_str}: {names}."}

            # ── Pipeline / deals ──────────────────────────────────────────────
            if any(k in lower for k in ("pipeline", "deal", "sales", "revenue", "closing")):
                deals = self._pipeline()
                if not deals:
                    return {"message": "No deals in the pipeline."}
                pipe_v = sum(self._parse_value(d.get("value","0")) for d in deals)
                closing = [d for d in deals if d.get("stage") == "closing"]
                c_str = f" {len(closing)} closing" if closing else ""
                return {"message": f"Pipeline: ${pipe_v:,.0f} across {len(deals)} deal{'s' if len(deals)!=1 else ''}{c_str}. Leads: " + ", ".join(d['company'] for d in deals[:3])}

            # ── Clients ───────────────────────────────────────────────────────
            if any(k in lower for k in ("client", "account", "customer")):
                clients = self._clients()
                active_c = [c for c in clients if c.get("tier") not in ("PROSPECT","")]
                if not clients:
                    return {"message": "No clients on file yet."}
                return {"message": f"{len(active_c)} active client{'s' if len(active_c)!=1 else ''} and {len(clients)-len(active_c)} prospects: " + ", ".join(c['name'] for c in clients[:4])}

            # ── KPIs / overview ───────────────────────────────────────────────
            if any(k in lower for k in ("kpi", "overview", "summary", "numbers", "how are we", "status")):
                kpis = self._kpis()
                return {"message": (
                    f"GreszTech status: {kpis['active_projects']} active projects, "
                    f"{kpis['total_clients']} clients, "
                    f"pipeline at {kpis['pipeline_value']}."
                    + (f" Warning: {kpis['overdue']} overdue." if kpis.get('overdue') else "")
                )}

            # ── Briefing ──────────────────────────────────────────────────────
            if any(k in lower for k in ("brief", "briefing", "executive", "report", "tell me everything")):
                result = await self.execute("briefing", {})
                return {"message": result.get("briefing", "Briefing unavailable.")}

            return {"message": "Ask me about projects, clients, the pipeline, KPIs, or request a business briefing."}

        return {"error": f"Unknown method: {method}"}
