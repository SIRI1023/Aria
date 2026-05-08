import os
import sys
import asyncio
from langchain_core.tools import tool
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from app.core.config import settings

GCAL_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "mcp-servers", "google-calendar", "server.py")
)

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=[GCAL_SERVER_PATH],
    env={**os.environ},
)


async def _call_gcal_tool(tool_name: str, arguments: dict) -> str:
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else "No result"


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@tool
def gcal_list_events(date_range: str, max_results: int = 10) -> str:
    """List Google Calendar events for a date range.
    date_range must be one of: today, tomorrow, this_week, next_week.
    Use for questions like 'what's on my calendar today?', 'do I have meetings this week?'."""
    return _run(_call_gcal_tool("gcal_list_events", {
        "date_range": date_range,
        "max_results": max_results,
    }))


@tool
def gcal_create_event(title: str, start_time: str, end_time: str, description: str = "", attendees: list = []) -> str:
    """Create a new event in Google Calendar.
    start_time and end_time must be ISO format: 2026-05-10T14:00:00.
    attendees is an optional list of email addresses."""
    return _run(_call_gcal_tool("gcal_create_event", {
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "description": description,
        "attendees": attendees,
    }))


@tool
def gcal_find_free_slots(date: str, duration_minutes: int, work_start_hour: int = 9, work_end_hour: int = 18) -> str:
    """Find free time slots on a specific date in Google Calendar.
    date must be in YYYY-MM-DD format. duration_minutes is how long the slot needs to be.
    Use when the user wants to schedule something and needs to know when they're free."""
    return _run(_call_gcal_tool("gcal_find_free_slots", {
        "date": date,
        "duration_minutes": duration_minutes,
        "work_start_hour": work_start_hour,
        "work_end_hour": work_end_hour,
    }))


GCAL_TOOLS = [gcal_list_events, gcal_create_event, gcal_find_free_slots]
