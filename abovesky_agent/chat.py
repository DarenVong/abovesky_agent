import json
import time
import uuid
from typing import AsyncIterator

import anthropic
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .config import settings

router = APIRouter()
_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

MODEL_ID = "abovesky-tutor"

SYSTEM_PROMPT = (
    "You are abovesky, a computer science tutor. You help students understand CS concepts "
    "deeply through clear explanations, examples, and Socratic questioning. You are "
    "knowledgeable about algorithms, data structures, systems, programming languages, and "
    "software engineering. When explaining concepts, build intuition from fundamentals. "
    "Be encouraging and precise."
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = MODEL_ID
    messages: list[Message]
    stream: bool = True
    max_tokens: int = 4096


def _prepare(messages: list[Message]) -> tuple[str, list[dict]]:
    system_parts: list[str] = [SYSTEM_PROMPT]
    chat: list[dict] = []
    for m in messages:
        if m.role == "system":
            system_parts.append(m.content)
        else:
            chat.append({"role": m.role, "content": m.content})
    return "\n\n".join(system_parts), chat


async def _sse_stream(request: ChatRequest) -> AsyncIterator[str]:
    system, messages = _prepare(request.messages)
    cid = f"chatcmpl-{uuid.uuid4().hex}"

    def _chunk(text: str, finish: str | None = None) -> str:
        return f"data: {json.dumps({'id': cid, 'object': 'chat.completion.chunk', 'created': int(time.time()), 'model': MODEL_ID, 'choices': [{'index': 0, 'delta': {'content': text} if text else {}, 'finish_reason': finish}]})}\n\n"

    try:
        async with _client.messages.stream(
            model=settings.default_model,
            max_tokens=request.max_tokens,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield _chunk(text)
    except anthropic.AuthenticationError:
        yield _chunk("⚠️ Anthropic API key is invalid or missing. Check ANTHROPIC_API_KEY in .env and restart the container.", finish="stop")
        yield "data: [DONE]\n\n"
        return
    except anthropic.APIError as e:
        yield _chunk(f"⚠️ API error: {e}", finish="stop")
        yield "data: [DONE]\n\n"
        return

    yield _chunk("", finish="stop")
    yield "data: [DONE]\n\n"


@router.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [{"id": MODEL_ID, "object": "model", "created": int(time.time()), "owned_by": "abovesky"}],
    }


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    if request.stream:
        return StreamingResponse(_sse_stream(request), media_type="text/event-stream")

    system, messages = _prepare(request.messages)
    response = await _client.messages.create(
        model=settings.default_model,
        max_tokens=request.max_tokens,
        system=system,
        messages=messages,
    )
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": MODEL_ID,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": response.content[0].text}, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens": response.usage.input_tokens,
            "completion_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        },
    }
