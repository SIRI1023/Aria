from typing import AsyncIterator
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.core.config import settings
from app.agents.tools import TOOLS
import json

SYSTEM_PROMPT = """You are Aria, an AI business operations assistant.

You have access to these tools:
- search_knowledge_base: search uploaded documents for relevant information
- calculate: evaluate arithmetic expressions

Always think step by step. If the user asks about documents or company information,
use search_knowledge_base first. Only answer from what you find — cite your sources."""


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
