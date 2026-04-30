from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.graph import run_agent_stream

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class AgentRequest(BaseModel):
    messages: list[Message]


@router.post("/agent")
async def agent_chat(request: AgentRequest):
    messages = [m.model_dump() for m in request.messages]
    last_user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )

    async def event_stream():
        async for chunk in run_agent_stream(last_user_msg, messages):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
