"""
ULTRON — Security specialist agent (Layer 2).

Capabilities (Phase 1):
  - Domain/IP threat scan: DNS, geo, SSL cert info, blacklist checks
  - HaveIBeenPwned breach lookup (email)
  - Passive recon: WHOIS-style data via DNS + ipinfo.io (no API key needed)
  - Watchlist monitoring: periodic scans of saved targets
  - Exposure log stored in SQLite via BaseSpecialist
"""
import asyncio
import ipaddress
import json
import logging
import re
import socket
import ssl
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from agents.base_specialist import BaseSpecialist, SEVERITY_INFO, SEVERITY_WATCH, SEVERITY_ALERT, SEVERITY_RESOLVED

log = logging.getLogger("jarvis.ultron")

# Free / no-auth APIs
_IPINFO_URL  = "https://ipinfo.io/{ip}/json"
_HIBP_URL    = "https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
_ABUSEIPDB   = "https://api.abuseipdb.com/api/v2/check"   # needs key — skipped if absent
_DNS_BLOCKLIST = [
    "zen.spamhaus.org",
    "bl.spamcop.net",
    "dnsbl.sorbs.net",
]

_HTTP_TIMEOUT = 8


def _http_get(url: str, headers: dict = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {
        "User-Agent": "JARVIS-Ultron/1.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}


def _resolve_target(target: str) -> tuple[str, str]:
    """Return (ip, kind) where kind is 'domain' or 'ip'."""
    target = target.strip().lower()
    target = re.sub(r"^https?://", "", target).split("/")[0]
    try:
        ipaddress.ip_address(target)
        return target, "ip"
    except ValueError:
        pass
    try:
        ip = socket.gethostbyname(target)
        return ip, "domain"
    except Exception:
        return "", "domain"


def _check_dnsbl(ip: str) -> list[str]:
    """Check IP against DNS blocklists. Returns list of hit blocklist names."""
    if not ip:
        return []
    rev = ".".join(reversed(ip.split(".")))
    hits = []
    for bl in _DNS_BLOCKLIST:
        try:
            socket.gethostbyname(f"{rev}.{bl}")
            hits.append(bl)
        except socket.gaierror:
            pass  # NXDOMAIN = not listed
        except Exception:
            pass
    return hits


def _get_ssl_info(domain: str) -> dict:
    """Grab SSL cert metadata."""
    try:
        ctx = ssl.create_default_context()
        conn = ctx.wrap_socket(
            socket.create_connection((domain, 443), timeout=6),
            server_hostname=domain,
        )
        cert = conn.getpeercert()
        conn.close()
        # Parse expiry
        expires_str = cert.get("notAfter", "")
        expires = None
        if expires_str:
            expires = datetime.strptime(expires_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        issuer = dict(x[0] for x in cert.get("issuer", []))
        subject = dict(x[0] for x in cert.get("subject", []))
        days_left = (expires - datetime.now(timezone.utc)).days if expires else None
        return {
            "valid": True,
            "issuer": issuer.get("organizationName", "Unknown"),
            "cn": subject.get("commonName", domain),
            "expires": expires_str,
            "days_left": days_left,
        }
    except ssl.SSLCertVerificationError as e:
        return {"valid": False, "error": str(e)}
    except Exception as e:
        return {"valid": None, "error": str(e)}


def _get_dns_records(domain: str) -> dict:
    """Basic DNS resolution."""
    results = {}
    try:
        results["A"] = socket.gethostbyname_ex(domain)[2]
    except Exception:
        results["A"] = []
    # MX via nslookup fallback (no dnspython needed)
    try:
        import subprocess
        out = subprocess.check_output(["nslookup", "-type=MX", domain],
                                      timeout=5, stderr=subprocess.DEVNULL).decode()
        mx = re.findall(r"mail exchanger = (.+)", out)
        results["MX"] = [m.strip() for m in mx]
    except Exception:
        results["MX"] = []
    return results


def _geo_ip(ip: str) -> dict:
    """Get geo/org info for an IP from ipinfo.io (free, no key needed for light use)."""
    if not ip:
        return {}
    data = _http_get(_IPINFO_URL.format(ip=ip))
    return {
        "country": data.get("country", "?"),
        "region":  data.get("region", "?"),
        "city":    data.get("city", "?"),
        "org":     data.get("org", "?"),
        "timezone":data.get("timezone", "?"),
        "bogon":   data.get("bogon", False),
    }


def _is_private_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except Exception:
        return False


def scan_target(target: str) -> dict:
    """
    Full synchronous scan of a domain or IP.
    Returns a structured results dict suitable for JSON serialisation.
    """
    raw = target.strip()
    ip, kind = _resolve_target(raw)

    result = {
        "target":  raw,
        "kind":    kind,
        "ip":      ip,
        "ts":      datetime.utcnow().isoformat(),
        "threats": [],
        "checks":  {},
    }

    if not ip:
        result["error"] = "Could not resolve target"
        return result

    if _is_private_ip(ip):
        result["private"] = True
        result["checks"]["geo"] = {"note": "Private/internal IP — no geo data"}
        return result

    # Geo
    geo = _geo_ip(ip)
    result["checks"]["geo"] = geo
    if geo.get("bogon"):
        result["threats"].append("Bogon/reserved IP range")

    # DNSBL
    hits = _check_dnsbl(ip)
    result["checks"]["dnsbl"] = {"hit": bool(hits), "lists": hits}
    for h in hits:
        result["threats"].append(f"Blacklisted on {h}")

    # DNS records (domains only)
    if kind == "domain":
        result["checks"]["dns"] = _get_dns_records(raw)
        ssl_info = _get_ssl_info(raw)
        result["checks"]["ssl"] = ssl_info
        if ssl_info.get("valid") is False:
            result["threats"].append("SSL certificate invalid or untrusted")
        elif ssl_info.get("days_left") is not None and ssl_info["days_left"] < 14:
            result["threats"].append(f"SSL certificate expires in {ssl_info['days_left']} days")

    result["safe"] = len(result["threats"]) == 0
    result["risk"] = "clean" if result["safe"] else ("high" if len(result["threats"]) >= 2 else "medium")
    return result


def check_email_breach(email: str, api_key: str = "") -> dict:
    """
    Check email against HaveIBeenPwned.
    Requires an HIBP API key (v3). Returns breach list or error.
    """
    if not api_key:
        return {"error": "HIBP API key not configured", "breaches": []}
    url = _HIBP_URL.format(email=email)
    data = _http_get(url, headers={
        "hibp-api-key": api_key,
        "User-Agent": "JARVIS-Ultron/1.0",
    })
    if "_error" in data:
        # 404 = not found (good news)
        if "404" in data["_error"] or "HTTP Error 404" in data["_error"]:
            return {"email": email, "breaches": [], "pwned": False}
        return {"error": data["_error"], "breaches": []}
    breaches = [{"name": b.get("Name"), "date": b.get("BreachDate"),
                 "count": b.get("PwnCount")} for b in (data if isinstance(data, list) else [])]
    return {"email": email, "breaches": breaches, "pwned": bool(breaches)}


class UltronAgent(BaseSpecialist):
    name = "ultron"

    async def tick(self):
        """Periodic watchlist scan."""
        self._mark_run()
        watchlist = self.get_state("watchlist", [])
        if not watchlist:
            return
        for target in watchlist:
            result = await asyncio.get_event_loop().run_in_executor(
                None, scan_target, target
            )
            if not result.get("safe"):
                threats = result.get("threats", [])
                existing = self._db.execute(
                    "SELECT id FROM logs WHERE title=? AND status='open'",
                    (f"Threat detected: {target}",)
                ).fetchone()
                if not existing:
                    self.add_log(
                        title=f"Threat detected: {target}",
                        detail="\n".join(threats),
                        severity=SEVERITY_ALERT,
                        category="watchlist",
                    )
                    log.warning(f"ULTRON watchlist alert: {target} — {threats}")

    async def execute(self, method: str, params: dict) -> dict:
        if method == "scan":
            target = params.get("target", "")
            if not target:
                return {"error": "target required"}
            result = await asyncio.get_event_loop().run_in_executor(
                None, scan_target, target
            )
            # Log to exposure log if threats found
            if not result.get("safe"):
                self.add_log(
                    title=f"Threats found: {target}",
                    detail="\n".join(result.get("threats", [])),
                    severity=SEVERITY_ALERT,
                    category="scan",
                    url=f"https://{target}" if result.get("kind") == "domain" else "",
                )
            return result

        if method == "breach":
            email = params.get("email", "")
            from core.config import env
            key = env("HIBP_API_KEY", "")
            return check_email_breach(email, key)

        if method == "watchlist_add":
            target = params.get("target", "")
            wl = self.get_state("watchlist", [])
            if target and target not in wl:
                wl.append(target)
                self.set_state("watchlist", wl)
                self.add_log(title=f"Added to watchlist: {target}", severity=SEVERITY_INFO, category="watchlist")
            return {"watchlist": wl}

        if method == "watchlist_remove":
            target = params.get("target", "")
            wl = [t for t in self.get_state("watchlist", []) if t != target]
            self.set_state("watchlist", wl)
            return {"watchlist": wl}

        if method == "watchlist_get":
            return {"watchlist": self.get_state("watchlist", [])}

        if method == "command":
            text  = params.get("text", "")
            lower = text.lower().strip()

            # ── Scan target ───────────────────────────────────────────────────
            # "scan google.com" / "check google.com" / "analyse 1.2.3.4"
            m = re.search(
                r'(?:scan|check|analyse|analyze|look up|lookup)\s+([\w.\-]+\.[a-z]{2,}|\d{1,3}(?:\.\d{1,3}){3})',
                lower
            )
            if m:
                return await self.execute("scan", {"target": m.group(1)})

            # bare domain/IP with no verb
            m = re.match(r'^([\w.\-]+\.[a-z]{2,}|\d{1,3}(?:\.\d{1,3}){3})$', lower)
            if m:
                return await self.execute("scan", {"target": m.group(1)})

            # ── Watchlist ─────────────────────────────────────────────────────
            # "add google.com to watchlist" / "watch cloudflare.com"
            m = re.search(
                r'(?:add|watch|monitor)\s+([\w.\-]+\.[a-z]{2,})',
                lower
            )
            if m:
                target = m.group(1)
                wl = self.get_state("watchlist", [])
                if target not in wl:
                    wl.append(target)
                    self.set_state("watchlist", wl)
                return {"message": f"Added {target} to the watchlist. Now monitoring {len(wl)} target{'s' if len(wl)!=1 else ''}."}

            # "remove google.com from watchlist"
            m = re.search(r'(?:remove|stop watching|unwatch)\s+([\w.\-]+\.[a-z]{2,})', lower)
            if m:
                target = m.group(1)
                wl = [t for t in self.get_state("watchlist", []) if t != target]
                self.set_state("watchlist", wl)
                return {"message": f"Removed {target} from the watchlist."}

            # ── Breach check ──────────────────────────────────────────────────
            # "check evan@gresz.io for breaches" / "has X been pwned"
            m = re.search(r'([\w.\-+]+@[\w.\-]+\.[a-z]{2,})', lower)
            if m and any(k in lower for k in ("breach", "pwned", "hacked", "check", "email")):
                return await self.execute("breach", {"email": m.group(1)})

            # ── Status / logs ─────────────────────────────────────────────────
            if any(k in lower for k in ("threat", "alert", "log", "status", "report", "overview", "any issues")):
                logs    = self.get_logs(limit=5, severity="alert")
                wl      = self.get_state("watchlist", [])
                open_t  = [l for l in logs if l.get("status") == "open"]
                if open_t:
                    lines = [f"• {l['title']}" for l in open_t[:3]]
                    return {"message": f"I have {len(open_t)} open threat{'s' if len(open_t)!=1 else ''}: " + "; ".join(lines)}
                return {"message": f"All clear. Monitoring {len(wl)} target{'s' if len(wl)!=1 else ''} on the watchlist. No open threats."}

            # ── Watchlist status ──────────────────────────────────────────────
            if any(k in lower for k in ("watchlist", "what am i watching", "targets")):
                wl = self.get_state("watchlist", [])
                if not wl:
                    return {"message": "The watchlist is empty. Say 'watch domain.com' to add a target."}
                return {"message": f"Watchlist has {len(wl)} target{'s' if len(wl)!=1 else ''}: " + ", ".join(wl[:5])}

            return {"message": "Tell me a domain or IP to scan, an email to check for breaches, or say 'watchlist' for status."}

        return {"error": f"Unknown method: {method}"}
