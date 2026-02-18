# Docker Compose Runbook

## Goal
Run the core system with one command:

```bash
docker compose up --build
```

## Included services
- Ops Hub (single visual status page): http://localhost:7070
- frontend UI: http://localhost:5173
- MCP API: http://localhost:8000
- Playwright MCP: http://localhost:8931
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100
- Tempo: http://localhost:3200
- cAdvisor: http://localhost:8081
- node-exporter: http://localhost:9100

## Prerequisites
- Docker Desktop with Compose v2
- Valid OpenAI key in `Backend/MCP_Agent/.env`

## Setup
1. Copy env templates if missing:
   - `Backend/MCP_Agent/.env.example` -> `Backend/MCP_Agent/.env`
   - `frontend/client/.env.example` -> `frontend/client/.env` (optional)
2. Set `OPENAI_API_KEY` in backend env.

## Run
```bash
docker compose up --build
```

## Observability checks
- Metrics endpoint: http://localhost:8000/metrics
- Health endpoint: http://localhost:8000/healthz
- Readiness endpoint: http://localhost:8000/readyz
- Grafana datasource provisioning: preloaded for Prometheus, Loki, Tempo
- Default dashboard: `Compose / Compose Overview`

## Notes
- Frontend and backend are configured for development mode with live reload.
- Backend talks to Playwright MCP over Docker DNS (`playwright-mcp`).
- If you only need core app services, stop observability containers manually or split profiles later.
