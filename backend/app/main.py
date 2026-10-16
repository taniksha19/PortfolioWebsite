"""FastAPI service that streams the portfolio agent's run to the browser as Server-Sent Events."""

import json
import logging
import os
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .graph import run_agent
from .llm import LLMUnavailable, model_name, provider, providers

log = logging.getLogger("portfolio-agent")

PER_IP_LIMIT = int(os.getenv("RATE_LIMIT_PER_IP", "15"))  # requests per window
PER_IP_WINDOW = 10 * 60  # seconds
DAILY_LIMIT = int(os.getenv("RATE_LIMIT_DAILY", "300"))  # all visitors combined; keeps Groq's 1,000 requests/day free tier in reach

app = FastAPI(title="Taniksha's portfolio agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:4173").split(",") if o.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class Turn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=6000)
    history: list[Turn] = Field(default_factory=list, max_length=12)


_hits: dict[str, deque] = defaultdict(deque)
_daily = {"day": "", "count": 0}


def _check_rate_limit(ip: str) -> None:
    now = time.time()
    today = time.strftime("%Y-%m-%d", time.gmtime(now))
    if _daily["day"] != today:
        _daily.update(day=today, count=0)
    if _daily["count"] >= DAILY_LIMIT:
        raise HTTPException(429, "The agent has hit its daily limit. Please email Taniksha directly.")
    q = _hits[ip]
    while q and now - q[0] > PER_IP_WINDOW:
        q.popleft()
    if len(q) >= PER_IP_LIMIT:
        raise HTTPException(429, "You're sending messages quickly. Try again in a few minutes.")
    q.append(now)
    _daily["count"] += 1


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    return forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")


@app.get("/api/health")
async def health():
    return {"ok": True, "provider": provider(), "model": model_name(), "providers": providers(), "demo": provider() == "demo"}


@app.post("/api/chat")
async def chat(body: ChatRequest, request: Request):
    _check_rate_limit(_client_ip(request))
    history = [t.model_dump() for t in body.history[-6:]]

    async def events():
        t0 = time.perf_counter()
        try:
            async for event in run_agent(body.message.strip(), history):
                yield f"data: {json.dumps(event)}\n\n"
        except LLMUnavailable:
            log.exception("every LLM provider failed")
            busy = "Nimbus is resting: all of today's free AI capacity is used up. Please try again later, or email Taniksha directly."
            yield f"data: {json.dumps({'type': 'error', 'message': busy})}\n\n"
        except Exception:
            log.exception("agent run failed")
            yield f"data: {json.dumps({'type': 'error', 'message': 'The agent hit an error. Please try again, or email Taniksha.'})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'ms': round((time.perf_counter() - t0) * 1000)})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
