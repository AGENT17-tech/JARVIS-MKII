"""
gmail_sensor.py — JARVIS MKIII Gmail Sensor
Monitors inbox for unread, urgent, and important emails.
Updates world state every 5 minutes.

Setup:
    1. Go to console.cloud.google.com
    2. Create project → Enable Gmail API
    3. Create OAuth2 credentials → Download as credentials.json
    4. Place credentials.json in ~/.jarvis/
    5. Run once manually to authenticate: python3 gmail_sensor.py
"""

import asyncio
import os
import json
from datetime import datetime

CREDENTIALS_PATH = os.path.expanduser("~/.jarvis/gmail_credentials.json")
TOKEN_PATH       = os.path.expanduser("~/.jarvis/gmail_token.json")
SCOPES           = ["https://www.googleapis.com/auth/gmail.readonly"]

# Keywords that mark an email as urgent
URGENT_KEYWORDS = [
    "urgent", "asap", "deadline", "important", "critical",
    "exam", "grade", "professor", "assignment due", "overdue",
    "faculty", "university", "buc",
]


class GmailSensor:
    def __init__(self):
        self._service = None
        self._available = False
        self._login_tried = False
        print("[GMAIL SENSOR] Initialized.")

    def _authenticate(self):
        self._login_tried = True
        """Authenticate with Gmail API."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            creds = None
            if os.path.exists(TOKEN_PATH):
                creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(CREDENTIALS_PATH):
                        print("[GMAIL SENSOR] credentials.json not found — skipping.")
                        return False
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_PATH, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())

            self._service  = build("gmail", "v1", credentials=creds)
            self._available = True
            print("[GMAIL SENSOR] Authenticated successfully.")
            return True
        except Exception as e:
            print(f"[GMAIL SENSOR] Auth error: {e}")
            return False

    def _is_urgent(self, subject: str, snippet: str) -> bool:
        text = (subject + " " + snippet).lower()
        return any(kw in text for kw in URGENT_KEYWORDS)

    async def read(self) -> dict:
        """Read inbox and return world state update."""
        if not self._available and not self._login_tried:
            self._authenticate()
        if not self._available and not self._login_tried:
            return {}

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_emails)
            return result
        except Exception as e:
            print(f"[GMAIL SENSOR] Read error: {e}")
            return {}

    def _fetch_emails(self) -> dict:
        """Synchronous Gmail fetch — run in executor."""
        try:
            # Get unread emails
            results = self._service.users().messages().list(
                userId="me", q="is:unread", maxResults=20
            ).execute()

            messages   = results.get("messages", [])
            unread     = len(messages)
            urgent     = 0
            summaries  = []

            for msg in messages[:5]:
                detail = self._service.users().messages().get(
                    userId="me", id=msg["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From"]
                ).execute()

                headers = {h["name"]: h["value"]
                           for h in detail.get("payload", {}).get("headers", [])}
                subject = headers.get("Subject", "No subject")
                sender  = headers.get("From", "Unknown")
                snippet = detail.get("snippet", "")

                if self._is_urgent(subject, snippet):
                    urgent += 1

                summaries.append(f"{sender}: {subject}")

            summary = summaries[0] if summaries else ""

            return {
                "email": {
                    "unread":  unread,
                    "urgent":  urgent,
                    "summary": summary,
                }
            }
        except Exception as e:
            print(f"[GMAIL SENSOR] Fetch error: {e}")
            return {}


# ── Singleton ─────────────────────────────────────────────────────────
gmail_sensor = GmailSensor()

if __name__ == "__main__":
    async def test():
        print("[TEST] Gmail sensor...")
        result = await gmail_sensor.read()
        if result:
            email = result.get("email", {})
            print(f"Unread:  {email.get('unread', 0)}")
            print(f"Urgent:  {email.get('urgent', 0)}")
            print(f"Summary: {email.get('summary', '')}")
            print("[TEST] Gmail PASS")
        else:
            print("[TEST] Gmail not configured — skipped (add credentials.json to ~/.jarvis/)")
    asyncio.run(test())
