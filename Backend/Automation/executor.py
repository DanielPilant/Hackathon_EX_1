import asyncio
import os
import json
from typing import Any, Dict, List, Optional, AsyncGenerator

from playwright.async_api import (
    async_playwright,
    Page,
    Locator,
    BrowserContext,
    TimeoutError as PlaywrightTimeoutError,
)
from pydantic import ValidationError

from schemas import Plan, Target, ExecutionResult
from visual_fx import RED_HALO_SCRIPT


TRACE_DIR = os.path.join(os.path.dirname(__file__), "traces")
VIEWPORT = {"width": 1280, "height": 720}
HUMAN_PAUSE_SECONDS = 1.0


async def build_locator(page: Page, target: Target) -> Locator:
    """Build a Playwright locator from a Target schema."""
    strategy = target.strategy
    selector = target.selector
    role_type = target.role_type.lower() if target.role_type else None
    
    if strategy == "role":
        return page.get_by_role(role_type, name=selector)
    if strategy == "text":
        return page.get_by_text(selector, exact=True)
    if strategy == "placeholder":
        return page.get_by_placeholder(selector)
    if strategy == "label":
        return page.get_by_label(selector)
    if strategy == "css":
        return page.locator(selector)
    if strategy == "xpath":
        return page.locator(f"xpath={selector}")
    
    raise RuntimeError(f"Unsupported strategy: {strategy}")


async def collect_visible_error_text(page: Page) -> List[str]:
    """Collect common visible error messages from the page."""
    candidates = [
        "[role='alert']", ".alert", ".error", ".error-message",
        ".toast", ".snackbar", ".notification", "#loginError", "#error",
    ]
    texts: List[str] = []
    
    for sel in candidates:
        try:
            loc = page.locator(sel)
            count = await loc.count()
            for i in range(min(count, 5)):
                item = loc.nth(i)
                if await item.is_visible():
                    text = await item.inner_text()
                    if text and text.strip():
                        texts.append(text.strip())
        except Exception:
            continue
    
    return list(dict.fromkeys(texts))


async def capture_screenshot_base64(page: Page) -> str:
    """Capture a screenshot and return as Base64 string."""
    # Function kept for interface compatibility but does nothing
    return ""


async def run_execution_plan(
    plan_json: Dict[str, Any],
    *,
    headless: bool = False,
    slow_mo_ms: int = 0,
    default_timeout_ms: int = 15000,
    enable_tracing: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute a test plan asynchronously with visual feedback.
    
    Yields events with uniform structure:
    {
        "step_id": int | None,
        "message": str,
        "status": "running" | "success" | "failure",
        "reason": str | None
    }
    """
    try:
        plan = Plan(**plan_json)
    except ValidationError as e:
        yield {
            "step_id": None,
            "message": "Plan validation failed",
            "status": "failure",
            "reason": str(e)
        }
        return
    
    log: List[str] = []
    results: Dict[str, Any] = {}
    
    current_step_id: Optional[int] = None
    current_action: Optional[str] = None
    
    dialog_errors: List[Dict[str, Any]] = []
    dialog_context_step_id: Optional[int] = None
    dialog_context_action: Optional[str] = None
    
    # Flag to track if any failure occurred, but we continue execution
    has_failure = False
    first_error_obj = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo_ms,
            args=["--start-maximized"] if not headless else [],
        )
        
        context: BrowserContext = await browser.new_context(viewport=VIEWPORT)
        page: Page = await context.new_page()
        page.set_default_timeout(default_timeout_ms)
        
        def on_dialog(dialog):
            dialog_errors.append({
                "type": dialog.type,
                "message": dialog.message,
                "step_id": dialog_context_step_id,
                "action": dialog_context_action,
            })
            asyncio.create_task(dialog.accept())
        
        page.on("dialog", on_dialog)
        
        def set_dialog_context(step_id: int, action: str):
            nonlocal dialog_context_step_id, dialog_context_action
            dialog_context_step_id = step_id
            dialog_context_action = action
        
        try:
            for step in plan.plan:
                step_id = step.step_id
                desc = step.description
                action = step.action
                target = step.target
                data = step.data
                
                current_step_id = step_id
                current_action = action
                
                # Yield running state
                yield {
                    "step_id": step_id,
                    "message": f"{desc} ({action})",
                    "status": "running",
                    "reason": None
                }
                
                log.append(f"[{step_id}] {desc} ({action})")
                
                step_failed = False
                step_fail_reason = None

                if action == "navigate":
                    set_dialog_context(step_id, action)
                    await page.goto(str(data), wait_until="domcontentloaded")
                
                elif action == "wait":
                    ms = int(data) if isinstance(data, (int, float)) else int(str(data).strip())
                    await page.wait_for_timeout(ms)
                
                else:
                    loc = await build_locator(page, target)
                    await loc.first.wait_for(state="visible")
                    
                    if action in {"click", "fill", "press"}:
                        try:
                            await loc.first.evaluate(RED_HALO_SCRIPT)
                        except Exception:
                            pass
                        await asyncio.sleep(HUMAN_PAUSE_SECONDS)
                    
                    if action == "click":
                        set_dialog_context(step_id, action)
                        await loc.first.click()
                    elif action == "fill":
                        set_dialog_context(step_id, action)
                        await loc.first.fill(str(data))
                    elif action == "press":
                        set_dialog_context(step_id, action)
                        await loc.first.press(str(data))
                    elif action == "read":
                        text = await loc.first.inner_text()
                        results[str(step_id)] = {"read_text": text}
                        # For read, we can consider it a success immediately with the value
                        yield {
                            "step_id": step_id,
                            "message": f"Read value: {text}",
                            "status": "success",
                            "reason": None
                        }
                        continue # Skip the generic success yield at the end of loop

                    # Check for errors immediately after interaction
                    if action in {"click", "fill", "press"}:
                        await asyncio.sleep(0.5)
                        
                        # 1. Check for Dialog/Alert errors
                        if dialog_errors:
                            last_dialog = dialog_errors[-1]
                            if last_dialog.get("step_id") == step_id:
                                step_failed = True
                                step_fail_reason = f"Dialog Error: {last_dialog['message']}"
                                dialog_errors = [] # Clear

                        # 2. Check for UI errors (text on page)
                        if not step_failed:
                            ui_errors = await collect_visible_error_text(page)
                            if ui_errors:
                                step_failed = True
                                step_fail_reason = f"UI Error: {'; '.join(ui_errors)}"

                if step_failed:
                    has_failure = True
                    log.append(f"[{step_id}] FAILURE: {step_fail_reason}")
                    yield {
                        "step_id": step_id,
                        "message": "Failed",
                        "status": "failure",
                        "reason": step_fail_reason
                    }
                    if first_error_obj is None:
                        first_error_obj = {
                            "step_id": step_id,
                            "action": action,
                            "message": step_fail_reason
                        }
                elif action != "read":
                    # If not failed and not read (read already yielded success)
                    yield {
                        "step_id": step_id,
                        "message": "Succeeded",
                        "status": "success",
                        "reason": None
                    }

            # Final completion event
            if has_failure:
                yield {
                    "step_id": None,
                    "message": "Execution completed with failures",
                    "status": "failure",
                    "reason": "One or more steps failed"
                }
            else:
                yield {
                    "step_id": None,
                    "message": "Execution completed successfully",
                    "status": "success",
                    "reason": None
                }
        
        except PlaywrightTimeoutError as e:
            log.append(f"TIMEOUT at step {current_step_id}: {e}")
            yield {
                "step_id": current_step_id,
                "message": "Timeout occurred",
                "status": "failure",
                "reason": str(e)
            }
            yield {
                "step_id": None,
                "message": "Execution stopped due to timeout",
                "status": "failure",
                "reason": str(e)
            }
        
        except Exception as e:
            log.append(f"ERROR at step {current_step_id}: {type(e).__name__}: {e}")
            yield {
                "step_id": current_step_id,
                "message": "Unexpected error",
                "status": "failure",
                "reason": str(e)
            }
            yield {
                "step_id": None,
                "message": "Execution stopped due to error",
                "status": "failure",
                "reason": str(e)
            }
        
        finally:
            await context.close()
            await browser.close()


async def run_plan_cli(plan_json: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Async wrapper for CLI usage that prints events."""
    final_result = {}
    async for event in run_execution_plan(plan_json, **kwargs):
        print(json.dumps(event, ensure_ascii=False))
        # We no longer return the full ExecutionResult object in the stream
        # But we can track the final status
    return final_result


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Run AI JSON plan with async Playwright.")
    parser.add_argument("--plan-file", required=True, help="Path to JSON file.")
    parser.add_argument("--headed", action="store_true", help="Run headed.")
    parser.add_argument("--slowmo", type=int, default=0, help="Slow motion ms.")
    parser.add_argument("--no-trace", action="store_true", help="Disable tracing.")
    args = parser.parse_args()
    
    with open(args.plan_file, "r", encoding="utf-8") as f:
        plan = json.load(f)
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    asyncio.run(run_plan_cli(plan, headless=not args.headed, slow_mo_ms=args.slowmo, enable_tracing=not args.no_trace))

