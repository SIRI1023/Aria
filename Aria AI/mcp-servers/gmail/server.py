import asyncio
import os
import json
import base64
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

load_dotenv(os.path.join(os.path.dirname(__file__), "../../backend/.env"))

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Reuse the same credentials.json from google-calendar (same Cloud project)
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "google-calendar", "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

server = Server("gmail-mcp")


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
    return build("gmail", "v1", credentials=creds)


def decode_body(payload: dict) -> str:
    """Extract plain text body from a Gmail message payload."""
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        # Recurse into nested parts
        for part in payload["parts"]:
            result = decode_body(part)
            if result:
                return result
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return ""


def get_header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def fmt_message(msg: dict, include_body: bool = False) -> dict:
    headers = msg.get("payload", {}).get("headers", [])
    result = {
        "id": msg["id"],
        "from": get_header(headers, "From"),
        "subject": get_header(headers, "Subject"),
        "date": get_header(headers, "Date"),
        "snippet": msg.get("snippet", ""),
    }
    if include_body:
        body = decode_body(msg.get("payload", {}))
        result["body"] = body[:3000] if body else msg.get("snippet", "")
    return result


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="gmail_list_emails",
            description=(
                "List recent emails from Gmail inbox. "
                "Use for: 'show me my recent emails', 'do I have unread emails', "
                "'what emails did I get today'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Number of emails to return (default 10)",
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "If true, only return unread emails",
                    },
                    "label": {
                        "type": "string",
                        "description": "Gmail label to filter by: INBOX, SENT, STARRED, IMPORTANT (default INBOX)",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="gmail_search_emails",
            description=(
                "Search emails using Gmail search syntax. "
                "Use for: 'emails from John', 'emails about the board meeting', "
                "'emails with attachments this week'. "
                "Query examples: 'from:john@example.com', 'subject:invoice', "
                "'after:2026/05/01', 'is:unread from:boss@company.com'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query string",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 10)",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="gmail_get_email",
            description=(
                "Get the full content of a specific email by its ID. "
                "Use this after gmail_list_emails or gmail_search_emails to read the full body of an email."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The Gmail message ID",
                    },
                },
                "required": ["email_id"],
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

    if name == "gmail_list_emails":
        max_results = arguments.get("max_results", 10)
        unread_only = arguments.get("unread_only", False)
        label = arguments.get("label", "INBOX")

        query = "is:unread" if unread_only else ""
        try:
            resp = service.users().messages().list(
                userId="me",
                labelIds=[label],
                q=query,
                maxResults=max_results,
            ).execute()
            messages = resp.get("messages", [])
            if not messages:
                return [types.TextContent(type="text", text=json.dumps({
                    "found": 0,
                    "message": f"No emails found in {label}.",
                }))]

            emails = []
            for m in messages:
                full = service.users().messages().get(
                    userId="me", id=m["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()
                emails.append(fmt_message(full))

            return [types.TextContent(type="text", text=json.dumps({
                "found": len(emails),
                "label": label,
                "emails": emails,
            }, indent=2))]
        except Exception as e:
            return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

    elif name == "gmail_search_emails":
        query = arguments["query"]
        max_results = arguments.get("max_results", 10)
        try:
            resp = service.users().messages().list(
                userId="me", q=query, maxResults=max_results
            ).execute()
            messages = resp.get("messages", [])
            if not messages:
                return [types.TextContent(type="text", text=json.dumps({
                    "found": 0,
                    "query": query,
                    "message": f"No emails found matching: {query}",
                }))]

            emails = []
            for m in messages:
                full = service.users().messages().get(
                    userId="me", id=m["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()
                emails.append(fmt_message(full))

            return [types.TextContent(type="text", text=json.dumps({
                "found": len(emails),
                "query": query,
                "emails": emails,
            }, indent=2))]
        except Exception as e:
            return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

    elif name == "gmail_get_email":
        email_id = arguments["email_id"]
        try:
            msg = service.users().messages().get(
                userId="me", id=email_id, format="full"
            ).execute()
            return [types.TextContent(type="text", text=json.dumps(
                fmt_message(msg, include_body=True), indent=2
            ))]
        except Exception as e:
            return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

    return [types.TextContent(type="text", text="Unknown tool")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
