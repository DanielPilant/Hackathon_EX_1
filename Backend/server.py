"""
FastAPI Orchestrator Server

Central hub coordinating:
- Frontend (React @ localhost:5173)
- LLM Module (backend_LLM/) - AI test generation
- Automation Module (Automation/) - Playwright execution
"""

import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Disable stdout buffering for immediate log output
os.environ['PYTHONUNBUFFERED'] = '1'

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

# Add Backend directory to path for imports
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import from backend modules
from backend_LLM.site_context_extractor import fetch_html, extract_site_context
from backend_LLM.session_manager import QASession
from Automation.executor import run_execution_plan


# ============================================================================
# Logging Configuration - Simple and Reliable
# ============================================================================

import traceback

def log_print(level: str, message: str):
    """Simple logging function that always flushes to stdout"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # Color codes
    colors = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
    }
    icons = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
    }
    
    color = colors.get(level, '')
    icon = icons.get(level, '')
    reset = '\033[0m'
    dim = '\033[2m'
    bold = '\033[1m'
    
    line = f"{dim}[{timestamp}]{reset} {icon} {color}{bold}{level:<8}{reset} {message}"
    print(line, flush=True)


class Log:
    """Simple logger class that uses print with flush"""
    @staticmethod
    def debug(msg): log_print('DEBUG', msg)
    @staticmethod
    def info(msg): log_print('INFO', msg)
    @staticmethod
    def warning(msg): log_print('WARNING', msg)
    @staticmethod
    def error(msg): log_print('ERROR', msg)


# Initialize simple logger
log = Log()


# ============================================================================
# Pydantic Models
# ============================================================================

class ConnectRequest(BaseModel):
    """Request model for /api/target endpoint"""
    user_id: str = Field(
        ..., min_length=1, description="User session identifier"
    )
    url: str = Field(..., min_length=1, description="Target website URL")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format"""
        v = v.strip()
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class ScanRequest(BaseModel):
    """Request model for /api/scan endpoint"""
    user_id: str = Field(
        ..., min_length=1, description="User session identifier"
    )
    action: str = Field(
        default="scan", description="Action type (currently unused)"
    )


class PromptRequest(BaseModel):
    """Request model for /api/generate endpoint"""
    user_id: str = Field(
        ..., min_length=1, description="User session identifier"
    )
    prompt: str = Field(
        ..., min_length=1, description="User test generation prompt"
    )


class ConnectResponse(BaseModel):
    """Response model for /api/target endpoint"""
    status: str
    message: str


# ============================================================================
# Global Session Storage
# ============================================================================

# Store QASession instances per user_id
user_sessions: Dict[str, QASession] = {}


# ============================================================================
# Helper Functions
# ============================================================================

def get_user_session(user_id: str) -> QASession:
    """
    Retrieve a user's session or raise HTTPException if not found.

    Args:
        user_id: User session identifier

    Returns:
        QASession instance

    Raises:
        HTTPException: If no session exists for user_id
    """
    if user_id not in user_sessions:
        log.warning(f"Session not found for user: {user_id}")
        raise HTTPException(
            status_code=400,
            detail="No active session. Connect to a target URL first."
        )
    log.debug(f"Retrieved session for user: {user_id}")
    return user_sessions[user_id]


async def stream_execution_events(plan_json: Dict[str, Any], user_id: str = "unknown"):
    """
    Async generator that formats executor events as SSE.

    Args:
        plan_json: Test plan JSON from LLM
        user_id: User identifier for logging

    Yields:
        SSE-formatted strings
    """
    step_count = len(plan_json.get("plan", []))
    log.info(f"🚀 Starting execution of {step_count} steps for user: {user_id}")
    
    try:
        async for event in run_execution_plan(plan_json, headless=True):
            # Log each event
            step_id = event.get("step_id", "?")
            status = event.get("status", "unknown")
            action = event.get("action_type", "unknown")
            desc = event.get("description", "")[:50]
            
            if status == "pass":
                log.info(f"   Step {step_id} [{action}] ✓ PASS - {desc}")
            elif status == "fail":
                error = event.get("error_reason", "Unknown error")[:60]
                log.error(f"   Step {step_id} [{action}] ✗ FAIL - {error}")
            elif status == "running":
                log.debug(f"   Step {step_id} [{action}] ⏳ Running - {desc}")
            
            # Format as SSE: "data: {json}\n\n"
            sse_data = f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield sse_data

            # Small delay to ensure frontend receives events properly
            await asyncio.sleep(0.1)
        
        log.info(f"✅ Execution completed for user: {user_id}")

    except Exception as e:
        # Get full traceback for debugging
        tb = traceback.format_exc()
        error_msg = str(e) if str(e) else f"{type(e).__name__}: {tb}"
        log.error(f"💥 Execution error for user {user_id}: {error_msg}")
        log.error(f"   Traceback:\n{tb}")
        
        # Send error event if execution fails catastrophically
        error_event = {
            "step_id": None,
            "status": "fail",
            "action_type": "error",
            "description": "Execution error",
            "error_reason": error_msg[:500],  # Truncate for safety
            "selector": None,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "duration": "0.0s"
        }
        yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="TestFlow AI Orchestrator",
    description="Central API for AI-powered QA automation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Log server startup"""
    log.info("=" * 60)
    log.info("🚀 TestFlow AI Orchestrator Starting...")
    log.info(f"   Python: {sys.executable}")
    log.info(f"   Version: {sys.version.split()[0]}")
    log.info("=" * 60)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.now()
    
    # Log incoming request
    log.info(f"📥 {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.now() - start_time).total_seconds() * 1000
    
    # Log response
    status_icon = "✅" if response.status_code < 400 else "❌"
    log.info(f"📤 {status_icon} {response.status_code} ({duration:.0f}ms)")
    
    return response


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    log.debug(f"Health check - {len(user_sessions)} active sessions")
    return {
        "status": "online",
        "service": "TestFlow AI Orchestrator",
        "active_sessions": len(user_sessions)
    }


@app.post("/api/target", response_model=ConnectResponse)
async def connect_target(request: ConnectRequest):
    """
    Initialize a QA session for a target website.

    Flow:
    1. Fetch HTML from target URL
    2. Extract site context (forms, buttons, links, etc.)
    3. Create new QASession with AI context
    4. Store session for user

    Returns:
        Success message with session confirmation
    """
    log.info(f"🎯 New target connection request")
    log.info(f"   User ID: {request.user_id}")
    log.info(f"   URL: {request.url}")
    
    try:
        # Step 1: Fetch HTML
        log.info(f"   📡 Fetching HTML from target...")
        html = fetch_html(request.url, mode="requests", timeout=15)
        log.info(f"   ✅ HTML fetched ({len(html):,} bytes)")

        # Step 2: Extract context
        log.info(f"   🔍 Extracting site context...")
        context = extract_site_context(request.url, html)
        num_elements = len(context.get('interactive_elements', []))
        num_forms = len(context.get('forms', []))
        log.info(f"   ✅ Context extracted: {num_elements} elements, {num_forms} forms")

        # Step 3: Create QASession
        log.info(f"   🤖 Creating AI session...")
        session = QASession()

        # Step 4: Initialize session with site context
        context_json = json.dumps(context, ensure_ascii=False, indent=2)
        session.start_new_session(request.url, context_json)
        log.info(f"   ✅ AI session initialized with site context")

        # Step 5: Store session
        user_sessions[request.user_id] = session
        log.info(f"   💾 Session stored for user: {request.user_id}")
        log.info(f"   📊 Active sessions: {len(user_sessions)}")

        return ConnectResponse(
            status="success",
            message=f"Target scanned. Found {num_elements} elements."
        )

    except Exception as e:
        log.error(f"   💥 Failed to connect: {str(e)}")
        # Clean up session if it was partially created
        user_sessions.pop(request.user_id, None)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to target: {str(e)}"
        )


@app.post("/api/scan")
async def autonomous_scan(request: ScanRequest):
    """
    Perform autonomous full QA audit of the connected website.

    Flow:
    1. Retrieve user's session
    2. Generate comprehensive test plan via AI
    3. Stream execution events via SSE

    Returns:
        StreamingResponse with Server-Sent Events
    """
    log.info(f"🔬 Autonomous scan request")
    log.info(f"   User ID: {request.user_id}")
    
    try:
        # Step 1: Validate session exists
        session = get_user_session(request.user_id)
        log.info(f"   ✅ Session validated")

        # Step 2: Generate test plan with predefined audit prompt
        audit_prompt = (
            "Perform a comprehensive QA audit: test forms, buttons, "
            "links, check for console errors and accessibility issues"
        )
        
        log.info(f"   🤖 Generating test plan via AI...")
        plan_json = session.generate_test_plan(audit_prompt)
        step_count = len(plan_json.get("plan", []))
        log.info(f"   ✅ Test plan generated: {step_count} steps")
        
        # Log plan summary
        for step in plan_json.get("plan", [])[:5]:  # Show first 5 steps
            log.debug(f"      Step {step.get('step_id')}: {step.get('action')} - {step.get('description', '')[:40]}")
        if step_count > 5:
            log.debug(f"      ... and {step_count - 5} more steps")

        # Step 3: Stream execution via SSE
        log.info(f"   📡 Starting SSE stream...")
        return StreamingResponse(
            stream_execution_events(plan_json, request.user_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"   💥 Scan failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Scan execution failed: {str(e)}"
        )


@app.post("/api/generate")
async def generate_custom_test(request: PromptRequest):
    """
    Generate and execute custom test based on user prompt.

    Flow:
    1. Retrieve user's session
    2. Generate test plan from user prompt
    3. Stream execution events via SSE

    Returns:
        StreamingResponse with Server-Sent Events
    """
    log.info(f"🎨 Custom test generation request")
    log.info(f"   User ID: {request.user_id}")
    log.info(f"   Prompt: \"{request.prompt[:60]}{'...' if len(request.prompt) > 60 else ''}\"")
    
    try:
        # Step 1: Validate session exists
        session = get_user_session(request.user_id)
        log.info(f"   ✅ Session validated")

        # Step 2: Generate test plan from user prompt
        log.info(f"   🤖 Generating test plan via AI...")
        plan_json = session.generate_test_plan(request.prompt)
        step_count = len(plan_json.get("plan", []))
        log.info(f"   ✅ Test plan generated: {step_count} steps")
        
        # Log plan summary
        for step in plan_json.get("plan", [])[:5]:  # Show first 5 steps
            log.debug(f"      Step {step.get('step_id')}: {step.get('action')} - {step.get('description', '')[:40]}")
        if step_count > 5:
            log.debug(f"      ... and {step_count - 5} more steps")

        # Step 3: Stream execution via SSE
        log.info(f"   📡 Starting SSE stream...")
        return StreamingResponse(
            stream_execution_events(plan_json, request.user_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"   💥 Test generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Test generation failed: {str(e)}"
        )


# ============================================================================
# Session Management Endpoints (Optional Utilities)
# ============================================================================

@app.get("/api/sessions")
async def list_sessions():
    """List all active user sessions (for debugging)"""
    log.info(f"📋 Listing sessions: {len(user_sessions)} active")
    return {
        "active_sessions": list(user_sessions.keys()),
        "count": len(user_sessions)
    }


@app.delete("/api/sessions/{user_id}")
async def clear_session(user_id: str):
    """Clear a specific user session"""
    log.info(f"🗑️ Session delete request for: {user_id}")
    if user_id in user_sessions:
        del user_sessions[user_id]
        log.info(f"   ✅ Session {user_id} cleared")
        log.info(f"   📊 Remaining sessions: {len(user_sessions)}")
        return {"status": "success", "message": f"Session {user_id} cleared"}
    else:
        log.warning(f"   ⚠️ Session not found: {user_id}")
        raise HTTPException(status_code=404, detail="Session not found")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Startup banner
    print("\n" + "=" * 60)
    print("  🧪 TestFlow AI Orchestrator")
    print("=" * 60)
    print(f"  Python: {sys.executable}")
    print(f"  Version: {sys.version.split()[0]}")
    print(f"  Server: http://localhost:8000")
    print(f"  Docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
