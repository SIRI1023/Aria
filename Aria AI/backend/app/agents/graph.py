from typing import AsyncIterator
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.config import settings
from app.agents.tools import TOOLS
import json

SYSTEM_PROMPT = """You are Aria, an AI business operations assistant. You help teams find information, answer questions, and get work done across their business tools.

## How to choose tools

Use notion_query_database for ANY structured question about tasks, projects, or meetings.
Always pass the correct database_name (tasks / projects / meetings / docs) and use
filters to narrow results — never query without filters when the user specifies
priority, status, date, or assignee.

Use notion_search_docs when the user asks about a document, guide, policy, or
written content by name or topic.

Use notion_get_page to read the full details of a specific page after finding its ID.

Use gcal_list_events when the user asks about their calendar, schedule, or meetings
for a specific time period (today, tomorrow, this week, next week).

Use gcal_create_event when the user wants to schedule or create a new calendar event.

Use gcal_find_free_slots when the user wants to know when they are free or needs to
find a good time to schedule something.

Use gmail_list_emails when the user wants to see recent emails or check their inbox.
Use gmail_search_emails when the user asks about emails from a specific person,
about a specific topic, or using any search criteria.
Use gmail_get_email to read the full body of a specific email after finding its ID.

Use search_knowledge_base when the user asks about files or documents they uploaded
directly to Aria (PDFs, text files) — not Notion content.

Use calculate for any arithmetic or numeric computation.

## How to handle results

- If a query returns no results, tell the user exactly which tool and parameters
  you used, and suggest broadening the search. Never substitute unrelated data.
- Always confirm which source (Notion, Google Calendar, or uploaded file) your answer came from.
- When listing calendar events, include the title, start time, end time, and location.
- When listing tasks or projects, include status, priority, and due date.
- Think step by step before choosing a tool. Pick the most specific one available."""


def build_graph():
    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    ).bind_tools(TOOLS)

    tool_node = ToolNode(TOOLS)

    def call_model(state: MessagesState) -> dict:
        system = SystemMessage(content=SYSTEM_PROMPT)
        response = llm.invoke([system] + state["messages"])
        return {"messages": [response]}

    def should_continue(state: MessagesState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


compiled_graph = build_graph()


async def run_agent_stream(user_message: str, history: list[dict]) -> AsyncIterator[str]:
    """Run the agent and stream back step events as JSON strings."""
    messages = []
    for m in history[:-1]:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            messages.append(AIMessage(content=m["content"]))
    messages.append(HumanMessage(content=user_message))

    async for event in compiled_graph.astream({"messages": messages}, stream_mode="updates"):
        for node_name, node_output in event.items():
            new_messages = node_output.get("messages", [])
            for msg in new_messages:
                if node_name == "tools":
                    yield json.dumps({
                        "type": "tool_result",
                        "tool": msg.name if hasattr(msg, "name") else "tool",
                        "content": str(msg.content)[:300],
                    })
                elif node_name == "agent":
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            yield json.dumps({
                                "type": "tool_call",
                                "tool": tc["name"],
                                "args": tc["args"],
                            })
                    elif hasattr(msg, "content") and msg.content:
                        yield json.dumps({
                            "type": "final_answer",
                            "content": msg.content,
                        })
