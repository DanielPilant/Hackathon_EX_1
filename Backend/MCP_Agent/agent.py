import asyncio
import os
import re

from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

# OpenAI SDK exception type (installed because agents uses it under the hood)
from openai import RateLimitError

load_dotenv()

# Force a cheaper model to reduce TPM pressure (works in your agents version via ENV)
os.environ["OPENAI_MODEL"] = "gpt-4o-mini"

PLAYWRIGHT_MCP_URL = "http://localhost:8931/mcp"


INSTRUCTIONS = """
You are a QA agent controlling a real browser via Playwright (MCP).

Rules:
- Follow the user goal only and stay on the allowed domain.
- Use stable selectors (roles, labels, visible text).
- Do not log in unless explicitly asked.
- Keep tool outputs small: do NOT request full page snapshots/DOM dumps.
  When checking page state, only read URL + title + 1-2 key elements.

Behavior:
- Work step by step and verify each action.
- Use human-like actions when possible (hover, slow typing, short waits).

Output:
- Short PASS/FAIL per step.
- End with current URL and what is on screen.
""".strip()



USER_PROMPT = """Go to https://savingplan.web.app/.

Steps:
1) Open the site.
2) Log in using:
   - Email: yits333@gmail.com
   - Password: 123456
3) Verify that login succeeded (page changes, login form disappears, or dashboard is shown).
4) After login, add several data entries or details in the app (use any visible form or input fields).
5) Verify that the changes were applied successfully (UI updates, new values appear, or confirmation is shown).

Rules:
- Stay only on savingplan.web.app.
- Use stable selectors (labels, visible text).
- Act like a real user (click, type, wait).
- Stop and report clearly if login fails.

Report:
- PASS/FAIL for login.
- PASS/FAIL for adding data.
- Describe what changed after each action (short).
- Output the final URL and current screen state.

""".strip()


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
    # Add a strict brevity rule to reduce output tokens
    return p + "\n\nKeep outputs extremely short (max 3 bullets total)."


async def run_with_tpm_fallback(agent: Agent, user_prompt: str, max_attempts: int = 4):
    """
    Retries Runner.run() on OpenAI 429 TPM / token-related rate limits.

    Strategy:
    - If error includes "Please try again in Xs" -> sleep Xs then retry
    - If "Request too large" -> shrink prompt then retry
    - Otherwise exponential backoff
    """
    prompt = user_prompt

    for attempt in range(1, max_attempts + 1):
        try:
            return await Runner.run(agent, prompt)

        except RateLimitError as e:
            msg = str(e)

            # Only handle token/TPM-related limits; otherwise re-raise
            if not _is_tpm_rate_limit(msg):
                raise

            retry_after = _parse_retry_after_seconds(msg)
            if retry_after is not None:
                await asyncio.sleep(retry_after + 0.5)
                continue

            if _is_request_too_large(msg):
                prompt = _shrink_prompt(prompt, keep_chars=600)
                # Re-assert model choice just in case
                os.environ["OPENAI_MODEL"] = "gpt-4o-mini"
                await asyncio.sleep(1.0)
                continue

            # Generic backoff for token limits without a retry-after hint
            await asyncio.sleep(min(2 ** attempt, 10))

    raise RuntimeError("TPM fallback exhausted: still hitting rate limits after retries.")


async def main():
    async with MCPServerStreamableHttp(
        name="playwright-local",
        params={
            "url": PLAYWRIGHT_MCP_URL,
            "timeout": 120,
        },
        cache_tools_list=True,
        client_session_timeout_seconds=180,
    ) as server:
        agent = Agent(
            name="UI Test Runner",
            instructions=INSTRUCTIONS,
            mcp_servers=[server],
        )

        result = await run_with_tpm_fallback(agent, USER_PROMPT, max_attempts=4)

        print("\n=== FINAL REPORT ===\n")
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
