import asyncio
import os
import re
import sys
import time
import uuid
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp
from openai import RateLimitError, AsyncOpenAI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for failure_analyzer import
sys.path.insert(0, str(Path(__file__).parent.parent))
from failure_analyzer import FailureAnalyzer, is_failure_event

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

from agents import set_tracing_disabled
set_tracing_disabled(True)



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
- IMPORTANT: Always set the viewport size to 1920x1080 for high-definition screenshots.

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

# Represents a single test scenario suggested by the AI after analyzing the page
class TestSuggestion(BaseModel):
    id: str = Field(..., description="Unique identifier for the suggestion")
    title: str = Field(..., description="Short, descriptive title of the test")
    description: str = Field(..., description="Full explanation of what the test will verify")


class CreateSessionRequest(BaseModel):
    start_url: str = Field(..., description="Initial URL to open (must be same domain you allow).")
    allowed_domain: str = Field("savingplan.web.app", description="Allowed domain for this session.")

class CreateSessionResponse(BaseModel):
    session_id: str
    snapshot: Optional[dict] = None
    suggestions: Optional[List[TestSuggestion]] = []

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
    ws: Optional[WebSocket] = None

    frame_sockets: List[WebSocket] = field(default_factory=list)
    frame_task: Optional[asyncio.Task] = None



SESSIONS: Dict[str, Session] = {}

# Global MCP connection (kept open)
MCP_SERVER: Optional[MCPServerStreamableHttp] = None

# Global Failure Analyzer instance
FAILURE_ANALYZER: Optional[FailureAnalyzer] = None

# FastAPI with lifespan startup/shutdown

@app.on_event("startup")
async def startup():
    global MCP_SERVER, FAILURE_ANALYZER
    MCP_SERVER = MCPServerStreamableHttp(
        name="playwright-local",
        params={"url": PLAYWRIGHT_MCP_URL, "timeout": 120},
        cache_tools_list=True,
        client_session_timeout_seconds=180,
    )
    # Open MCP connection ONCE and keep it open
    await MCP_SERVER.__aenter__()
    
    # Initialize Failure Analyzer (uses same OpenAI API key from env)
    FAILURE_ANALYZER = FailureAnalyzer(
        openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    )
    print("Failure Analyzer initialized")


@app.on_event("shutdown")
async def shutdown():
    global MCP_SERVER
    if MCP_SERVER is not None:
        await MCP_SERVER.__aexit__(None, None, None)
        MCP_SERVER = None


# ---------------------------
# Helper Functions
# ---------------------------

def format_live_step(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Transforms raw MCP logs into beautiful, human-readable steps.
    """
    # We only care about tool calls or specific events
    event_type = payload.get("type", "")
    data = str(payload.get("data", ""))
    data_lower = data.lower()

    # 1. Navigation
    if "goto" in data_lower or "navigat" in data_lower:
        # Extract URL if possible
        url_match = re.search(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", data)
        url = url_match.group(0) if url_match else "target page"
        return {
            "type": "execution_step",
            "data": {
                "icon": "🌐",
                "action": "Navigating",
                "details": f"to {url}",
                "timestamp": time.strftime("%H:%M:%S"),
                "status": "info"
            }
        }

    # 2. Clicks
    if "click" in data_lower:
        # Try to extract selector
        selector = "element"
        if "selector=" in data:
            selector = data.split("selector=")[1].split(" ")[0]
        elif "'" in data:
             parts = data.split("'")
             if len(parts) > 1:
                 selector = parts[1]
        
        return {
            "type": "execution_step",
            "data": {
                "icon": "🖱️",
                "action": "Clicking",
                "details": selector,
                "timestamp": time.strftime("%H:%M:%S"),
                "status": "info"
            }
        }

    # 3. Typing / Filling
    if "fill" in data_lower or "type" in data_lower:
        return {
            "type": "execution_step",
            "data": {
                "icon": "⌨️",
                "action": "Typing",
                "details": "input data...",
                "timestamp": time.strftime("%H:%M:%S"),
                "status": "info"
            }
        }
    
    # 4. Screenshots
    if "screenshot" in data_lower:
        return {
            "type": "execution_step",
            "data": {
                "icon": "📸",
                "action": "Capturing",
                "details": "visual state",
                "timestamp": time.strftime("%H:%M:%S"),
                "status": "info"
            }
        }

    # 5. Final / Success
    if event_type == "final" or "run completed" in data_lower:
         return {
            "type": "execution_step",
            "data": {
                "icon": "✅",
                "action": "Test Completed",
                "details": "The session finished successfully.",
                "timestamp": time.strftime("%H:%M:%S"),
                "status": "success"
            }
        }

    # 6. Generic Logs (Fallback) - Catch-all for other tool events or logs
    # We want to avoid sending raw JSON, so we wrap everything else.
    if event_type in ["log", "tool_call", "tool_result", "info"] or data:
         # Clean up data if it's a dict string or too long
         clean_details = data[:100] + "..." if len(data) > 100 else data
         
         return {
            "type": "execution_step",
            "data": {
                "icon": "ℹ️",
                "action": "Processing",
                "details": clean_details,
                "timestamp": time.strftime("%H:%M:%S"),
                "status": "info"
            }
        }
    
    return None

async def process_and_send_log(websocket: WebSocket, payload: Dict[str, Any]):
    print(f"🪝 PROCESSING: {payload}") # לוג לטרמינל
    
    # בדיקה האם המנתח קיים
    if FAILURE_ANALYZER:
        # בדיקה האם האירוע הוא שגיאה
        is_fail = is_failure_event(payload)
        print(f"🔍 Is Failure? {is_fail}")

        if is_fail:
            print(f"🔴 Failure Detected! Analyzing...")
            try:
                analysis = await FAILURE_ANALYZER.analyze(payload)
                if analysis.get("status") != "ignored_non_failure_log":
                    smart_payload = {
                        "type": "failure_analysis",
                        "data": analysis
                    }
                    await websocket.send_json(smart_payload)
                    return 
            except Exception as e:
                print(f"❌ Analysis failed: {e}")
    
    # STRICT TRANSFORMATION: Never send raw payload
    try:
        formatted = format_live_step(payload)
        if formatted:
            await websocket.send_json(formatted)
        else:
            # If format_live_step returns None, it means we decided to ignore this log.
            # Do NOT send raw payload.
            pass
    except Exception as e:
        print(f"⚠️ Failed to send log via WS: {e}")
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


# NEW/STAY: Shared utility function that can be called from multiple endpoints
async def _generate_page_suggestions(session: Session) -> List[dict]:
    analysis_prompt = """
        You are a senior QA engineer analyzing the CURRENT VIEW of a live web page via Playwright.

        MISSION:
        Generate 5-10 high-impact test ideas that target REAL RISKS visible on this specific page.
        Prioritize tests that would catch regressions, security issues, broken flows, or critical UX failures.

        HARD CONSTRAINTS:
        1. Analyze ONLY what's visible/interactive RIGHT NOW (no assumptions about other pages)
        2. Each test MUST reference a specific element on THIS page (button name, form field, nav link, modal, table, banner, CTA, etc.)
        3. NO step-by-step instructions - provide test concepts only
        4. NO implementation details (Playwright, selectors, code)
        5. Avoid generic tests ("page loads") unless tied to a critical page-specific indicator

        COVERAGE MATRIX (use what exists on the page):
        ✓ Critical user flows (primary CTA, main conversion path)
        ✓ Form validation (required fields, format rules, boundary cases, empty submit)
        ✓ Authentication/Authorization signals (login gates, role-based visibility, session timeout indicators)
        ✓ Navigation integrity (menu links, breadcrumbs, back/forward, deep links)
        ✓ Error handling (invalid input, 404 states, empty results, disabled actions)
        ✓ Async content (loading states, race conditions, stale data)
        ✓ Security vectors (XSS inputs, CSRF tokens if forms exist, rate limiting hints, unsafe redirects)
        ✓ Accessibility (keyboard navigation, focus traps, ARIA labels, color contrast issues)
        ✓ Layout/Responsive integrity (overlapping elements, clipped CTAs, mobile breakpoints if testable)
        ✓ Data correctness (prices, dates, totals, counts, status indicators)

        QUALITY BAR:
        - Each test must target a DISTINCT risk
        - Prefer tests that validate user value over technical minutiae
        - If the page is complex → aim for 10 tests covering breadth
        - If the page is simple → 5-7 focused tests on depth (edge cases, accessibility, validation)
        - Balance: 40% happy path + 30% validation/errors + 30% security/accessibility

        OUTPUT FORMAT (STRICT JSON):
        [
        {
            "id": "descriptive-slug-format",
            "title": "Concise test name (≤70 chars)",
            "description": "1-3 sentences. Must mention the specific visible element(s) being tested and why it matters. Explain the risk/value clearly."
        }
        ]

        RULES:
        - Return ONLY valid JSON (no markdown, no code fences, no commentary)
        - "id" format: lowercase-with-hyphens (e.g., "signup-empty-email-validation")
        - "title" max 70 characters
        - "description" must reference at least ONE concrete element from the current view

        Now analyze the page and generate the JSON array.
        """.strip()
    try:
        run = await run_with_tpm_fallback(session.agent, analysis_prompt)
        content = run.final_output.strip()
        match = re.search(r"(\[.*\])", content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except Exception as e:
        print(f"Discovery error: {e}")
    return []



# ---------------------------

FRAME_FPS = 20
FRAME_INTERVAL = 1.0 / FRAME_FPS
FRAME_JPEG_QUALITY = 70

from typing import Optional

async def _grab_frame_data_url() -> Optional[str]:
    if MCP_SERVER is None:
        print("[frames] MCP_SERVER is None")
        return None

    try:
        result = await MCP_SERVER.call_tool(
            "browser_take_screenshot",
            {"format": "jpeg", "quality": 70},
        )
    except Exception as e:
        print("[frames] browser_take_screenshot failed:", repr(e))
        return None

    # result is CallToolResult
    content = getattr(result, "content", None)
    if not content:
        print("[frames] CallToolResult has no content")
        return None

    # Find first image content
    for item in content:
        # item is usually mcp.types.ImageContent
        mime = getattr(item, "mimeType", None) or getattr(item, "mime", None)
        data = getattr(item, "data", None)

        if data and mime:
            return f"data:{mime};base64,{data}"

    # If we got here, response shape is unexpected
    print("[frames] No image item in content. content types:", [type(x) for x in content])
    return None

async def _frames_loop(s: Session):
    try:
        while s.frame_sockets:
            try:
                frame = await _grab_frame_data_url()
                
                if frame:
                    payload = {
                        "type": "frame",
                        "ts": time.time(),
                        "mime": "image/jpeg",
                        "frame": frame,
                    }

                    for ws in list(s.frame_sockets):
                        try:
                            await ws.send_json(payload)
                        except Exception:
                            if ws in s.frame_sockets:
                                s.frame_sockets.remove(ws)

            except Exception as e:
                # לא מפילים את הלולאה
                 print("[frames] loop error:", repr(e))

            await asyncio.sleep(FRAME_INTERVAL)

    finally:
        s.frame_task = None


@app.websocket("/ws/sessions/{session_id}/frames")
async def frames_ws(ws: WebSocket, session_id: str):
    s = SESSIONS.get(session_id)
    if not s:
        await ws.close(code=1008)
        return

    await ws.accept()
    s.frame_sockets.append(ws)
    print(f"FRAMES WS CONNECTED: session={session_id}")

    if s.frame_task is None:
        s.frame_task = asyncio.create_task(_frames_loop(s))

    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        pass
    finally:
        if ws in s.frame_sockets:
            s.frame_sockets.remove(ws)
        print(f"FRAMES WS DISCONNECTED: session={session_id}")


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

    suggestions_data = []

    async with s.lock:
        s.last_used_at = time.time()
        run = await run_with_tpm_fallback(s.agent, _compose_prompt(s, init_prompt), max_attempts=4)
        out = (run.final_output or "").strip()
        s.history.append(out[:1200])
        s.last_snapshot = _extract_state_block(out)
        suggestions_data = await _generate_page_suggestions(s)

    return CreateSessionResponse(session_id=session_id, snapshot=s.last_snapshot, suggestions=suggestions_data)


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

            run = Runner.run_streamed(s.agent, composed, max_turns=50)

            final_output = None
            collected_events = []  # Collect events for potential failure analysis

            async for event in run.stream_events():
                payload = {
                    "type": event.type,
                    "data": None,
                }

                if hasattr(event, "item") and event.item:
                    payload["data"] = str(event.item)

                # Collect event for failure analysis
                collected_events.append(payload)

                # Stream live to WebSocket
                if s.ws:
                    await process_and_send_log(s.ws, payload)
                
                # (Redundant analysis block removed - handled by process_and_send_log)


            out = (getattr(run, "final_output", None) or "").strip()

            # Check final output for failures as well
            if FAILURE_ANALYZER and out:
                final_event = {"type": "final_output", "data": out}
                # We send this to process_and_send_log to handle analysis, 
                # but we might not want to send the raw final output as a log event if it's just text.
                # However, process_and_send_log will send it if it's not a failure.
                # The original code didn't send final_event raw.
                # So we only invoke analysis here manually if we don't want to send raw.
                # But to keep it consistent with "Central Gateway", let's just analyze it manually 
                # and send the result via process_and_send_log if it IS a failure.
                
                if is_failure_event(final_event):
                    try:
                        analysis = await FAILURE_ANALYZER.analyze(final_event)
                        if analysis.get("status") != "ignored_non_failure_log":
                            if s.ws:
                                await process_and_send_log(s.ws, {
                                    "type": "failure_analysis",
                                    "data": analysis
                                })
                    except Exception as analysis_err:
                        print(f"Final output analysis error: {analysis_err}")

            if s.ws:
                await process_and_send_log(s.ws, {
                    "type": "final",
                    "data": "run completed"
                })

            s.history.append(out[:1200])
            if len(s.history) > 10:
                s.history = s.history[-10:]

            snap = _extract_state_block(out)
            if snap:
                s.last_snapshot = snap

            return PromptResponse(
                ok=True,
                session_id=session_id,
                output=out,
                snapshot=s.last_snapshot
            )

        except Exception as e:
            err = {"type": type(e).__name__, "message": str(e)}
            
            # Analyze the exception as a failure
            if FAILURE_ANALYZER:
                try:
                    error_event = {
                        "type": "error",
                        "message": str(e),
                        "error_type": type(e).__name__
                    }
                    # We can send this error event to process_and_send_log to handle it!
                    if s.ws:
                         await process_and_send_log(s.ws, error_event)
                except Exception as analysis_err:
                    print(f"Exception analysis error: {analysis_err}")
            
            return PromptResponse(ok=False, session_id=session_id, output="", snapshot=s.last_snapshot, error=err)


@app.post("/sessions/{session_id}/suggest")
async def suggest_test(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get context: either the last snapshot or just the allowed domain/url
    context = f"Allowed Domain: {session.allowed_domain}"
    if session.last_snapshot:
        context += f"\nCurrent URL: {session.last_snapshot.get('url')}"
        context += f"\nPage Title: {session.last_snapshot.get('title')}"
        context += f"\nVisible Elements: {session.last_snapshot.get('keys')}"
    
    # 1. Extract History (Last 5 actions)
    recent_history = session.history[-5:] if session.history else []
    history_text = "\n".join([f"- {h}" for h in recent_history]) if recent_history else "None"

    try:
        client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are a QA Lead. Suggest the NEXT logical test step for a Playwright automation agent.
CRITICAL RULES:
1. Look at the `RECENT_ACTIONS`. **DO NOT** repeat a suggestion that was just made.
2. If the main path (e.g., Login) was just attempted, suggest a **Negative Test** (invalid input), a **Secondary Action** (Forgot Password, links), or **Navigation** (Go Back, Home).
3. Output ONLY the prompt text. Do not include quotes or explanations."""},
                {"role": "user", "content": f"Context: {context}\n\nRECENT_ACTIONS:\n{history_text}"}
            ],
            max_tokens=60,
            temperature=0.7
        )
        suggestion = response.choices[0].message.content.strip()
        return {"suggestion": suggestion}
    except Exception as e:
        print(f"Suggestion failed: {e}")
        return {"suggestion": "Verify the page title and main heading."}


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

@app.get("/sessions/{session_id}/suggestions", response_model=List[TestSuggestion])
async def get_manual_suggestions(session_id: str):
    s = SESSIONS.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    
    async with s.lock:
        s.last_used_at = time.time()
        # Call the shared utility function
        return await _generate_page_suggestions(s)


@app.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    s = SESSIONS.pop(session_id, None)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    # Note: closing actual browser/page depends on MCP tool support.
    # For now we just drop the session reference.
    return {"ok": True, "session_id": session_id}




@app.websocket("/ws/sessions/{session_id}")
async def session_ws(ws: WebSocket, session_id: str):
    s = SESSIONS.get(session_id)
    if not s:
        await ws.close(code=1008)
        return

    await ws.accept()
    s.ws = ws
    print(f"WS CONNECTED: session={session_id}")

    try:
        while True:
            # keep connection alive; we don't expect messages from client
            await ws.receive_text()
    except WebSocketDisconnect:
        print(f"WS DISCONNECTED: session={session_id}")
    finally:
        if s.ws is ws:
            s.ws = None
