import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import re


# ---- Logging ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("savingplan_suite")

TARGET_URL = "https://savingplan.web.app/"
OUT_DIR = Path("out_plans")


def safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def dump_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_context_best_effort(url: str) -> str:
    """
    Best-effort context extraction.
    - If backend_LLM.site_context_extractor has fetch_html/extract_site_context, use them.
    - Otherwise fallback to minimal context so the run is still runnable.
    """
    try:
        from backend_LLM.site_context_extractor import fetch_html, extract_site_context  # type: ignore

        html = fetch_html(url, mode="requests")
        ctx = extract_site_context(url, html)
        ctx_str = json.dumps(ctx, ensure_ascii=False, indent=2)
        log.info("Context extracted successfully (len=%d chars).", len(ctx_str))
        return ctx_str
    except Exception as e:
        log.warning("Context extraction failed (%s). Falling back to minimal context.", e)
        return f"Target URL: {url}\n(Context extraction unavailable; use semantic locators by visible text/role.)"


def get_session() -> "QASession":
    from backend_LLM.session_manager import QASession  # type: ignore
    return QASession()


def generate_with_retries(session: "QASession", prompt_text: str, max_attempts: int = 4) -> Dict[str, Any]:
    """
    Calls session.generate_test_plan with simple retry/backoff for transient failures.
    NOTE: This does NOT sleep 33s on purpose; it's a quick local test runner.
    """
    last_err: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            log.info("Generating plan (attempt %d/%d)...", attempt, max_attempts)
            plan = session.generate_test_plan(prompt_text)
            return plan
        except Exception as e:
            last_err = e
            msg = str(e)

            # Default backoff: 1, 2, 4, 8...
            sleep_s = 2 ** (attempt - 1)

            # If Google returns a suggested retry delay (e.g. "Please retry in 6.7s"), respect it
            m = re.search(r"Please retry in ([0-9.]+)s", msg)
            if m:
                sleep_s = int(float(m.group(1))) + 1  # add 1s safety margin

            log.error("Attempt %d failed: %s", attempt, e)

            if attempt < max_attempts:
                log.info("Sleeping %ds before retry...", sleep_s)
                time.sleep(sleep_s)


    raise last_err if last_err else RuntimeError("Unknown error")


def main() -> None:
    log.info("Starting SavingPlan E2E LLM suite...")

    user_id = f"user_{uuid.uuid4().hex[:10]}"
    safe_mkdir(OUT_DIR)

    # 1) Build and save the URL JSON (your required schema)
    url_payload = {"user_id": user_id, "target_url": TARGET_URL}
    dump_json(OUT_DIR / "00_url.json", url_payload)
    log.info("Wrote %s", OUT_DIR / "00_url.json")

    # 2) Extract site context (best-effort)
    context_str = extract_context_best_effort(TARGET_URL)

    # 3) Start session
    s = get_session()
    s.start_new_session(url=TARGET_URL, html_context=context_str)

    # 4) Build PROMPT requests (your required schema)
    prompts: List[Dict[str, str]] = [
        {
            "user_id": user_id,
            "prompt_text": (
                "Navigate to the site and verify the login page is visible. "
                "Verify there are input fields for 'אימייל' and 'סיסמה', and buttons 'התחבר' and 'הירשם'. "
                "Return a JSON plan with at least 6 steps."
            ),
        },
        {
            "user_id": user_id,
            "prompt_text": (
                "Test basic validation on the login form: "
                "try clicking 'התחבר' with empty fields and verify a validation message or prevented submit. "
                "Then fill invalid email (e.g. 'abc') and verify error handling. "
                "Return a JSON plan with at least 10 steps."
            ),
        },
        {
            "user_id": user_id,
            "prompt_text": (
                "After login (assume user is already authenticated), test navigation between tabs: "
                "'ראשי', 'היסטוריה', 'הגדרות'. Verify each page shows a visible header. "
                "Return a JSON plan with at least 9 steps."
            ),
        },
    ]

    # Save the input PROMPT JSON files (for traceability)
    for i, p in enumerate(prompts, start=1):
        dump_json(OUT_DIR / f"{i:02d}_prompt.json", p)

    # 5) Generate plans and save output JSON
    for i, p in enumerate(prompts, start=1):
        prompt_text = p["prompt_text"]

        # Add strict JSON + non-empty plan requirement
        strict_prefix = (
            "Return ONLY valid JSON matching the schema. "
            "The 'plan' list MUST NOT be empty. No markdown, no extra text.\n"
        )
        plan = generate_with_retries(s, strict_prefix + prompt_text, max_attempts=4)

        dump_json(OUT_DIR / f"{i:02d}_plan.json", plan)
        log.info("Wrote %s", OUT_DIR / f"{i:02d}_plan.json")

    log.info("Done. All outputs are in: %s", OUT_DIR.resolve())
    log.info("User_id used for ALL requests: %s", user_id)


if __name__ == "__main__":
    main()
