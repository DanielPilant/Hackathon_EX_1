import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from executor import run_execution_plan  # <-- זה הקובץ שבו נמצא הקוד שלך

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # לפיתוח בלבד
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# plan לדוגמה - תחליף לשלך / או תעשה POST
DEMO_PLAN = {
  "plan": [
    {
      "step_id": 1,
      "description": "Navigating to the login page",
      "action": "navigate",
      "target": None,
      "data": "https://savingplan.web.app/"
    },
    {
      "step_id": 2,
      "description": "Filling email field",
      "action": "fill",
      "target": {
        "strategy": "label",
        "role_type": None,
        "selector": "אימייל"
      },
      "data": "yossijosko@gmail.com"
    },
    {
      "step_id": 3,
      "description": "Filling password field",
      "action": "fill",
      "target": {
        "strategy": "label",
        "role_type": None,
        "selector": "סיסמה"
      },
      "data": "Ry5563ר"
    },
    {
      "step_id": 4,
      "description": "Submitting login form",
      "action": "click",
      "target": {
        "strategy": "css",
        "role_type": None,
        "selector": "form#loginForm button[type='submit']"
      },
      "data": None
    },
    {
      "step_id": 5,
      "description": "Waiting for app screen to appear",
      "action": "read",
      "target": {
        "strategy": "css",
        "role_type": None,
        "selector": "#appScreen"
      },
      "data": None
    }
  ]
}

@app.get("/ping")
def ping():
    return {"ok": True}


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    print("CLIENT CONNECTED")

    try:
        async for ev in run_execution_plan(DEMO_PLAN, headless=True, emit_frames=True):
            print("EV:", ev.get("action_type"))
            await ws.send_text(json.dumps(ev, ensure_ascii=False))
    except Exception as e:
        print("WS ERROR:", e)
        await ws.close()
