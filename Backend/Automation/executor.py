"""
Async Execution Engine for TestFlow AI

Production-grade executor with:
- Async Playwright for non-blocking FastAPI integration
- Pydantic validation for strict schema enforcement
- Screenshot capture on failure (Base64 encoded)
- Tracing support for debugging
- Red Halo visual feedback for Passive View mode
"""

import asyncio
import base64
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from playwright.async_api import (
    async_playwright,
    Page,
    Locator,
    BrowserContext,
    TimeoutError as PlaywrightTimeoutError,
)
from pydantic import ValidationError

from .schemas import Plan, Target, ExecutionResult
from .visual_fx import RED_HALO_SCRIPT


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


async def capture_screenshot_base64(page: Page) -> str:
    """Capture a screenshot and return as Base64 string."""
    screenshot_bytes = await page.screenshot(type="png", full_page=False)
    return base64.b64encode(screenshot_bytes).decode("utf-8")


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


async def run_execution_plan(
    plan_json: Dict[str, Any],
    *,
    headless: bool = False,
    slow_mo_ms: int = 0,
    default_timeout_ms: int = 15000,
    enable_tracing: bool = True,
) -> Dict[str, Any]:
    """
    Execute a test plan asynchronously with visual feedback.
    
    Returns ExecutionResult dict with ok, results, log, error, screenshot_base64, trace_path.
    """
    try:
        plan = Plan(**plan_json)
    except ValidationError as e:
        return ExecutionResult(
            ok=False,
            error={"type": "VALIDATION_ERROR", "message": "Plan validation failed", "details": e.errors()},
            log=[f"VALIDATION_ERROR: {e}"],
        ).model_dump()
    
    log: List[str] = []
    results: Dict[str, Any] = {}
    error_obj: Optional[Dict[str, Any]] = None
    screenshot_b64: Optional[str] = None
    trace_path: Optional[str] = None
    
    current_step_id: Optional[int] = None
    current_action: Optional[str] = None
    
    dialog_errors: List[Dict[str, Any]] = []
    dialog_context_step_id: Optional[int] = None
    dialog_context_action: Optional[str] = None
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo_ms,
            args=["--start-maximized"] if not headless else [],
        )
        
        context: BrowserContext = await browser.new_context(viewport=VIEWPORT)
        page: Page = await context.new_page()
        page.set_default_timeout(default_timeout_ms)
        
        if enable_tracing:
            os.makedirs(TRACE_DIR, exist_ok=True)
            await context.tracing.start(screenshots=True, snapshots=True)
        
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
                log.append(f"[{step_id}] {desc} ({action})")
                
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
            
            log.append("Execution completed successfully")
            if enable_tracing:
                await context.tracing.stop()
            
            return ExecutionResult(ok=True, results=results, log=log).model_dump()
        
        except PlaywrightTimeoutError as e:
            log.append(f"TIMEOUT at step {current_step_id}: {e}")
            
            try:
                screenshot_b64 = await capture_screenshot_base64(page)
            except Exception:
                pass
            
            if dialog_errors:
                last = dialog_errors[-1]
                error_obj = {
                    "type": "DOMAIN_ERROR",
                    "code": "AUTH_DIALOG_ERROR",
                    "step_id": last.get("step_id"),
                    "action": last.get("action"),
                    "dialog": {"type": last.get("type"), "message": last.get("message")},
                    "url": page.url,
                }
            else:
                ui_errors = await collect_visible_error_text(page)
                error_obj = {
                    "type": "PLAYWRIGHT_TIMEOUT",
                    "step_id": current_step_id,
                    "action": current_action,
                    "message": str(e),
                    "url": page.url,
                    "ui_errors": ui_errors,
                }
            
            if enable_tracing:
                trace_path = os.path.join(TRACE_DIR, f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
                await context.tracing.stop(path=trace_path)
            
            return ExecutionResult(
                ok=False, results=results, log=log, error=error_obj,
                screenshot_base64=screenshot_b64, trace_path=trace_path,
            ).model_dump()
        
        except Exception as e:
            log.append(f"ERROR at step {current_step_id}: {type(e).__name__}: {e}")
            
            try:
                screenshot_b64 = await capture_screenshot_base64(page)
            except Exception:
                pass
            
            error_obj = {
                "type": type(e).__name__,
                "step_id": current_step_id,
                "action": current_action,
                "message": str(e),
                "url": page.url if page else None,
            }
            
            if enable_tracing:
                try:
                    trace_path = os.path.join(TRACE_DIR, f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
                    await context.tracing.stop(path=trace_path)
                except Exception:
                    pass
            
            return ExecutionResult(
                ok=False, results=results, log=log, error=error_obj,
                screenshot_base64=screenshot_b64, trace_path=trace_path,
            ).model_dump()
        
        finally:
            await context.close()
            await browser.close()


def run_plan_sync(plan_json: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Synchronous wrapper for CLI usage."""
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.run(run_execution_plan(plan_json, **kwargs))


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Run AI JSON plan with async Playwright.")
    parser.add_argument("--plan-file", required=True, help="Path to JSON file.")
    parser.add_argument("--headed", action="store_true", help="Run headed.")
    parser.add_argument("--slowmo", type=int, default=0, help="Slow motion ms.")
    parser.add_argument("--no-trace", action="store_true", help="Disable tracing.")
    args = parser.parse_args()
    
    with open(args.plan_file, "r", encoding="utf-8") as f:
        plan = json.load(f)
    
    result = run_plan_sync(plan, headless=not args.headed, slow_mo_ms=args.slowmo, enable_tracing=not args.no_trace)
    
    if result.get("screenshot_base64"):
        result["screenshot_base64"] = f"<{len(result['screenshot_base64'])} chars>"
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

