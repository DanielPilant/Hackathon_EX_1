from __future__ import annotations

import os
import json
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI


async def generate_goal_execution_plan(
    user_prompt: str,
    *,
    model: Optional[str] = None,
    max_attempts: int = 5,
    max_steps_per_attempt: int = 7,
    mock_mode: bool = False,
) -> Dict[str, Any]:
    """
    Goal-oriented planner (MVP): returns up to 5 distinct attempts to achieve the user's request.
    No QA/audit/negative tests by default. In-browser only.
    """
    load_dotenv()

    user_prompt = (user_prompt or "").strip()
    if not user_prompt:
        raise ValueError("user_prompt must be a non-empty string")

    # Hard bounds for MVP stability
    max_attempts = max(1, min(int(max_attempts), 5))
    max_steps_per_attempt = max(3, min(int(max_steps_per_attempt), 10))

    api_key = os.getenv("OPENAI_API_KEY")
    if mock_mode or not api_key:
        return {
            "goal": user_prompt,
            "attempts": [
                {
                    "name": "Fallback attempt — in-browser only",
                    "preconditions": [],
                    "steps": [
                        "Navigate to the most relevant page for the goal.",
                        "Use the main navigation/menu/search to locate the feature related to the goal.",
                        "Perform the primary action to complete the goal.",
                    ],
                    "success_criteria": [
                        "A clear success indicator appears (URL change / success message / expected element)."
                    ],
                    "stop_condition": "Stop immediately if success criteria are met; otherwise stop on a blocking error.",
                }
            ],
            "assumptions": ["Target site is reachable and you are authorized to use it."],
            "risky_areas": ["Navigation differences", "Auth/session", "Dynamic UI timing"],
            "coverage_tags": ["goal", "mvp"],
        }

    client = AsyncOpenAI(api_key=api_key)
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    system = (
        "You are a GOAL EXECUTION PLANNER for web automation in an MVP.\n"
        "Your job is to produce a SMALL, EXECUTABLE plan that maximizes the chance of achieving the user's goal.\n"
        "You are NOT writing a QA test plan.\n\n"
        "HARD CONSTRAINTS:\n"
        f"- Produce at most {max_attempts} attempts total.\n"
        f"- Each attempt must have at most {max_steps_per_attempt} steps.\n"
        "- Attempts must be MATERIALLY DIFFERENT strategies (not small variations of the same flow).\n"
        "- Stop early: if success is achieved, do NOT include further attempts.\n"
        "- Avoid redundancy: do not repeat the same action/verification across attempts.\n\n"
        "EXECUTABILITY RULES (VERY IMPORTANT):\n"
        "- Only include steps that can be executed INSIDE the browser session.\n"
        "- Do NOT include: checking email inbox, SMS/phone OTP, 2FA codes, external apps, CAPTCHA solving.\n"
        "- You MAY include password reset ONLY if it can be completed fully in-browser WITHOUT external email/OTP.\n"
        "- If a step depends on information not provided (credentials, code, email access), mark it as a precondition and propose an alternative attempt.\n"
        "- Do not assume specific buttons/features exist (e.g., Facebook/2FA). If referencing SSO, phrase it conditionally: "
        "\"If an SSO button is present, click it\".\n\n"
        "ACTION-FIRST STYLE:\n"
        "- Prefer actions over UI validations (no titles/labels/visibility checks unless required to proceed).\n"
        "- Use concrete user actions (click, type, submit, navigate) but keep wording selector-agnostic.\n\n"
        "SUCCESS CRITERIA:\n"
        "- Use 1–2 strong, generic indicators that can be observed in-browser (URL change to protected area, logout button, profile/avatar/account menu).\n\n"
        "OUTPUT:\n"
        "- Output MUST be valid JSON only.\n"
        "- Must match the schema exactly.\n"
    )

    user = f"""
User request:
{user_prompt}

Plan requirements:
- Build up to {max_attempts} attempts to achieve the goal.
- Attempts must be ordered from most likely to succeed to least likely.
- Each attempt must be a DIFFERENT strategy, examples:
  1) Use existing credentials (if available)
  2) Create account / Sign up (if available)
  3) Use SSO provider buttons ONLY if present (Google/Microsoft/GitHub) — do not invent providers; phrase conditionally
  4) Directly navigate to the target/protected page to detect existing session
  5) Use alternate entry points (navbar, footer, hamburger menu, search) to reach the goal

Strict prohibitions:
- No negative tests, no audits.
- No steps requiring email inbox, SMS, OTP, 2FA, or external apps.

Return JSON with exactly these keys:
{{
  "goal": string,
  "attempts": [
    {{
      "name": string,
      "preconditions": string[],
      "steps": string[],
      "success_criteria": string[],
      "stop_condition": string
    }}
  ],
  "assumptions": string[],
  "risky_areas": string[],
  "coverage_tags": string[]
}}

Quality checklist (must satisfy):
- No attempt is just a tiny variation of another attempt.
- No attempt includes external dependencies.
- Steps are short, actionable, and in-browser only.
""".strip()

    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )

    content = (resp.choices[0].message.content or "").strip()
    try:
        data = json.loads(content)
    except Exception as e:
        raise RuntimeError(f"Goal planner returned invalid JSON: {e}\nRaw:\n{content}")

    # --- MVP safety filter: remove non-executable attempts (email/otp/2fa/captcha/etc.) ---
    blocked_terms = [
        "email", "inbox", "mailbox", "e-mail",
        "sms", "text message", "phone otp",
        "otp", "2fa", "two-factor", "verification code",
        "captcha", "authenticator app"
    ]

    if isinstance(data.get("attempts"), list):
        filtered_attempts = []
        for a in data["attempts"]:
            if not isinstance(a, dict):
                continue
            steps = a.get("steps", [])
            if not isinstance(steps, list):
                continue
            steps_text = " ".join(str(s) for s in steps).lower()
            if any(t in steps_text for t in blocked_terms):
                continue
            filtered_attempts.append(a)
        data["attempts"] = filtered_attempts

    # Ensure at least one attempt exists (fallback)
    if not data.get("attempts"):
        data["attempts"] = [
            {
                "name": "Fallback attempt — in-browser only",
                "preconditions": [],
                "steps": [
                    "Navigate to the most relevant page for the goal.",
                    "Use the main navigation/menu/search to locate the feature related to the goal.",
                    "Perform the primary action to complete the goal.",
                ],
                "success_criteria": [
                    "A clear success indicator appears (URL change / success message / expected element)."
                ],
                "stop_condition": "Stop immediately if success criteria are met; otherwise stop on a blocking error.",
            }
        ]
        data.setdefault("goal", user_prompt)
        data.setdefault("assumptions", ["Target site is reachable and you are authorized to use it."])
        data.setdefault("risky_areas", ["Navigation differences", "Auth/session", "Dynamic UI timing"])
        data.setdefault("coverage_tags", ["goal", "mvp"])

    # Light enforcement (bounds)
    if isinstance(data.get("attempts"), list):
        data["attempts"] = data["attempts"][:max_attempts]
        for a in data["attempts"]:
            if isinstance(a, dict) and isinstance(a.get("steps"), list):
                a["steps"] = a["steps"][:max_steps_per_attempt]

    # Minimal key presence enforcement (prevent downstream KeyErrors)
    data.setdefault("goal", user_prompt)
    data.setdefault("assumptions", [])
    data.setdefault("risky_areas", [])
    data.setdefault("coverage_tags", ["goal"])

    return data
