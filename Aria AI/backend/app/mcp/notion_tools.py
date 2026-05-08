import os
import sys
import asyncio
from langchain_core.tools import tool
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from app.core.config import settings

NOTION_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "mcp-servers", "notion", "server.py")
)

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=[NOTION_SERVER_PATH],
    env={**os.environ, "NOTION_API_KEY": settings.notion_api_key},
)


async def _call_notion_tool(tool_name: str, arguments: dict) -> str:
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
def notion_query_database(database_name: str, filters: dict = {}) -> str:
    """Query a specific Notion database. database_name must be one of: tasks, projects, meetings, docs.
    filters is optional: {status, priority, stage, date_range}.
    date_range values: this_week, today, overdue, past.
    Examples:
    - High priority tasks this week: database_name=tasks, filters={priority: High, date_range: this_week}
    - In-progress projects: database_name=projects, filters={stage: In Progress}
    - Completed projects: database_name=projects, filters={stage: Complete}
    - Last meeting: database_name=meetings, filters={date_range: past}
    Valid stage values for projects: Idea, Planning, In Progress, Complete, Archived, Blocked
    Valid priority values: Low, Medium, High
    Valid task status values: Not started, In Progress, Done
    Always use this instead of notion_search for structured data."""
    return _run(_call_notion_tool("notion_query_database", {
        "database_name": database_name,
        "filters": filters
    }))


@tool
def notion_search_docs(query: str) -> str:
    """Search Notion pages and docs by keyword. Use only for free-text search in Docs.
    For tasks, projects, or meetings — use notion_query_database instead."""
    return _run(_call_notion_tool("notion_search_docs", {"query": query}))


@tool
def notion_get_page(page_id: str) -> str:
    """Get the full content and properties of a specific Notion page by its ID.
    Use this after notion_query_database to get the full details of a specific result."""
    return _run(_call_notion_tool("notion_get_page", {"page_id": page_id}))


@tool
def notion_create_page(title: str, content: str = "", database_name: str = "") -> str:
    """Create a new page in Notion. Optionally specify database_name (tasks, projects, meetings, docs)
    to add it as a row in a specific database."""
    return _run(_call_notion_tool("notion_create_page", {
        "title": title,
        "content": content,
        "database_name": database_name
    }))


NOTION_TOOLS = [notion_query_database, notion_search_docs, notion_get_page, notion_create_page]
