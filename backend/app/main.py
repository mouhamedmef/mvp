import json
import os
import secrets
import time
import uuid
from collections.abc import Iterator
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.db import delete_chat_log, fetch_recent_logs, init_db, insert_chat_log
from app.graph import graph

API_KEY = os.getenv("API_KEY", "pfe-local-key")
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False


app = FastAPI(title="L1 Support Echo API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.middleware("http")
async def api_key_guard(request: Request, call_next):
    path = request.url.path

    if not path.startswith("/v1/") or path in PUBLIC_PATHS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "message": "Missing bearer token.",
                    "type": "invalid_request_error",
                    "code": "missing_api_key",
                }
            },
        )

    provided_key = auth_header.replace("Bearer ", "", 1).strip()
    if not secrets.compare_digest(provided_key, API_KEY):
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "message": "Invalid API key.",
                    "type": "invalid_request_error",
                    "code": "invalid_api_key",
                }
            },
        )

    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/models")
def list_models() -> dict:
    return {
        "object": "list",
        "data": [
            {
                "id": "echo-langgraph",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "local",
            }
        ],
    }


@app.get("/v1/logs")
def list_logs(limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return {"data": fetch_recent_logs(limit)}


@app.delete("/v1/logs/{log_id}")
def delete_log(log_id: int) -> dict:
    removed = delete_chat_log(log_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Log not found")
    return {"status": "deleted", "id": log_id}


def _build_chat_completion(model: str, content: str) -> dict:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


def _stream_event(data: dict | str) -> str:
    if isinstance(data, str):
        return f"data: {data}\n\n"
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _stream_chat_completion(model: str, content: str) -> Iterator[str]:
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())
    chunk_size = 80

    yield _stream_event(
        {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": None,
                }
            ],
        }
    )

    for start in range(0, len(content), chunk_size):
        part = content[start : start + chunk_size]
        yield _stream_event(
            {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": part},
                        "finish_reason": None,
                    }
                ],
            }
        )

    yield _stream_event(
        {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
    )
    yield _stream_event("[DONE]")


@app.post("/v1/chat/completions")
def chat_completions(payload: ChatCompletionRequest):
    user_message = next(
        (message.content for message in reversed(payload.messages) if message.role == "user"),
        None,
    )

    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")

    result = graph.invoke({"user_input": user_message})
    bot_output = result["bot_output"]

    try:
        insert_chat_log(payload.model, user_message, bot_output)
    except Exception as exc:  # pragma: no cover - defensive branch for runtime env issues
        raise HTTPException(status_code=500, detail=f"Failed to write chat log: {exc}") from exc

    if payload.stream:
        return StreamingResponse(
            _stream_chat_completion(payload.model, bot_output),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    return _build_chat_completion(payload.model, bot_output)
