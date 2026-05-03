# AI-Powered Browser Automation & QA Platform

A production-grade, full-stack platform that lets you control a real browser with natural language, watch it live in a web UI, and automatically analyze failures using AI — all containerized and observable out of the box.

---

## Table of Contents

1. [Problem & Solution](#1-problem--solution)
2. [Architecture Overview](#2-architecture-overview)
3. [Repository Structure](#3-repository-structure)
4. [Component Deep Dive](#4-component-deep-dive)
5. [Data Flow](#5-data-flow)
6. [WebSocket Layer](#6-websocket-layer)
7. [Observability Stack](#7-observability-stack)
8. [Environment Variables](#8-environment-variables)
9. [Setup & Installation](#9-setup--installation)
10. [Running the Platform](#10-running-the-platform)
11. [API Reference](#11-api-reference)
12. [Troubleshooting](#12-troubleshooting)
13. [Example Usage](#13-example-usage)
14. [Roadmap](#14-roadmap)
15. [Tech Stack](#15-tech-stack)

---

## 1. Problem & Solution

### Problem

Traditional browser automation requires engineers to write brittle, maintenance-heavy Playwright/Selenium scripts. These scripts break every time the UI changes, produce cryptic errors, and give no live visibility into what the browser is actually doing while a test runs.

### Solution

This platform wraps Playwright inside an AI agent loop driven by OpenAI function calling. You describe what to test in plain English; the agent translates that into Playwright tool calls, executes them in a real headless Chromium browser, streams JPEG screenshots to a React dashboard at 20 FPS, and uses a secondary AI pipeline to classify and explain any failures in structured JSON — all in real time.

**Key properties:**
- **Zero-script QA** — natural language replaces Playwright code
- **Live visual feed** — browser screenshots streamed over WebSocket at 20 FPS
- **AI failure analysis** — rule-based + LLM pipeline categorizes and explains errors
- **Domain-sandboxed sessions** — each test session is locked to one allowed domain
- **Full-stack observability** — distributed tracing (Tempo), structured logs (Loki), metrics (Prometheus), all queryable via Grafana

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                                   │
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                    React Frontend  :5173                           │    │
│   │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │    │
│   │  │ControlPanel  │  │  VideoPlayer │  │     ResultsLog         │  │    │
│   │  │(URL, prompt) │  │ (live JPEG   │  │(steps, failures, AI    │  │    │
│   │  │              │  │  frames)     │  │ analysis, suggestions) │  │    │
│   │  └──────┬───────┘  └──────┬───────┘  └───────────┬────────────┘  │    │
│   │         │  REST/HTTP       │  WS /frames           │  WS /session  │    │
│   └─────────┼──────────────────┼───────────────────────┼───────────────┘    │
└─────────────┼──────────────────┼───────────────────────┼─────────────────────┘
              │                  │                        │
              ▼                  ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend  :8000  (mcp-api)                     │
│                                                                             │
│  POST /sessions ──► Agent bootstrap + initial page load                    │
│  POST /sessions/{id}/prompt ──► Agent loop, streams events over WS         │
│  GET  /sessions/{id}/suggestions ──► AI-generated test ideas               │
│  WS   /ws/sessions/{id} ──► Live step events → failure_analyzer → frontend │
│  WS   /ws/sessions/{id}/frames ──► 20 FPS JPEG screenshot stream           │
│                                                                             │
│  ┌──────────────────────┐    ┌──────────────────────────────────────────┐  │
│  │   openai-agents SDK  │    │         FailureAnalyzer                  │  │
│  │   (Agent + Runner)   │    │  normalize → classify → OpenAI explain   │  │
│  └──────────┬───────────┘    └──────────────────────────────────────────┘  │
└─────────────┼───────────────────────────────────────────────────────────────┘
              │  MCP over HTTP  http://playwright-mcp:8931/mcp
              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│               Playwright MCP Server  :8931  (playwright-mcp)                │
│                                                                             │
│   @playwright/mcp  ──►  Chromium (headless, shared context)                │
│   Tools exposed: browser_navigate, browser_click, browser_fill,            │
│                  browser_take_screenshot, browser_snapshot, …              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Observability Stack                                 │
│                                                                             │
│  otel-collector:4317  ──► Tempo:3200 (traces)                              │
│  otel-collector:8889  ──► Prometheus:9090 (metrics) ──► Grafana:3000       │
│  promtail ──────────────► Loki:3100 (logs) ──────────► Grafana:3000        │
│  cadvisor:8081  ──► Prometheus (container metrics)                         │
│  node-exporter:9100 ──► Prometheus (host metrics)                         │
│  ops-hub:7070  (Nginx dashboard linking all tools)                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Startup Dependency Chain

```
playwright-mcp (healthy)
       ↓
otel-collector (started)
       ↓
mcp-api (healthy)
       ↓
frontend (healthy)
       ↓
ops-hub
```

---

## 3. Repository Structure

```
Hackathon_EX_1/
│
├── docker-compose.yml              # Full stack: 13 services, 1 command
│
├── Backend/
│   ├── MCP_Agent/
│   │   ├── server.py               # FastAPI app — all routes, WS endpoints,
│   │   │                           #   agent logic, frames loop
│   │   ├── requirements.txt        # Python dependencies
│   │   ├── Dockerfile.dev          # python:3.12-slim image
│   │   ├── .env                    # Runtime secrets (git-ignored)
│   │   └── .env.example            # Template for all required env vars
│   │
│   ├── failure_analyzer/           # Self-contained failure analysis module
│   │   ├── analyzer.py             # Orchestrator: normalize → classify → explain
│   │   ├── normalizer.py           # Extracts structured fields from raw MCP JSON
│   │   ├── classifier.py           # Rule-based pre-classifier (no AI needed)
│   │   ├── openai_client.py        # Async OpenAI wrapper for explanations
│   │   ├── prompts.py              # LLM prompt templates
│   │   ├── schemas.py              # Pydantic models (FailureCategory, FailureAnalysis)
│   │   ├── test_cli.py             # Interactive CLI for manual testing
│   │   ├── test_fixtures.py        # Reusable test fixture events
│   │   └── tests/                  # pytest suite (no OpenAI required in CI)
│   │
│   ├── playwright-mcp/
│   │   └── Dockerfile              # node:22-slim + @playwright/mcp@latest
│   │                               #   + chromium installed via MCP's bundled
│   │                               #     playwright CLI (version-pinned)
│   │
│   ├── run_e2e.py                  # Standalone e2e test runner script
│   └── run_savingplan_suite.py     # Domain-specific test suite runner
│
├── frontend/
│   └── client/
│       ├── src/
│       │   ├── App.jsx             # Root layout: resizable panels
│       │   ├── config.js           # API_BASE_URL, WS URLs, buildWsCandidates()
│       │   ├── api.js              # Thin HTTP wrappers
│       │   ├── components/
│       │   │   ├── ControlPanel.jsx   # URL input, prompt input, action buttons
│       │   │   ├── VideoPlayer.jsx    # WS frames consumer → live <img> display
│       │   │   ├── ResultsLog.jsx     # Scrolling log of steps + AI analysis cards
│       │   │   ├── Sidebar.jsx        # Session info, user ID
│       │   │   ├── TestSuggestions.jsx # AI suggestion cards
│       │   │   ├── ExecutionLoader.jsx # Animated loading state
│       │   │   └── ui/             # GlassCard, GlowButton primitives
│       │   ├── hooks/
│       │   │   ├── useTestAgent.js # Central state + WS management hook
│       │   │   └── useTheme.js     # Dark/light theme toggle
│       │   └── services/
│       │       └── backend.js      # axios wrapper for all REST calls
│       ├── Dockerfile.dev          # node:22-alpine + vite dev server
│       └── package.json            # React 19, Vite, TailwindCSS v4, framer-motion
│
└── ops/
    ├── hub/                        # Nginx ops dashboard (port 7070)
    ├── grafana/provisioning/       # Auto-provisioned datasources + dashboards
    ├── otel/                       # OpenTelemetry Collector config
    ├── prometheus/                 # Scrape targets config
    ├── loki/                       # Log retention config
    ├── promtail/                   # Docker log scraping config
    └── tempo/                      # Distributed trace storage config
```

---

## 4. Component Deep Dive

### 4.1 FastAPI Backend (`Backend/MCP_Agent/server.py`)

The backend is a single FastAPI application that owns:

**Session lifecycle** — Each call to `POST /sessions` creates a `Session` dataclass containing an `openai-agents` `Agent`, an `asyncio.Lock`, browser state snapshot, prompt history (last 10 entries, capped at 1200 chars each), and two WebSocket slot lists.

**Agent construction** — The agent is built from `openai-agents` SDK with the global `MCPServerStreamableHttp` connection injected as a tool provider. The connection to `playwright-mcp` is opened **once** at startup (`@app.on_event("startup")`) and shared across all sessions via `--shared-browser-context` on the MCP server side.

**Streaming execution** — `POST /sessions/{id}/prompt` calls `Runner.run_streamed()`, consumes async events, classifies each event via `process_and_send_log()`, and sends structured JSON over the session WebSocket in real time.

**Frames loop** — A per-session `asyncio.Task` runs `_frames_loop()` at 20 FPS. Each tick calls `browser_take_screenshot` with `{"type": "jpeg"}` over MCP, extracts the base64 payload from the `ImageContent` response, and fans out `{"type": "frame", "ts": ..., "mime": "image/jpeg", "frame": "data:image/jpeg;base64,..."}` to all connected frame WebSocket clients.

**TPM rate limit handling** — `run_with_tpm_fallback()` retries up to 4 times with exponential backoff, parsing OpenAI's `Please try again in Xs` message for exact sleep duration.

### 4.2 Playwright MCP Server (`Backend/playwright-mcp/Dockerfile`)

Built on `node:22-slim`. The critical build insight:

```dockerfile
# @playwright/mcp@latest bundles its own playwright internally.
# That bundled playwright needs a specific chromium revision.
# We install chromium using the MCP's own bundled playwright CLI,
# NOT the system npx playwright, to guarantee revision alignment.
RUN PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    node "$(npm root -g)/@playwright/mcp/node_modules/playwright/cli.js" \
    install chromium --with-deps
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
```

Started with:
```
--headless --browser chromium --allowed-hosts '*'
--shared-browser-context --image-responses allow
```

- `--shared-browser-context` — all MCP HTTP requests share one Chromium browser context, enabling the agent's navigation and the frames screenshot to operate in the same session
- `--image-responses allow` — required for `browser_take_screenshot` to return `ImageContent` (base64 JPEG) instead of a plain text path reference

### 4.3 Failure Analyzer (`Backend/failure_analyzer/`)

A three-stage pipeline invoked inline during prompt streaming:

```
Raw MCP Event Dict
       ↓
  normalizer.py  →  NormalizedFailure (extracts: message, step, console, network, locators)
       ↓
  classifier.py  →  ClassificationResult (rule-based: ELEMENT_NOT_FOUND | ASSERTION_FAILED |
                                           JS_ERROR | NETWORK_FAILURE | UNKNOWN)
       ↓
  openai_client.py →  FailureAnalysis (LLM-generated: explanation, fix_suggestion, confidence)
       ↓
  WebSocket →  {"type": "failure_analysis", "data": {...}}
```

The rule-based classifier runs first (deterministic, free), reducing LLM calls to only confirmed failures. `UNKNOWN`-classified events are filtered before being sent to the frontend to avoid noise.

### 4.4 React Frontend (`frontend/client/`)

Built with Vite + React 19 + TailwindCSS v4. Layout is two resizable panels via `react-resizable-panels`:

- **Left panel**: `Sidebar` (session metadata) + `ControlPanel` (URL input, prompt bar, action buttons)
- **Right panel**: `VideoPlayer` (top, live frame display) + `ResultsLog` (bottom, scrolling event log)

`useTestAgent.js` is the central hook managing all state. It batches incoming WebSocket log events via `logBufferRef` to prevent excessive re-renders during high-frequency test runs.

---

## 5. Data Flow

### Session Creation

```
User types URL in ControlPanel
         │
         ▼
frontend/services/backend.js: POST /sessions
         │  { start_url, allowed_domain }
         ▼
server.py: create_session()
  ├── Validates URL is within allowed_domain
  ├── Creates Session + openai-agents Agent
  ├── Runs initial prompt: "Go to <url>. Confirm page loaded. End with STATE."
  │     └── Agent calls: browser_navigate → playwright-mcp → Chromium
  └── Returns { session_id, snapshot: {url, title, keys} }
         │
         ▼
frontend: stores session_id, opens TWO WebSocket connections:
  ├── ws://localhost:8000/ws/sessions/{id}          ← log stream
  └── ws://localhost:8000/ws/sessions/{id}/frames   ← frame stream
```

### Prompt Execution & Streaming

```
User types natural language prompt → "Click Login and fill email"
         │
         ▼
POST /sessions/{id}/prompt
         │
         ▼
Runner.run_streamed(agent, composed_prompt, max_turns=50)
         │
         ├── Agent → OpenAI GPT → function call: browser_click({selector:"[role=button]"})
         │                                           │
         │                          MCP HTTP call to playwright-mcp:8931
         │                                           │
         │                               Playwright executes in Chromium
         │                                           │
         │                          MCP returns ToolResult (text confirmation)
         │
         ├── Each event → process_and_send_log() → format_live_step()
         │                                              │
         │                              ┌─── is_failure_event()? ───┐
         │                              │ YES                        │ NO
         │                              ▼                            ▼
         │                      FailureAnalyzer.analyze()    format_live_step()
         │                              │                            │
         │                              ▼                            ▼
         │           WS: {"type":"failure_analysis",...}   WS: {"type":"execution_step",...}
         │
         └── End: WS: {"type":"final","data":"run completed"}
```

### Frame Streaming

```
_frames_loop (asyncio.Task, 20 FPS)
         │
         ├── await MCP_SERVER.call_tool("browser_take_screenshot", {"type":"jpeg"})
         │         │
         │         ▼
         │   playwright-mcp returns ImageContent { mimeType: "image/jpeg", data: "<b64>" }
         │         │
         │         ▼
         │   Build: f"data:image/jpeg;base64,{data}"
         │         │
         │         ▼
         │   Fan-out to all s.frame_sockets:
         │   { "type":"frame", "ts":1700000000.0, "mime":"image/jpeg", "frame":"data:..." }
         │
         ▼
VideoPlayer.jsx: ws.onmessage → setSrc(ev.frame) → <img src={src} />
```

---

## 6. WebSocket Layer

The platform uses **two parallel WebSocket connections** per session.

### 6.1 Session Log WebSocket

| Property | Value |
|---|---|
| Endpoint | `ws://localhost:8000/ws/sessions/{session_id}` |
| Direction | Server → Client (one-way push) |
| Purpose | Real-time step events, failure analysis, agent thoughts |

**Message types sent by server:**

```jsonc
// Step event
{ "type": "execution_step", "data": { "icon": "🌐", "action": "Navigating",
  "details": "to https://example.com", "timestamp": "14:32:01", "status": "info" } }

// AI failure analysis
{ "type": "failure_analysis", "data": { "failure_category": "ELEMENT_NOT_FOUND",
  "explanation": "The selector '#submit-btn' was not found...",
  "fix_suggestion": "Wait for the element or use a more stable selector.",
  "confidence": 0.91 } }

// Run complete
{ "type": "final", "data": "run completed" }
```

### 6.2 Frames WebSocket

| Property | Value |
|---|---|
| Endpoint | `ws://localhost:8000/ws/sessions/{session_id}/frames` |
| Direction | Server → Client (one-way push at 20 FPS) |
| Purpose | Live JPEG screenshot of the browser viewport |

**Message format:**

```json
{
  "type": "frame",
  "ts": 1708000000.123,
  "mime": "image/jpeg",
  "frame": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

### 6.3 Connection Lifecycle & Reconnection

Both WebSocket connections use the same fallback logic in `config.js`:

```javascript
export const buildWsCandidates = (path) => {
  return [...new Set([
    `${WS_BASE_URL}${path}`,          // env-configured (default: ws://localhost:8000)
    `${FRAMES_WS_BASE_URL}${path}`,
    `ws://localhost:8000${path}`,     // explicit fallback
    `ws://127.0.0.1:8000${path}`,     // IPv4 literal fallback
  ])];
};
```

The client tries each candidate in order. If the first fails (connection refused / CORS error), it promotes to the next. This handles subtle Docker networking differences between `localhost` and `127.0.0.1`.

The frames loop keeps running on the server as long as `len(s.frame_sockets) > 0`. When the last client disconnects, the loop exits naturally. Reconnecting triggers a new task.

---

## 7. Observability Stack

All observability services are provisioned automatically via the `docker-compose.yml`.

| Service | URL | Purpose |
|---|---|---|
| **Grafana** | http://localhost:3000 | Unified dashboards (login: admin/admin) |
| **Prometheus** | http://localhost:9090 | Metrics scraping + querying |
| **Loki** | http://localhost:3100 | Log aggregation (via Promtail) |
| **Tempo** | http://localhost:3200 | Distributed trace storage |
| **OTel Collector** | localhost:4317 (gRPC) / 4318 (HTTP) | Trace + metrics ingestion |
| **cAdvisor** | http://localhost:8081 | Container resource metrics |
| **Node Exporter** | http://localhost:9100 | Host system metrics |
| **Ops Hub** | http://localhost:7070 | Nginx homepage linking all tools |

**What is instrumented automatically:**
- All FastAPI routes — request duration, status codes (via `prometheus-fastapi-instrumentator`)
- Distributed traces on every HTTP handler — spans exported to Tempo via OTel gRPC
- All container stdout/stderr — scraped by Promtail → shipped to Loki
- `container` and `compose_service` labels attached to every log line

---

## 8. Environment Variables

Copy the example file and fill in your values:

```bash
cp Backend/MCP_Agent/.env.example Backend/MCP_Agent/.env
```

```dotenv
# ── Required ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-...                    # OpenAI API key with GPT-4o access
OPENAI_MODEL=gpt-4o-mini                 # Model to use (gpt-4o-mini recommended)

# ── MCP Server ────────────────────────────────────────────────────────────────
PLAYWRIGHT_MCP_URL=http://playwright-mcp:8931/mcp   # Internal Docker hostname
                                                     # Use http://localhost:8931/mcp for local dev

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# ── Observability ─────────────────────────────────────────────────────────────
ENABLE_METRICS=true
ENABLE_TRACING=true
AGENTS_TRACING_DISABLED=false
LOG_LEVEL=INFO                           # DEBUG | INFO | WARNING | ERROR
LOG_FORMAT=json                          # json (structured) | text (human-readable)
OTEL_SERVICE_NAME=mcp-api
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_INSECURE=true
```

**Frontend environment** (set in `docker-compose.yml`, override in `frontend/client/.env.local` for local dev):

```dotenv
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
VITE_FRAMES_WS_BASE_URL=ws://localhost:8000
```

---

## 9. Setup & Installation

### Prerequisites

| Tool | Minimum Version | Notes |
|---|---|---|
| Docker Desktop | 24.x | Must be running |
| Docker Compose | v2.20+ | Included with Docker Desktop |
| OpenAI API key | — | GPT-4o or GPT-4o-mini access required |
| Git | Any | — |
| 8 GB RAM | — | Chromium + all observability containers |

> **Windows users**: Ensure Docker Desktop is set to **Linux containers** mode.

### Clone & Configure

```bash
git clone https://github.com/DanielPilant/Hackathon_EX_1.git
cd Hackathon_EX_1

# Create backend env file
cp Backend/MCP_Agent/.env.example Backend/MCP_Agent/.env
```

Open `Backend/MCP_Agent/.env` and set at minimum:

```dotenv
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

---

## 10. Running the Platform

### Production Mode (Docker Compose — Recommended)

```bash
docker compose up --build
```

On first run this will:
1. Build `hackathon-playwright-mcp` — downloads Chromium (~200 MB, one-time)
2. Build `mcp-api` — installs Python dependencies
3. Build `frontend-client` — installs Node dependencies
4. Start all 13 services in dependency order

**Expected startup time:** 3–5 minutes on first build, under 30 seconds on subsequent starts.

Wait until all services are healthy:

```bash
docker compose ps
```

All services should show `healthy` or `running`. Then open:

| Interface | URL |
|---|---|
| **Application** | http://localhost:5173 |
| **API docs (Swagger)** | http://localhost:8000/docs |
| **Ops Hub** | http://localhost:7070 |
| **Grafana** | http://localhost:3000 (admin/admin) |

### Local Development (Backend Only)

If you want to run the backend outside Docker for faster iteration:

```bash
# Terminal 1 — Start Playwright MCP container only
docker compose up playwright-mcp -d

# Terminal 2 — Run backend locally
cd Backend/MCP_Agent
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Override PLAYWRIGHT_MCP_URL to localhost for local run
PLAYWRIGHT_MCP_URL=http://localhost:8931/mcp uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```

### Local Development (Frontend Only)

```bash
cd frontend/client
npm install
npm run dev
# Vite dev server starts at http://localhost:5173
```

### Stop Everything

```bash
docker compose down          # stops and removes containers
docker compose down -v       # also removes named volumes (wipes Grafana/Prometheus data)
```

---

## 11. API Reference

All endpoints are served at `http://localhost:8000`. Interactive docs: http://localhost:8000/docs

### Health

```
GET  /healthz   → 200 { "status": "ok" }
GET  /readyz    → 200 { "status": "ready", "mcp_server": true, "failure_analyzer": true }
                  503 if MCP or analyzer not initialized
```

### Sessions

```
POST /sessions
Body: { "start_url": "https://example.com", "allowed_domain": "example.com" }
Returns: { "session_id": "a1b2c3...", "snapshot": { "url": "...", "title": "...", "keys": "..." } }

GET  /sessions/{session_id}
Returns: { "session_id", "created_at", "last_used_at", "last_snapshot", "history_len" }

DELETE /sessions/{session_id}
Returns: { "ok": true, "session_id": "..." }
```

### Prompts & Suggestions

```
POST /sessions/{session_id}/prompt
Body: { "prompt": "Click the Login button", "max_attempts": 4 }
Returns: { "ok": true, "session_id": "...", "output": "<agent final response>",
           "snapshot": { "url", "title", "keys" }, "error": null }

POST /sessions/{session_id}/suggest
Returns: { "suggestion": "Try submitting the form with an empty email field." }

GET  /sessions/{session_id}/suggestions
Returns: [ { "id": "signup-empty-validation", "title": "...", "description": "..." }, ... ]
```

### WebSocket Endpoints

```
WS  /ws/sessions/{session_id}          ← Attach to receive live step/failure events
WS  /ws/sessions/{session_id}/frames   ← Attach to receive 20 FPS JPEG frame stream
```

---

## 12. Troubleshooting

### Visual Feed shows "Waiting for frame data"

**Cause A — WS connection not established:**
Open browser DevTools → Network → WS tab. Look for `/ws/sessions/{id}/frames`. Check that it connects (101 Switching Protocols). If it fails, verify `VITE_FRAMES_WS_BASE_URL` matches the host you're accessing the frontend from.

**Cause B — Screenshot returns text instead of image:**
```bash
docker exec mcp-api python3 -c "
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
async def t():
    async with streamablehttp_client('http://playwright-mcp:8931/mcp') as (r,w,_):
        async with ClientSession(r,w) as s:
            await s.initialize()
            res = await s.call_tool('browser_take_screenshot', {'type': 'jpeg'})
            for item in res.content:
                print(type(item).__name__, getattr(item,'mimeType',''))
asyncio.run(t())
"
```
If you see `TextContent` with an error about `chromium not installed`, rebuild the playwright-mcp image:
```bash
docker compose build --no-cache playwright-mcp
docker compose up -d --force-recreate playwright-mcp
```

**Cause C — `--shared-browser-context` missing:**
The frames loop and agent must share the same browser context. Confirm the docker-compose `command` for `playwright-mcp` includes `--shared-browser-context`.

### 401 — OpenAI Authentication Error

```
HTTP 401: { "code": "openai_auth_error", "message": "OpenAI authentication failed..." }
```

Verify `Backend/MCP_Agent/.env` contains a valid `OPENAI_API_KEY`. Test it:

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | jq '.data | length'
```

If the key is valid you'll get a number (e.g., `67`). Restart mcp-api after changing the `.env`:

```bash
docker compose restart mcp-api
```

### 429 — Rate Limit / Quota Exceeded

```
HTTP 429: { "code": "openai_rate_limit" }
HTTP 429: { "code": "openai_quota_exceeded" }
```

- `openai_rate_limit` — too many requests per minute. The backend auto-retries with backoff, but very large prompts can overflow TPM. Reduce test complexity or upgrade tier.
- `openai_quota_exceeded` — billing quota exhausted. Check https://platform.openai.com/usage.

### playwright-mcp container exits immediately

Check logs:

```bash
docker compose logs playwright-mcp
```

**Common causes:**
- `error: unknown option '--shared-browser-context'` → wrong `@playwright/mcp` version. Re-run `docker compose build --no-cache playwright-mcp`.
- `Browser "chromium" is not installed` → Chromium install step in Dockerfile failed. Check build output for download errors (network timeout during build is common on slow connections). Retry `docker compose build playwright-mcp`.

### mcp-api cannot reach playwright-mcp

```bash
docker exec mcp-api curl -s http://playwright-mcp:8931/ | head -20
```

Should return HTML. If it fails with `Connection refused`, playwright-mcp is not healthy yet. Wait and check `docker compose ps`.

### Frontend shows blank page / build error

```bash
docker compose logs frontend
```

If you see Vite errors about missing `node_modules`, the volume bind may have stale state:

```bash
docker compose down
docker volume prune
docker compose up --build
```

### Grafana shows "No datasource found"

Datasources are auto-provisioned on first start. If they are missing:

```bash
docker compose restart grafana
```

---

## 13. Example Usage

### Scenario: Test the Login flow on a web app

1. Open http://localhost:5173
2. In the URL field, enter your app's URL (e.g., `https://savingplan.web.app`)
3. The allowed domain is autodetected from the hostname
4. Click **Connect** — the agent navigates to the page; the Visual Feed shows the live browser
5. Watch the Results Log for the initial page load confirmation

**Run a test:**

In the prompt field, type:
```
Click the Login button, enter email "test@example.com" and password "wrong123", 
then submit and verify the error message shown
```

Click **Run Test**. You will see:
- Live browser frames showing each action as it happens
- Step-by-step events in the Results Log (Navigating, Clicking, Typing, Capturing)
- If the error message element is not found, a `failure_analysis` card appears automatically with category `ELEMENT_NOT_FOUND`, an AI explanation, and a suggested fix

**Get AI test suggestions:**

Click **Deep Scan** to have the AI analyze the current page and propose 5–10 high-impact tests. Click any suggestion to run it immediately.

### Scenario: API usage (curl)

```bash
# 1. Create session
SESSION=$(curl -s -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"start_url":"https://example.com","allowed_domain":"example.com"}' \
  | jq -r .session_id)

echo "Session: $SESSION"

# 2. Run a test prompt
curl -s -X POST "http://localhost:8000/sessions/$SESSION/prompt" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Verify the page title contains Example and the main heading is visible"}' \
  | jq '{ok,output,snapshot}'

# 3. Get AI test suggestions
curl -s "http://localhost:8000/sessions/$SESSION/suggestions" | jq '.[].title'

# 4. Delete session
curl -s -X DELETE "http://localhost:8000/sessions/$SESSION"
```

---

## 14. Roadmap

| Priority | Feature |
|---|---|
| High | **Session persistence** — survive mcp-api restarts via Redis session store |
| High | **Multi-tab support** — parallel Playwright contexts within one session |
| High | **Video recording** — store full test run as MP4 via Playwright's `recordVideo` |
| Medium | **Test plan generator** — AI generates and auto-executes a full test suite from a URL |
| Medium | **Slack/webhook notifications** — push failure analyses to external channels |
| Medium | **Authentication helpers** — built-in `browser_login` tool with credential vault |
| Medium | **Screenshot diffing** — visual regression via pixel comparison against baseline |
| Low | **Multi-model support** — pluggable LLM backend (Gemini, Claude, local Ollama) |
| Low | **Export to Playwright code** — generate `.spec.ts` from session history |
| Low | **RBAC** — user accounts, session isolation, usage quotas per team |

---

## 15. Tech Stack

### Backend

| Layer | Technology | Version |
|---|---|---|
| Runtime | Python | 3.12 |
| Web framework | FastAPI | latest |
| ASGI server | Uvicorn | latest |
| AI agent SDK | openai-agents | ≥ 0.2.0 |
| OpenAI client | openai | ≥ 1.0.0 |
| MCP client | mcp | latest |
| Data validation | Pydantic | v2 |
| Metrics | prometheus-fastapi-instrumentator | ≥ 7.0.0 |
| Tracing | OpenTelemetry SDK + OTLP exporter | ≥ 1.28.0 |
| Structured logs | python-json-logger | ≥ 2.0.7 |

### Browser Automation

| Layer | Technology | Version |
|---|---|---|
| MCP server | @playwright/mcp | latest (0.0.68+) |
| Browser engine | Chromium (via playwright) | ~146.0 (rev 1212) |
| Container base | node:22-slim | — |

### Frontend

| Layer | Technology | Version |
|---|---|---|
| UI framework | React | 19 |
| Build tool | Vite | 6 |
| Styling | TailwindCSS | v4 |
| HTTP client | axios | 1.x |
| Animations | framer-motion | 12 |
| Layout | react-resizable-panels | 3 |
| Icons | lucide-react | 0.56 |

### Observability

| Tool | Role |
|---|---|
| Grafana | Unified dashboards |
| Prometheus | Metrics storage + alerting |
| Loki | Log aggregation |
| Tempo | Distributed trace storage |
| OpenTelemetry Collector | Telemetry pipeline |
| Promtail | Docker log scraper |
| cAdvisor | Container metrics |
| Node Exporter | Host metrics |

### Infrastructure

| Tool | Role |
|---|---|
| Docker Compose | Multi-service orchestration |
| Nginx | Ops hub reverse proxy |

---

*Branch: `main` — Repository: [DanielPilant/Hackathon_EX_1](https://github.com/DanielPilant/Hackathon_EX_1)*

