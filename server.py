#!/usr/bin/env python3
"""Kaka.ai API server — exposes the agent over HTTP.

Run:  ./venv/bin/python server.py [--host 127.0.0.1] [--port 8900]
Endpoints:
  GET  /health              -> status info
  GET  /tools               -> available tools
  POST /chat                -> {"message": "...", "session_id": "...", "model": "..."}
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.agent import Agent
from core.config import Config

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

API_TOKEN = os.getenv("KAKA_API_KEY", "").strip()
# CORS: default to loopback (a website must not drive your agent). Set
# KAKA_CORS_ORIGINS to a comma-separated list to allow others.
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("KAKA_CORS_ORIGINS", "").split(",") if o.strip()] or [
    "http://localhost",
    "http://127.0.0.1",
]

app = FastAPI(title="Kaka.ai", version="2.2", description="Autonomous AI agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=False,
)

_sessions: dict[str, dict] = {}
_sessions_lock = threading.Lock()
_MAX_SESSIONS = 200


def _require_auth(authorization: str | None = Header(default=None)) -> None:
    """Enforce a bearer token when KAKA_API_KEY is configured."""
    if not API_TOKEN:
        return  # no key set — loopback-only by default (see --host)
    if not authorization or authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized — set KAKA_API_KEY on the server")


def _prune_sessions() -> None:
    """Drop oldest sessions past the cap so one client can't leak memory."""
    while len(_sessions) > _MAX_SESSIONS:
        oldest = min(_sessions, key=lambda k: _sessions[k]["ts"])
        del _sessions[oldest]


def _get_agent(session_id: str, model: str | None = None) -> Agent:
    if len(session_id) > 64:
        raise HTTPException(status_code=400, detail="session_id too long (max 64 chars)")
    if model and len(model) > 128:
        raise HTTPException(status_code=400, detail="model too long (max 128 chars)")
    key = f"{session_id}::{model or ''}"
    with _sessions_lock:
        if key not in _sessions:
            cfg = Config.from_env()
            cfg.verbose = False
            if model:
                cfg.model = model
            _sessions[key] = {"ts": time.time(), "agent": Agent(config=cfg)}
        else:
            _sessions[key]["ts"] = time.time()
        _prune_sessions()
        return _sessions[key]["agent"]


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    model: str | None = None

    @field_validator("message")
    @classmethod
    def _message_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message must not be empty")
        if len(v) > 4000:
            raise ValueError("message too long (max 4000 chars)")
        return v


@app.get("/health")
def health():
    cfg = Config.from_env()
    return {
        "status": "ok",
        "agent": "Kaka.ai",
        "provider": cfg.provider,
        "model": cfg.model,
        "fallback_models": cfg.fallback_models,
        "active_sessions": len(_sessions),
        "auth_required": bool(API_TOKEN),
        "bind_safe": "loopback-only recommended (use --host 127.0.0.1)",
    }


@app.get("/tools")
def tools():
    reg = type(_get_agent("probe").tools)()
    from core.builtins import register_built_in_tools

    register_built_in_tools(reg)
    return {"count": len(reg.list_tools()), "tools": [t["name"] for t in reg.list_tools()]}


@app.post("/chat")
def chat(req: ChatRequest, authorization: str | None = Header(default=None)):
    _require_auth(authorization)
    agent = _get_agent(req.session_id, req.model)
    try:
        response = agent.chat(req.message)
        return {
            "session_id": req.session_id,
            "model": agent.config.model,
            "response": response,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)[:300])


@app.post("/reset")
def reset(session_id: str = "default", authorization: str | None = Header(default=None)):
    _require_auth(authorization)
    if len(session_id) > 64:
        raise HTTPException(status_code=400, detail="session_id too long (max 64 chars)")
    with _sessions_lock:
        removed = [k for k in _sessions if k.split("::")[0] == session_id]
        for k in removed:
            del _sessions[k]
    return {"reset": session_id, "sessions_cleared": len(removed)}


def main() -> None:
    parser = argparse.ArgumentParser(prog="kaka-server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8900)
    args = parser.parse_args()

    if args.host not in ("127.0.0.1", "localhost", "::1") and not API_TOKEN:
        logging.warning(
            "Binding to a non-loopback host without KAKA_API_KEY exposes an RCE-capable "
            "agent to the network. Set KAKA_API_KEY first."
        )

    logging.basicConfig(level=logging.INFO)
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
