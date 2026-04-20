"""
Friday — Calendar & Google Meet Tool
Creates calendar events and Google Meet links on Tanish's behalf.

Setup needed (one-time):
  1. Go to console.cloud.google.com
  2. Enable Google Calendar API
  3. Create OAuth2 credentials → download as credentials.json
  4. Place credentials.json in Friday project root
  5. First run will open browser for auth → creates token.json

After that, runs headlessly.
"""
import asyncio
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytz
from dateutil import parser as date_parser

CREDS_FILE  = Path(__file__).parent.parent.parent / "credentials.json"
TOKEN_FILE  = Path(__file__).parent.parent.parent / "token.json"
SCOPES      = ["https://www.googleapis.com/auth/calendar"]
IST         = pytz.timezone("Asia/Kolkata")
OWNER_EMAIL = "tanishrajput9@gmail.com"


def _get_google_service():
    """Returns an authenticated Google Calendar service (sync helper)."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        creds = None
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif CREDS_FILE.exists():
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
                creds = flow.run_local_server(port=0)
                TOKEN_FILE.write_text(creds.to_json())
            else:
                return None  # No credentials file yet

        return build("calendar", "v3", credentials=creds)
    except Exception:
        return None


async def create_meeting(
    requester_name: str,
    requester_email: str,
    topic: str,
    preferred_date: str,        # e.g. "tomorrow", "25 Jan", "next Monday"
    preferred_time: str = "11:00 AM",  # IST
    duration_minutes: int = 30,
) -> dict:
    """
    Creates a Google Calendar event with a Meet link.
    Returns {"success": bool, "meet_link": str, "event_time": str, "message": str}
    """
    # ── Parse date/time ───────────────────────────────────────────────────────
    try:
        now_ist = datetime.now(IST)
        date_str = preferred_date.strip().lower()

        if date_str in ("tomorrow", "tmrw"):
            base_date = now_ist + timedelta(days=1)
        elif date_str in ("day after tomorrow",):
            base_date = now_ist + timedelta(days=2)
        elif date_str == "next monday":
            days_ahead = (0 - now_ist.weekday()) % 7 or 7
            base_date = now_ist + timedelta(days=days_ahead)
        else:
            base_date = date_parser.parse(preferred_date, dayfirst=True)
            base_date = IST.localize(base_date) if base_date.tzinfo is None else base_date

        time_obj   = date_parser.parse(preferred_time)
        start_dt   = base_date.replace(
            hour=time_obj.hour,
            minute=time_obj.minute,
            second=0, microsecond=0,
        )
        end_dt     = start_dt + timedelta(minutes=duration_minutes)

    except Exception as e:
        return {"success": False, "message": f"Couldn't parse the date/time: {e}"}

    # ── Try Google Calendar API ───────────────────────────────────────────────
    service = await asyncio.to_thread(_get_google_service)

    if service:
        try:
            event = {
                "summary":     f"Chat with {requester_name} — {topic}",
                "description": (
                    f"Meeting requested via Friday (Tanish's AI agent) by {requester_name} ({requester_email}).\n"
                    f"Topic: {topic}"
                ),
                "start":  {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
                "end":    {"dateTime": end_dt.isoformat(),   "timeZone": "Asia/Kolkata"},
                "attendees": [
                    {"email": OWNER_EMAIL},
                    {"email": requester_email},
                ],
                "conferenceData": {
                    "createRequest": {
                        "requestId":             f"friday-{int(datetime.now().timestamp())}",
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                },
                "reminders": {
                    "useDefault": False,
                    "overrides":  [
                        {"method": "email",  "minutes": 60},
                        {"method": "popup",  "minutes": 15},
                    ],
                },
            }

            created = await asyncio.to_thread(
                lambda: service.events().insert(
                    calendarId="primary",
                    body=event,
                    conferenceDataVersion=1,
                    sendUpdates="all",
                ).execute()
            )

            meet_link  = created.get("hangoutLink", "Link will be in the calendar invite")
            event_time = start_dt.strftime("%A, %d %B %Y at %I:%M %p IST")

            return {
                "success":    True,
                "meet_link":  meet_link,
                "event_time": event_time,
                "message":    (
                    f"Done! Meeting scheduled for {event_time}. "
                    f"Google Meet link: {meet_link}. "
                    f"Tanish and {requester_email} will both receive calendar invites."
                ),
            }

        except Exception as e:
            # Fall through to email fallback
            pass

    # ── Fallback: send email to Tanish requesting the meeting ─────────────────
    try:
        import resend
        from friday.config import get_settings
        cfg = get_settings()
        resend.api_key = cfg.resend_api_key

        event_time = start_dt.strftime("%A, %d %B %Y at %I:%M %p IST")
        resend.Emails.send({
            "from":    cfg.sender_email,
            "to":      [cfg.your_email],
            "subject": f"Meeting Request from {requester_name} — {topic}",
            "html":    f"""
            <p><strong>{requester_name}</strong> ({requester_email}) would like to schedule a meeting.</p>
            <p><strong>Topic:</strong> {topic}</p>
            <p><strong>Requested time:</strong> {event_time}</p>
            <p><strong>Duration:</strong> {duration_minutes} minutes</p>
            <p>Please reply directly to {requester_email} to confirm.</p>
            <p style="color:#999;font-size:0.8rem;">Requested via Friday — Tanish's AI voice agent.</p>
            """,
        })

        return {
            "success":    True,
            "meet_link":  None,
            "event_time": event_time,
            "message":    (
                f"Tanish hasn't connected Google Calendar yet, but I've sent him your meeting request for "
                f"{event_time}. He'll reach out to {requester_email} to confirm."
            ),
        }

    except Exception as e:
        return {"success": False, "message": f"Couldn't schedule the meeting: {e}"}
