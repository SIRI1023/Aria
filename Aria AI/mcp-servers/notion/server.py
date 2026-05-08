import asyncio
import os
import json
from datetime import date, timedelta
from dotenv import load_dotenv
from notion_client import Client
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

load_dotenv(os.path.join(os.path.dirname(__file__), "../../backend/.env"))

NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
# notion_version pins to the API version that supports /databases/{id}/query
# (notion-client v3 defaults to 2025-09-03 which dropped that endpoint)
notion = Client(auth=NOTION_API_KEY, notion_version="2022-06-28")
server = Server("notion-mcp")

# --- Database registry (cached at startup) ---
DATABASES = {
    "tasks":    "c9a58ffe-7762-83e9-a62b-81c4d7b5d23a",
    "projects": "00958ffe-7762-82ef-9053-012df8f516e3",
    "meetings": "cd658ffe-7762-82da-9315-81a3afd974b3",
    "docs":     "2d558ffe-7762-827f-8d8a-016ac775d15e",
}

# Exact property names per database (case-sensitive)
DB_PROPERTIES = {
    "tasks":    {"title": "Tasks",    "status": "Status", "priority": "Priority", "due_date": "Due Date", "assignee": "Assignee"},
    "projects": {"title": "Project",  "status": "Status", "priority": "Priority", "due_date": "Due Date", "owner": "Owner", "stage": "Stage"},
    "meetings": {"title": "Meetings", "date": "Date",     "attendees": "Attendees", "notes": "Notes", "action_items": "Action Items"},
    "docs":     {"title": "Document"},
}


# --- Date helpers ---
def this_week_range() -> tuple[str, str]:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return monday.isoformat(), sunday.isoformat()


def today_str() -> str:
    return date.today().isoformat()


# --- Property extractors ---
def extract_property_value(val: dict) -> str | list | None:
    vtype = val.get("type")
    if vtype == "title":
        texts = val.get("title", [])
        return texts[0]["plain_text"] if texts else ""
    if vtype == "rich_text":
        texts = val.get("rich_text", [])
        return texts[0]["plain_text"] if texts else ""
    if vtype == "select":
        sel = val.get("select")
        return sel["name"] if sel else None
    if vtype == "multi_select":
        return [s["name"] for s in val.get("multi_select", [])]
    if vtype == "date":
        d = val.get("date")
        return d["start"] if d else None
    if vtype == "people":
        return [p.get("name", "") for p in val.get("people", [])]
    if vtype == "checkbox":
        return val.get("checkbox")
    if vtype == "status":
        s = val.get("status")
        return s["name"] if s else None
    return None


def extract_page(page: dict) -> dict:
    props = {}
    for key, val in page.get("properties", {}).items():
        v = extract_property_value(val)
        if v is not None and v != "" and v != []:
            props[key] = v
    return {"id": page["id"], "properties": props}


def get_page_title(page: dict, db_name: str) -> str:
    title_key = DB_PROPERTIES.get(db_name, {}).get("title", "")
    props = page.get("properties", {})
    if title_key and title_key in props:
        v = extract_property_value(props[title_key])
        return v if isinstance(v, str) else "Untitled"
    for val in props.values():
        if val.get("type") == "title":
            texts = val.get("title", [])
            return texts[0]["plain_text"] if texts else "Untitled"
    return "Untitled"


def extract_blocks(page_id: str) -> str:
    blocks = notion.blocks.children.list(block_id=page_id)
    lines = []
    for b in blocks["results"]:
        btype = b["type"]
        content = b.get(btype, {})
        rich = content.get("rich_text", [])
        text = "".join(r.get("plain_text", "") for r in rich)
        if text:
            lines.append(text)
    return "\n".join(lines)


def build_filter(db_name: str, filters: dict) -> dict | None:
    props = DB_PROPERTIES.get(db_name, {})
    conditions = []

    if "status" in filters and filters["status"] and "status" in props:
        conditions.append({
            "property": props["status"],
            "select": {"equals": filters["status"]}
        })

    if "stage" in filters and filters["stage"] and "stage" in props:
        conditions.append({
            "property": props["stage"],
            "select": {"equals": filters["stage"]}
        })

    if "priority" in filters and filters["priority"] and "priority" in props:
        conditions.append({
            "property": props["priority"],
            "select": {"equals": filters["priority"]}
        })

    date_prop = props.get("due_date") or props.get("date")
    if date_prop and "date_range" in filters:
        dr = filters["date_range"]
        if dr == "this_week":
            start, end = this_week_range()
            conditions.append({
                "property": date_prop,
                "date": {"on_or_after": start}
            })
            conditions.append({
                "property": date_prop,
                "date": {"on_or_before": end}
            })
        elif dr == "today":
            conditions.append({
                "property": date_prop,
                "date": {"equals": today_str()}
            })
        elif dr == "overdue":
            conditions.append({
                "property": date_prop,
                "date": {"before": today_str()}
            })
        elif dr == "past":
            conditions.append({
                "property": date_prop,
                "date": {"before": today_str()}
            })

    if not conditions:
        return None
    if len(conditions) == 1:
        return {"filter": conditions[0]}
    return {"filter": {"and": conditions}}


# --- MCP Tool Definitions ---
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="notion_query_database",
            description=(
                "Query a specific Notion database with optional filters. "
                "Use this for ALL structured queries about tasks, projects, or meetings. "
                "database_name must be one of: tasks, projects, meetings, docs. "
                "filters is optional JSON with keys: status, priority, stage, date_range "
                "(date_range values: this_week, today, overdue, past)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "database_name": {
                        "type": "string",
                        "enum": ["tasks", "projects", "meetings", "docs"],
                        "description": "Which database to query"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional filters: {status, priority, stage, date_range}",
                        "properties": {
                            "status":     {"type": "string"},
                            "priority":   {"type": "string"},
                            "stage":      {"type": "string"},
                            "date_range": {"type": "string", "enum": ["this_week", "today", "overdue", "past"]}
                        }
                    }
                },
                "required": ["database_name"],
            },
        ),
        types.Tool(
            name="notion_search_docs",
            description="Search docs and pages in Notion by keyword. Use only for free-text search in Docs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="notion_get_page",
            description="Get the full content and properties of a specific Notion page by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"}
                },
                "required": ["page_id"],
            },
        ),
        types.Tool(
            name="notion_create_page",
            description="Create a new page in Notion. Specify database_name to add it to a database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title":         {"type": "string"},
                    "content":       {"type": "string"},
                    "database_name": {"type": "string", "enum": ["tasks", "projects", "meetings", "docs"]}
                },
                "required": ["title"],
            },
        ),
    ]


# --- MCP Tool Handlers ---
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    if name == "notion_query_database":
        db_name = arguments["database_name"].lower()
        db_id = DATABASES.get(db_name)
        if not db_id:
            return [types.TextContent(type="text", text=f"Unknown database: {db_name}")]

        filters = arguments.get("filters") or {}
        query_params = build_filter(db_name, filters)

        body = {"page_size": 20}
        if query_params:
            body.update(query_params)

        # Sort by date descending for meetings
        if db_name == "meetings":
            body["sorts"] = [{"property": "Date", "direction": "descending"}]

        try:
            response = notion.request(
                path=f"databases/{db_id}/query",
                method="POST",
                body=body,
            )
        except Exception as e:
            err = str(e)
            return [types.TextContent(type="text", text=json.dumps({
                "found": 0,
                "database": db_name,
                "error": err,
                "message": f"Query failed for {db_name} database: {err}. Check filter values and retry with correct options."
            }))]
        pages = response.get("results", [])

        if not pages:
            filter_desc = json.dumps(filters) if filters else "no filters"
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "found": 0,
                    "database": db_name,
                    "filters_applied": filters,
                    "message": f"No results found in {db_name} database with filters: {filter_desc}. Try broadening your search."
                })
            )]

        results = []
        for page in pages:
            extracted = extract_page(page)
            extracted["title"] = get_page_title(page, db_name)
            results.append(extracted)

        return [types.TextContent(type="text", text=json.dumps({
            "found": len(results),
            "database": db_name,
            "filters_applied": filters,
            "results": results
        }, indent=2))]

    elif name == "notion_search_docs":
        response = notion.search(
            query=arguments["query"],
            filter={"property": "object", "value": "page"}
        )
        pages = response.get("results", [])
        if not pages:
            return [types.TextContent(type="text", text=json.dumps({
                "found": 0,
                "message": f"No pages found matching '{arguments['query']}' in Notion."
            }))]

        results = []
        for page in pages[:5]:
            extracted = extract_page(page)
            extracted["title"] = get_page_title(page, "docs")
            content = extract_blocks(page["id"])
            extracted["content"] = content[:500] if content else ""
            results.append(extracted)

        return [types.TextContent(type="text", text=json.dumps({
            "found": len(results),
            "results": results
        }, indent=2))]

    elif name == "notion_get_page":
        page = notion.pages.retrieve(page_id=arguments["page_id"])
        extracted = extract_page(page)
        extracted["content"] = extract_blocks(arguments["page_id"])
        return [types.TextContent(type="text", text=json.dumps(extracted, indent=2))]

    elif name == "notion_create_page":
        db_name = arguments.get("database_name", "").lower()
        title = arguments["title"]
        content = arguments.get("content", "")

        if db_name and db_name in DATABASES:
            db_id = DATABASES[db_name]
            title_prop = DB_PROPERTIES[db_name]["title"]
            new_page = notion.pages.create(
                parent={"database_id": db_id},
                properties={
                    title_prop: {"title": [{"type": "text", "text": {"content": title}}]}
                },
                children=[{
                    "object": "block", "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": content}}]}
                }] if content else []
            )
        else:
            parent_id = "26a58ffe-7762-83b7-b4dc-014786683164"
            new_page = notion.pages.create(
                parent={"type": "page_id", "page_id": parent_id},
                properties={
                    "title": {"title": [{"type": "text", "text": {"content": title}}]}
                },
                children=[{
                    "object": "block", "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": content}}]}
                }] if content else []
            )

        return [types.TextContent(type="text", text=json.dumps({
            "created": True, "id": new_page["id"], "title": title, "database": db_name or "workspace"
        }))]

    return [types.TextContent(type="text", text="Unknown tool")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
