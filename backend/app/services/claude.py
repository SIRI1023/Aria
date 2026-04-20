from typing import AsyncIterator
import anthropic
from app.core.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """You are Aria, an AI business operations assistant. You help users find information,
answer questions, and complete tasks efficiently. Be concise, helpful, and professional."""


async def stream_chat(messages: list[dict]) -> AsyncIterator[str]:
    """Stream a chat response from Claude with prompt caching on the system prompt."""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # prompt caching
            }
        ],
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text
