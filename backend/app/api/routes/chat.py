from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.claude import stream_chat
from app.rag.retrieval import retrieve_context
import json

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


@router.post("/chat")
async def chat(request: ChatRequest):
    messages = [m.model_dump() for m in request.messages]

    last_user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    context, citations = retrieve_context(last_user_msg)

    async def event_stream():
        async for chunk in stream_chat(messages, context):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        if citations:
            yield f"data: {json.dumps({'citations': citations})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
