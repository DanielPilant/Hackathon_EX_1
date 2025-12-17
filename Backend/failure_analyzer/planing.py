from __future__ import annotations

import os
import json
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI


async def generate_expanded_test_plan(
    user_prompt: str,
    *,
    model: Optional[str] = None,
    max_steps: int = 25,
    include_edge_cases: bool = True,
    include_negative_tests: bool = True,
    include_accessibility: bool = True,
    include_security: bool = True,
    mock_mode: bool = False,
) -> Dict[str, Any]:
    """
    Expand a short user QA request into a detailed, executable test plan (plain English),
    plus structured metadata that can be used by an execution agent.

    Returns:
      {
        "expanded_plan_text": str,
        "checklist": [str],
        "assumptions": [str],
        "risky_areas": [str],
        "coverage_tags": [str]
      }
    """
    load_dotenv()

    user_prompt = (user_prompt or "").strip()
    if not user_prompt:
        raise ValueError("user_prompt must be a non-empty string")

    # Allow running without OpenAI during MVP/demo
    api_key = os.getenv("OPENAI_API_KEY")
    if mock_mode or not api_key:
        return {
            "expanded_plan_text": (
                "1) Navigate to the target page related to the request.\n"
                "2) Identify the main UI elements involved.\n"
                "3) Execute the happy-path flow.\n"
                "4) Validate expected outcomes (URL, key text, key element states).\n"
                "5) Run a basic negative test (invalid input / missing input).\n"
                "6) Capture any failures with steps-to-reproduce.\n"
            ),
            "checklist": [
                "Happy path works",
                "Basic validation errors appear",
                "No obvious console/network errors",
            ],
            "assumptions": ["Target URL is reachable and stable", "User is authorized to test the site"],
            "risky_areas": ["Auth/session state", "Form validation", "Unexpected navigation"],
            "coverage_tags": ["functional", "smoke", "basic-negative"],
        }

    client = AsyncOpenAI(api_key=api_key)
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    system = (
        "You are a senior QA architect. Your job is to expand short user requests into comprehensive, "
        "high-signal test plans that are practical for browser automation.\n"
        "Rules:\n"
        "- Infer missing but reasonable details; state assumptions.\n"
        "- Add negative tests and edge cases.\n"
        "- Keep steps concrete and executable.\n"
        "- Prefer stable checks: URL/title/visible text/roles/labels.\n"
        "- Avoid huge checklists; focus on the highest value coverage.\n"
        "- Output MUST be valid JSON only, matching the schema exactly.\n"
    )

    # Build coverage requirements
    coverage = []
    if include_edge_cases:
        coverage.append("edge cases")
    if include_negative_tests:
        coverage.append("negative tests")
    if include_accessibility:
        coverage.append("basic accessibility checks")
    if include_security:
        coverage.append("basic security checks (e.g., auth boundaries, input handling)")

    user = f"""
Expand the following user request into a detailed test plan for web E2E automation.

User request:
{user_prompt}

Constraints:
- Max steps: {max_steps}
- Include: {", ".join(coverage) if coverage else "core functional coverage only"}

Return JSON with exactly these keys:
{{
  "expanded_plan_text": string,          // numbered steps in plain English
  "checklist": string[],                // concise validations to assert
  "assumptions": string[],              // what you assumed
  "risky_areas": string[],              // where failures are likely
  "coverage_tags": string[]             // short tags like ["functional","negative","a11y"]
}}
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
        # If the model returns non-JSON, fail clearly (so you can log and iterate)
        raise RuntimeError(f"Planning LLM returned invalid JSON. Error: {e}\nRaw:\n{content}")

    # Minimal validation (protect downstream code)
    for k in ["expanded_plan_text", "checklist", "assumptions", "risky_areas", "coverage_tags"]:
        if k not in data:
            raise RuntimeError(f"Planning JSON missing key: {k}. Raw:\n{content}")

    if not isinstance(data["expanded_plan_text"], str) or not data["expanded_plan_text"].strip():
        raise RuntimeError(f"expanded_plan_text must be a non-empty string. Raw:\n{content}")

    return data
