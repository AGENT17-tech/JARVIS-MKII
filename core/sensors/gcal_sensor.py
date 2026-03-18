"""
gcal_sensor.py — JARVIS MKIII Google Calendar Sensor
Monitors events for today and next 7 days.
Detects upcoming exams and deadlines.

Setup: Same OAuth2 credentials as Gmail.
Place credentials.json in ~/.jarvis/
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone

CREDENTIALS_PATH = os.path.expanduser("~/.jarvis/gmail_credentials.json")
TOKEN_PATH       = os.path.expanduser("~/.jarvis/gcal_token.json")
SCOPES           = ["https://www.googleapis.com/auth/calendar.readonly"]

EXAM_KEYWORDS    = ["exam", "test", "quiz", "final", "midterm", "assessment"]
DEADLINE_KEYWORDS = ["deadline", "due", "submit", "assignment", "project"]


class GCalSensor:
    def __init__(self):
        self._service   = None
        self._available = False
        self._login_tried = False
        print("[GCAL SENSOR] Initialized.")

    def _authenticate(self):
        self._login_tried = True
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
                        print("[GCAL SENSOR] credentials.json not found — skipping.")
                        return False
                    flow = InstalledAppFlow.from_client_secrets_file(
                        CREDENTIALS_PATH, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(TOKEN_PATH, "w") as f:
                    f.write(creds.to_json())

            self._service   = build("calendar", "v3", credentials=creds)
            self._available = True
            print("[GCAL SENSOR] Authenticated successfully.")
            return True
        except Exception as e:
            print(f"[GCAL SENSOR] Auth error: {e}")
            return False

    def _classify_event(self, title: str) -> str:
        title_lower = title.lower()
        if any(k in title_lower for k in EXAM_KEYWORDS):
            return "exam"
        if any(k in title_lower for k in DEADLINE_KEYWORDS):
            return "deadline"
        return "event"

    def _fetch_events(self) -> dict:
        try:
            now      = datetime.now(timezone.utc)
            week_end = now + timedelta(days=7)

            events_result = self._service.events().list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=week_end.isoformat(),
                maxResults=20,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events       = events_result.get("items", [])
            today        = now.date()
            events_today = 0
            next_event   = ""
            next_exam    = ""
            days_to_exam = 99
            deadline     = ""

            for event in events:
                start = event.get("start", {})
                dt_str = start.get("dateTime", start.get("date", ""))
                title  = event.get("summary", "Untitled")
                kind   = self._classify_event(title)

                # Parse event date
                try:
                    if "T" in dt_str:
                        event_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                        event_date = event_dt.date()
                        time_str   = event_dt.strftime("%H:%M")
                    else:
                        event_date = datetime.strptime(dt_str, "%Y-%m-%d").date()
                        time_str   = "all day"
                except Exception:
                    continue

                if event_date == today:
                    events_today += 1
                    if not next_event:
                        next_event = f"{title} at {time_str}"

                if kind == "exam" and not next_exam:
                    days_left    = (event_date - today).days
                    days_to_exam = days_left
                    next_exam    = f"{title} — {days_left} days"

                if kind == "deadline" and not deadline:
                    days_left = (event_date - today).days
                    deadline  = f"{title} — {days_left} days"

            return {
                "calendar": {
                    "next_event":    next_event,
                    "events_today":  events_today,
                    "deadline_soon": deadline,
                },
                "buc_portal": {
                    "next_exam":    next_exam,
                    "days_to_exam": days_to_exam,
                }
            }
        except Exception as e:
            print(f"[GCAL SENSOR] Fetch error: {e}")
            return {}

    async def read(self) -> dict:
        if not self._available and not self._login_tried:
            self._authenticate()
        if not self._available and not self._login_tried:
            return {}
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_events)
        except Exception as e:
            print(f"[GCAL SENSOR] Read error: {e}")
            return {}


gcal_sensor = GCalSensor()

if __name__ == "__main__":
    async def test():
        print("[TEST] Google Calendar sensor...")
        result = await gcal_sensor.read()
        if result:
            cal = result.get("calendar", {})
            buc = result.get("buc_portal", {})
            print(f"Events today:  {cal.get('events_today', 0)}")
            print(f"Next event:    {cal.get('next_event', 'none')}")
            print(f"Deadline:      {cal.get('deadline_soon', 'none')}")
            print(f"Next exam:     {buc.get('next_exam', 'none')}")
            print(f"Days to exam:  {buc.get('days_to_exam', 99)}")
            print("[TEST] GCal PASS")
        else:
            print("[TEST] GCal not configured — skipped.")
    asyncio.run(test())
