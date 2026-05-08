"""Run this once to seed your Google Calendar with test events for Aria demos."""
import os
import json
from datetime import datetime, timedelta, date
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]


def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(os.path.dirname(__file__), "credentials.json"), SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def dt(d: date, hour: int, minute: int = 0) -> str:
    return datetime(d.year, d.month, d.day, hour, minute).isoformat()


def create(service, title, start, end, description="", attendees=None):
    body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start, "timeZone": "America/New_York"},
        "end":   {"dateTime": end,   "timeZone": "America/New_York"},
    }
    if attendees:
        body["attendees"] = [{"email": e} for e in attendees]
    event = service.events().insert(calendarId="primary", body=body).execute()
    print(f"  Created: {title}")
    return event


def main():
    service = get_service()
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)

    # Work out Monday of this week and next
    monday_this = today - timedelta(days=today.weekday())
    monday_next = monday_this + timedelta(days=7)

    print(f"\nSeeding events for week of {monday_this} ...\n")

    # --- TODAY ---
    create(service,
        "Daily Standup",
        dt(today, 9, 30), dt(today, 9, 45),
        description="Team sync - blockers, progress, plan",
        attendees=["alice@example.com", "bob@example.com"])

    create(service,
        "Sprint Planning",
        dt(today, 11, 0), dt(today, 12, 0),
        description="Plan tasks for the next sprint with the engineering team")

    create(service,
        "Lunch with Investor",
        dt(today, 13, 0), dt(today, 14, 0),
        description="Quarterly check-in with seed investor")

    create(service,
        "1:1 with Manager",
        dt(today, 15, 0), dt(today, 15, 30),
        description="Weekly 1:1 - performance review prep")

    # --- TOMORROW ---
    create(service,
        "Product Demo",
        dt(tomorrow, 10, 0), dt(tomorrow, 11, 0),
        description="Demo Aria AI to potential enterprise customer",
        attendees=["client@bigcorp.com"])

    create(service,
        "Design Review",
        dt(tomorrow, 14, 0), dt(tomorrow, 15, 0),
        description="Review new dashboard designs with UX team")

    # --- DAY AFTER TOMORROW ---
    create(service,
        "Engineering All-Hands",
        dt(day_after, 10, 0), dt(day_after, 11, 30),
        description="Monthly all-hands: roadmap, OKRs, and Q&A")

    create(service,
        "Candidate Interview — Senior Engineer",
        dt(day_after, 14, 0), dt(day_after, 15, 0),
        description="Technical interview round 2")

    # --- REST OF THIS WEEK (Thu, Fri) ---
    thu = monday_this + timedelta(days=3)
    fri = monday_this + timedelta(days=4)

    if thu > today:
        create(service,
            "Board Meeting Prep",
            dt(thu, 9, 0), dt(thu, 10, 0),
            description="Prepare slides and metrics for board meeting")

        create(service,
            "Customer Success Call",
            dt(thu, 15, 0), dt(thu, 16, 0),
            description="Quarterly review with top 3 enterprise accounts")

    if fri > today:
        create(service,
            "Weekly Retrospective",
            dt(fri, 16, 0), dt(fri, 17, 0),
            description="End-of-week retro: what went well, what to improve")

    # --- NEXT WEEK ---
    print("\nSeeding events for next week ...\n")

    create(service,
        "Board Meeting",
        dt(monday_next, 10, 0), dt(monday_next + timedelta(days=0), 12, 0),
        description="Quarterly board meeting — financials, roadmap, hiring plan")

    create(service,
        "New Hire Onboarding",
        dt(monday_next + timedelta(days=1), 9, 0),
        dt(monday_next + timedelta(days=1), 10, 0),
        description="Onboarding session for 2 new engineers joining the team")

    create(service,
        "Investor Update Call",
        dt(monday_next + timedelta(days=2), 11, 0),
        dt(monday_next + timedelta(days=2), 12, 0),
        description="Monthly update to lead investor — metrics and milestones")

    create(service,
        "Product Roadmap Review",
        dt(monday_next + timedelta(days=3), 14, 0),
        dt(monday_next + timedelta(days=3), 15, 30),
        description="Q3 roadmap finalization with product and eng leads")

    print("\nDone! All events created in your Google Calendar.")
    print("Now try asking Aria: 'What meetings do I have today?' or 'What's on my calendar this week?'")


if __name__ == "__main__":
    main()
