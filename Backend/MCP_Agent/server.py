import asyncio
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp
from openai import RateLimitError
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Playwright Agent Server", version="1.0")

# --- הוספת CORS ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow both localhost and IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

# Use a cheaper model by default
os.environ.setdefault("OPENAI_MODEL", "gpt-4o-mini")

PLAYWRIGHT_MCP_URL = os.getenv("PLAYWRIGHT_MCP_URL", "http://localhost:8931/mcp")

INSTRUCTIONS = """
You are a QA agent controlling a real browser via Playwright (MCP).

Rules:
- Follow the user goal only and stay on the allowed domain.
- Use stable selectors (roles, labels, visible text).
- Keep tool outputs small: do NOT request full page snapshots/DOM dumps.
  When checking page state, only read URL + title + 1-2 key elements.

Behavior:
- Work step by step and verify each action.
- Use human-like actions when possible (hover, slow typing, short waits).

Output format (MUST follow):
- Use short PASS/FAIL per step.
- End with:
  STATE:
  url: <current_url>
  title: <page_title>
  keys: <1-2 key visible elements or indicators>
""".strip()


# ---------------------------
# Rate limit helpers (same logic you wrote)
# ---------------------------

def _parse_retry_after_seconds(msg: str) -> float | None:
    m = re.search(r"Please try again in ([0-9.]+)s", msg)
    return float(m.group(1)) if m else None

def _is_tpm_rate_limit(msg: str) -> bool:
    s = msg.lower()
    return ("tokens per min" in s) or ("tpm" in s) or ("rate limit" in s)

def _is_request_too_large(msg: str) -> bool:
    return "request too large" in msg.lower()

def _shrink_prompt(prompt: str, keep_chars: int = 700) -> str:
    p = prompt.strip()
    if len(p) > keep_chars:
        p = p[:keep_chars].rstrip()
    return p + "\n\nKeep outputs extremely short."

async def run_with_tpm_fallback(agent: Agent, user_prompt: str, max_attempts: int = 4):
    prompt = user_prompt
    for attempt in range(1, max_attempts + 1):
        try:
            return await Runner.run(agent, prompt)
        except RateLimitError as e:
            msg = str(e)
            if not _is_tpm_rate_limit(msg):
                raise
            retry_after = _parse_retry_after_seconds(msg)
            if retry_after is not None:
                await asyncio.sleep(retry_after + 0.5)
                continue
            if _is_request_too_large(msg):
                prompt = _shrink_prompt(prompt, keep_chars=600)
                os.environ["OPENAI_MODEL"] = "gpt-4o-mini"
                await asyncio.sleep(1.0)
                continue
            await asyncio.sleep(min(2 ** attempt, 10))
    raise RuntimeError("TPM fallback exhausted: still hitting rate limits after retries.")


# ---------------------------
# API models
# ---------------------------

class CreateSessionRequest(BaseModel):
    start_url: str = Field(..., description="Initial URL to open (must be same domain you allow).")
    allowed_domain: str = Field("savingplan.web.app", description="Allowed domain for this session.")

class CreateSessionResponse(BaseModel):
    session_id: str
    snapshot: Optional[dict] = None

class PromptRequest(BaseModel):
    prompt: str
    max_attempts: int = 4

class PromptResponse(BaseModel):
    ok: bool
    session_id: str
    output: str
    snapshot: Optional[dict] = None
    error: Optional[dict] = None

class SessionStateResponse(BaseModel):
    session_id: str
    created_at: float
    last_used_at: float
    last_snapshot: Optional[dict] = None
    history_len: int

# ---------------------------
# Session store
# ---------------------------

@dataclass
class Session:
    session_id: str
    allowed_domain: str
    agent: Agent
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    created_at: float = field(default_factory=lambda: time.time())
    last_used_at: float = field(default_factory=lambda: time.time())
    # Keep it small to reduce tokens
    history: List[str] = field(default_factory=list)
    last_snapshot: Optional[dict] = None


SESSIONS: Dict[str, Session] = {}

# Global MCP connection (kept open)
MCP_SERVER: Optional[MCPServerStreamableHttp] = None

# FastAPI with lifespan startup/shutdown

@app.on_event("startup")
async def startup():
    global MCP_SERVER
    MCP_SERVER = MCPServerStreamableHttp(
        name="playwright-local",
        params={"url": PLAYWRIGHT_MCP_URL, "timeout": 120},
        cache_tools_list=True,
        client_session_timeout_seconds=180,
    )
    # Open MCP connection ONCE and keep it open
    await MCP_SERVER.__aenter__()


@app.on_event("shutdown")
async def shutdown():
    global MCP_SERVER
    if MCP_SERVER is not None:
        await MCP_SERVER.__aexit__(None, None, None)
        MCP_SERVER = None


def _assert_domain(url: str, allowed_domain: str):
    # Very simple guard; you can harden it (urlparse etc.)
    if allowed_domain not in url:
        raise HTTPException(status_code=400, detail=f"URL must be within allowed domain: {allowed_domain}")


def _build_agent(allowed_domain: str) -> Agent:
    if MCP_SERVER is None:
        raise RuntimeError("MCP server not initialized")
    # Domain restriction is enforced primarily by instructions + your own checks.
    # You can also add more hard checks in prompts.
    return Agent(
        name="UI Test Runner",
        instructions=INSTRUCTIONS + f"\n\nHard rule: Stay only on domain: {allowed_domain}",
        mcp_servers=[MCP_SERVER],
    )


def _compose_prompt(session: Session, user_prompt: str) -> str:
    # Keep context tiny: last snapshot + last 2 outputs max
    recent = session.history[-2:]
    snap = session.last_snapshot or {}

    context_lines = []
    if snap:
        context_lines.append("CURRENT_STATE (from server memory):")
        context_lines.append(f"url: {snap.get('url', '')}")
        context_lines.append(f"title: {snap.get('title', '')}")
        context_lines.append(f"keys: {snap.get('keys', '')}")

    if recent:
        context_lines.append("RECENT_RESULTS (most recent last):")
        for r in recent:
            # keep short
            context_lines.append(r[:600])

    # Important: ask agent to *continue in the already-open browser*
    # and not to restart unless necessary.
    return "\n".join([
        f"You are continuing an existing browser session. Do NOT restart the browser unless absolutely required.",
        f"Allowed domain: {session.allowed_domain}.",
        *context_lines,
        "",
        "USER_REQUEST:",
        user_prompt.strip(),
        "",
        "Remember: keep outputs short and end with STATE: url/title/keys.",
    ])


def _extract_state_block(output: str) -> Optional[dict]:
    # Expect the agent to end with:
    # STATE:
    # url: ...
    # title: ...
    # keys: ...
    m = re.search(r"STATE:\s*?\nurl:\s*(.*)\ntitle:\s*(.*)\nkeys:\s*(.*)\s*$", output.strip(), re.IGNORECASE)
    if not m:
        return None
    return {"url": m.group(1).strip(), "title": m.group(2).strip(), "keys": m.group(3).strip()}


# ---------------------------
# Endpoints
# ---------------------------

@app.post("/sessions", response_model=CreateSessionResponse)
async def create_session(req: CreateSessionRequest):
    _assert_domain(req.start_url, req.allowed_domain)

    session_id = uuid.uuid4().hex
    agent = _build_agent(req.allowed_domain)

    s = Session(
        session_id=session_id,
        allowed_domain=req.allowed_domain,
        agent=agent,
    )
    SESSIONS[session_id] = s

    # Initial navigation prompt (short and controlled)
    init_prompt = (
        f"Go to {req.start_url}.\n"
        f"Confirm page loaded.\n"
        f"Do not log in unless asked.\n"
        f"End with STATE."
    )

    async with s.lock:
        s.last_used_at = time.time()
        run = await run_with_tpm_fallback(s.agent, _compose_prompt(s, init_prompt), max_attempts=4)
        out = (run.final_output or "").strip()
        s.history.append(out[:1200])
        snap = _extract_state_block(out)
        s.last_snapshot = snap

    return CreateSessionResponse(session_id=session_id, snapshot=s.last_snapshot)


@app.post("/sessions/{session_id}/prompt", response_model=PromptResponse)
async def send_prompt(session_id: str, req: PromptRequest):
    s = SESSIONS.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # Optional: tiny domain guard inside prompt (the agent also has it)
    # If user tries to escape domain, block it.
    if "http" in req.prompt and s.allowed_domain not in req.prompt:
        raise HTTPException(status_code=400, detail=f"Prompt contains URL outside allowed domain: {s.allowed_domain}")

    async with s.lock:
        s.last_used_at = time.time()
        try:
            composed = _compose_prompt(s, req.prompt)
            run = await run_with_tpm_fallback(s.agent, composed, max_attempts=req.max_attempts)
            out = (run.final_output or "").strip()

            s.history.append(out[:1200])
            # Keep history bounded
            if len(s.history) > 10:
                s.history = s.history[-10:]

            snap = _extract_state_block(out)
            if snap:
                s.last_snapshot = snap

            return PromptResponse(ok=True, session_id=session_id, output=out, snapshot=s.last_snapshot)

        except Exception as e:
            err = {"type": type(e).__name__, "message": str(e)}
            return PromptResponse(ok=False, session_id=session_id, output="", snapshot=s.last_snapshot, error=err)


@app.get("/sessions/{session_id}", response_model=SessionStateResponse)
async def get_session(session_id: str):
    s = SESSIONS.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionStateResponse(
        session_id=session_id,
        created_at=s.created_at,
        last_used_at=s.last_used_at,
        last_snapshot=s.last_snapshot,
        history_len=len(s.history),
    )


@app.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    s = SESSIONS.pop(session_id, None)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    # Note: closing actual browser/page depends on MCP tool support.
    # For now we just drop the session reference.
    return {"ok": True, "session_id": session_id}
