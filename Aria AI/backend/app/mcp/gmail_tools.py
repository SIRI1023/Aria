import os
import sys
import asyncio
from langchain_core.tools import tool
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

GMAIL_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "mcp-servers", "gmail", "server.py")
)

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=[GMAIL_SERVER_PATH],
    env={**os.environ},
)


async def _call_gmail_tool(tool_name: str, arguments: dict) -> str:
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
def gmail_list_emails(max_results: int = 10, unread_only: bool = False, label: str = "INBOX") -> str:
    """List recent emails from Gmail.
    label must be one of: INBOX, SENT, STARRED, IMPORTANT.
    Set unread_only=true to only return unread emails.
    Use for: 'show my recent emails', 'do I have unread emails', 'what's in my inbox'."""
    return _run(_call_gmail_tool("gmail_list_emails", {
        "max_results": max_results,
        "unread_only": unread_only,
        "label": label,
    }))


@tool
def gmail_search_emails(query: str, max_results: int = 10) -> str:
    """Search Gmail using Gmail search syntax.
    Query examples: 'from:john@example.com', 'subject:invoice', 'is:unread subject:meeting'.
    Use for: 'emails from X', 'emails about Y', 'unread emails from my boss'."""
    return _run(_call_gmail_tool("gmail_search_emails", {
        "query": query,
        "max_results": max_results,
    }))


@tool
def gmail_get_email(email_id: str) -> str:
    """Get the full content of a specific email by its ID.
    Use this after gmail_list_emails or gmail_search_emails to read the full body of an email."""
    return _run(_call_gmail_tool("gmail_get_email", {"email_id": email_id}))


GMAIL_TOOLS = [gmail_list_emails, gmail_search_emails, gmail_get_email]
