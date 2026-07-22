"""GmailAgent — read, summarize, draft, and send email via Gmail API."""
import asyncio
import base64
import logging
import os
from email.mime.text import MIMEText
from pathlib import Path

from agents.base import BaseAgent
from core.config import env
from core.memory import Memory

log = logging.getLogger("jarvis.gmail")
mem = Memory()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def _get_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import googleapiclient.discovery

    token_path = Path("config/gmail_token.json")
    creds_path = Path(env("GOOGLE_CREDENTIALS_PATH", "config/google_credentials.json"))
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return googleapiclient.discovery.build("gmail", "v1", credentials=creds)


class GmailAgent(BaseAgent):
    name = "gmail"

    def tools(self):
        return [
            self._tool("get_unread", "Get unread emails summary.", {
                "max_results": {"type": "integer", "description": "Max emails to fetch (default 10)"},
            }),
            self._tool("search_email", "Search emails by query.", {
                "query": {"type": "string", "description": "Gmail search query e.g. 'from:boss@corp.com'"},
                "max_results": {"type": "integer"},
            }, required=["query"]),
            self._tool("send_email", "Send an email.", {
                "to":      {"type": "string"},
                "subject": {"type": "string"},
                "body":    {"type": "string"},
            }, required=["to", "subject", "body"]),
            self._tool("mark_read", "Mark an email as read by message ID.", {
                "message_id": {"type": "string"},
            }, required=["message_id"]),
        ]

    async def execute(self, method: str, params: dict):
        if method == "get_unread":
            return await asyncio.to_thread(self._get_unread, params.get("max_results", 10))
        if method == "search_email":
            return await asyncio.to_thread(self._search, params["query"], params.get("max_results", 10))
        if method == "send_email":
            return await asyncio.to_thread(self._send, params["to"], params["subject"], params["body"])
        if method == "mark_read":
            return await asyncio.to_thread(self._mark_read, params["message_id"])
        return {"error": f"Unknown method: {method}"}

    def _get_unread(self, max_results: int) -> dict:
        try:
            svc = _get_service()
            result = svc.users().messages().list(
                userId="me", q="is:unread", maxResults=max_results
            ).execute()
            messages = result.get("messages", [])
            emails = []
            for msg in messages:
                data = svc.users().messages().get(userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["Subject", "From", "Date"]).execute()
                headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
                emails.append({
                    "id": msg["id"],
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "date": headers.get("Date", ""),
                    "snippet": data.get("snippet", ""),
                })
            mem.set_fact("gmail_unread_count", len(emails))
            return {"unread_count": len(emails), "emails": emails}
        except Exception as e:
            log.error(f"Gmail unread error: {e}")
            return {"error": str(e)}

    def _search(self, query: str, max_results: int) -> dict:
        try:
            svc = _get_service()
            result = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = result.get("messages", [])
            emails = []
            for msg in messages:
                data = svc.users().messages().get(userId="me", id=msg["id"], format="metadata",
                    metadataHeaders=["Subject", "From", "Date"]).execute()
                headers = {h["name"]: h["value"] for h in data["payload"]["headers"]}
                emails.append({
                    "id": msg["id"],
                    "from": headers.get("From", ""),
                    "subject": headers.get("Subject", ""),
                    "date": headers.get("Date", ""),
                    "snippet": data.get("snippet", ""),
                })
            return {"query": query, "count": len(emails), "emails": emails}
        except Exception as e:
            return {"error": str(e)}

    def _send(self, to: str, subject: str, body: str) -> dict:
        try:
            svc = _get_service()
            msg = MIMEText(body)
            msg["to"] = to
            msg["subject"] = subject
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            svc.users().messages().send(userId="me", body={"raw": raw}).execute()
            return {"status": "sent", "to": to, "subject": subject}
        except Exception as e:
            return {"error": str(e)}

    def _mark_read(self, message_id: str) -> dict:
        try:
            svc = _get_service()
            svc.users().messages().modify(
                userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            return {"status": "marked_read", "id": message_id}
        except Exception as e:
            return {"error": str(e)}

    async def tick(self):
        """Alert on new important emails."""
        try:
            result = await asyncio.to_thread(self._get_unread, 5)
            count = result.get("unread_count", 0)
            prev = mem.get_fact("gmail_unread_prev", 0)
            if count > prev:
                from core.bus import bus
                await bus.publish("gmail.new", {
                    "new_count": count - prev,
                    "emails": result.get("emails", [])[:3],
                })
            mem.set_fact("gmail_unread_prev", count)
        except Exception as e:
            log.warning(f"Gmail tick: {e}")
