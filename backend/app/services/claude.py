from typing import AsyncIterator
from anthropic import AsyncAnthropic
from app.core.config import settings

client = AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """You are Aria, an AI business operations assistant. You help users find information,
answer questions, and complete tasks efficiently. Be concise, helpful, and professional."""


async def stream_chat(messages: list[dict]) -> AsyncIterator[str]:
    async with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text
