import asyncio
import os
import json
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

load_dotenv(os.path.join(os.path.dirname(__file__), "../../backend/.env"))

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

server = Server("google-calendar-mcp")


def get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def get_time_range(date_range: str) -> tuple[str, str]:
    today = date.today()
    if date_range == "today":
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
    elif date_range == "tomorrow":
        d = today + timedelta(days=1)
        start = datetime.combine(d, datetime.min.time())
        end = datetime.combine(d, datetime.max.time())
    elif date_range == "this_week":
        monday = today - timedelta(days=today.weekday())
        start = datetime.combine(monday, datetime.min.time())
        end = datetime.combine(monday + timedelta(days=6), datetime.max.time())
    elif date_range == "next_week":
        next_monday = today + timedelta(days=7 - today.weekday())
        start = datetime.combine(next_monday, datetime.min.time())
        end = datetime.combine(next_monday + timedelta(days=6), datetime.max.time())
    else:
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
    return start.isoformat() + "Z", end.isoformat() + "Z"


def fmt_event(event: dict) -> dict:
    s = event.get("start", {})
    e = event.get("end", {})
    return {
        "id": event.get("id", ""),
        "title": event.get("summary", "No title"),
        "start": s.get("dateTime", s.get("date", "")),
        "end": e.get("dateTime", e.get("date", "")),
        "location": event.get("location", ""),
        "description": (event.get("description") or "")[:200],
        "attendees": [a.get("email", "") for a in event.get("attendees", [])],
        "link": event.get("htmlLink", ""),
    }


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="gcal_list_events",
            description=(
                "List Google Calendar events for a date range. "
                "Use for: 'what's on my calendar today/this week', "
                "'do I have meetings tomorrow', 'what are my events next week'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date_range": {
                        "type": "string",
                        "enum": ["today", "tomorrow", "this_week", "next_week"],
                        "description": "Time range to list events for",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Max events to return (default 10)",
                    },
                },
                "required": ["date_range"],
            },
        ),
        types.Tool(
            name="gcal_create_event",
            description="Create a new event in Google Calendar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_time": {
                        "type": "string",
                        "description": "ISO datetime e.g. 2026-05-10T14:00:00",
                    },
                    "end_time": {
                        "type": "string",
                        "description": "ISO datetime e.g. 2026-05-10T15:00:00",
                    },
                    "description": {"type": "string"},
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses",
                    },
                },
                "required": ["title", "start_time", "end_time"],
            },
        ),
        types.Tool(
            name="gcal_find_free_slots",
            description=(
                "Find free time slots on a specific date. "
                "Use when the user wants to schedule something and needs to know when they're available."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Length of slot needed in minutes",
                    },
                    "work_start_hour": {
                        "type": "integer",
                        "description": "Work day start hour 0-23 (default 9)",
                    },
                    "work_end_hour": {
                        "type": "integer",
                        "description": "Work day end hour 0-23 (default 18)",
                    },
                },
                "required": ["date", "duration_minutes"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        service = get_service()
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({
            "error": f"Auth failed: {e}. Run server.py directly once to complete OAuth."
        }))]

    if name == "gcal_list_events":
        date_range = arguments["date_range"]
        max_results = arguments.get("max_results", 10)
        time_min, time_max = get_time_range(date_range)
        try:
            result = service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            events = result.get("items", [])
            if not events:
                return [types.TextContent(type="text", text=json.dumps({
                    "found": 0,
                    "date_range": date_range,
                    "message": f"No events found for {date_range}.",
                }))]
            return [types.TextContent(type="text", text=json.dumps({
                "found": len(events),
                "date_range": date_range,
                "events": [fmt_event(e) for e in events],
            }, indent=2))]
        except Exception as e:
            return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

    elif name == "gcal_create_event":
        body = {
            "summary": arguments["title"],
            "description": arguments.get("description", ""),
            "start": {"dateTime": arguments["start_time"], "timeZone": "UTC"},
            "end": {"dateTime": arguments["end_time"], "timeZone": "UTC"},
        }
        attendees = arguments.get("attendees", [])
        if attendees:
            body["attendees"] = [{"email": e} for e in attendees]
        try:
            event = service.events().insert(calendarId="primary", body=body).execute()
            return [types.TextContent(type="text", text=json.dumps({
                "created": True,
                "id": event.get("id"),
                "title": arguments["title"],
                "start": arguments["start_time"],
                "end": arguments["end_time"],
                "link": event.get("htmlLink", ""),
            }))]
        except Exception as e:
            return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

    elif name == "gcal_find_free_slots":
        target_date = arguments["date"]
        duration = timedelta(minutes=arguments["duration_minutes"])
        work_start_h = arguments.get("work_start_hour", 9)
        work_end_h = arguments.get("work_end_hour", 18)
        try:
            d = date.fromisoformat(target_date)
            time_min = datetime(d.year, d.month, d.day, work_start_h).isoformat() + "Z"
            time_max = datetime(d.year, d.month, d.day, work_end_h).isoformat() + "Z"
            result = service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            events = result.get("items", [])

            busy = []
            for ev in events:
                s = ev.get("start", {}).get("dateTime")
                e = ev.get("end", {}).get("dateTime")
                if s and e:
                    busy.append((
                        datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None),
                        datetime.fromisoformat(e.replace("Z", "+00:00")).replace(tzinfo=None),
                    ))
            busy.sort()

            work_start = datetime(d.year, d.month, d.day, work_start_h)
            work_end = datetime(d.year, d.month, d.day, work_end_h)
            free_slots = []
            cursor = work_start
            for b_start, b_end in busy:
                if cursor + duration <= b_start:
                    free_slots.append({
                        "start": cursor.strftime("%H:%M"),
                        "end": (cursor + duration).strftime("%H:%M"),
                    })
                cursor = max(cursor, b_end)
            if cursor + duration <= work_end:
                free_slots.append({
                    "start": cursor.strftime("%H:%M"),
                    "end": (cursor + duration).strftime("%H:%M"),
                })

            return [types.TextContent(type="text", text=json.dumps({
                "date": target_date,
                "duration_minutes": arguments["duration_minutes"],
                "found": len(free_slots),
                "free_slots": free_slots[:5],
            }, indent=2))]
        except Exception as e:
            return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

    return [types.TextContent(type="text", text="Unknown tool")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
