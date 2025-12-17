import asyncio
import os
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncGenerator

from playwright.async_api import (
    async_playwright,
    Page,
    Locator,
    BrowserContext,
    TimeoutError as PlaywrightTimeoutError,
)
from pydantic import ValidationError

from Automation.schemas import Plan, Target, ExecutionResult
from visual_fx import RED_HALO_SCRIPT


TRACE_DIR = os.path.join(os.path.dirname(__file__), "traces")
VIEWPORT = {"width": 1280, "height": 720}
HUMAN_PAUSE_SECONDS = 1.0
HUMAN_TYPE_DELAY_MS = 120

# --- Frames settings ---
FRAMES_MAX_FPS = 45
FRAMES_JPEG_QUALITY = 70
FRAMES_QUEUE_MAXSIZE = 7  # keep latest only


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


async def stream_frames_cdp(
    page: Page,
    frame_queue: asyncio.Queue,
    *,
    max_fps: int = FRAMES_MAX_FPS,
    quality: int = FRAMES_JPEG_QUALITY,
    width: int = VIEWPORT["width"],
    height: int = VIEWPORT["height"],
):
    """
    Use Chrome DevTools Protocol to receive screencast frames and push them into frame_queue.
    Each frame is a data URL: "data:image/jpeg;base64,..."

    Important: MUST ack every frame or screencast will stall.
    """
    cdp = await page.context.new_cdp_session(page)

    frame_interval = 1.0 / max_fps
    last_sent = 0.0

    async def ack(session_id: str):
        await cdp.send("Page.screencastFrameAck", {"sessionId": session_id})

    async def handle_frame(params: Dict[str, Any]):
        nonlocal last_sent
        now = asyncio.get_running_loop().time()

        # Throttle FPS but always ACK
        if now - last_sent < frame_interval:
            await ack(params["sessionId"])
            return

        last_sent = now

        try:
            data_url = "data:image/jpeg;base64," + params["data"]

            # keep latest only (drop old if full)
            try:
                if frame_queue.full():
                    _ = frame_queue.get_nowait()
                frame_queue.put_nowait(data_url)
            except Exception:
                pass
        finally:
            await ack(params["sessionId"])

    cdp.on("Page.screencastFrame", lambda p: asyncio.create_task(handle_frame(p)))

    await cdp.send("Page.startScreencast", {
        "format": "jpeg",
        "quality": quality,
        "maxWidth": width,
        "maxHeight": height,
    })

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        try:
            await cdp.send("Page.stopScreencast")
        except Exception:
            pass


async def run_execution_plan(
    plan_json: Dict[str, Any],
    *,
    headless: bool = True,  # NOTE: frames work great headless; set False if you also want a local window
    slow_mo_ms: int = 0,
    default_timeout_ms: int = 15000,
    enable_tracing: bool = False,
    emit_frames: bool = True,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Execute a test plan asynchronously with visual feedback + optional frames via CDP.

    Yields events with uniform structure:
    {
        "step_id": int | None,
        "status": "pass" | "fail" | "running",
        "action_type": str,   # includes "frame"
        "description": str,
        "error_reason": str | None,
        "selector": str | None,
        "timestamp": str,
        "duration": str,
        # when action_type == "frame":
        "frame": "data:image/jpeg;base64,..."
    }
    """
    # 1. Validate Plan
    try:
        plan = Plan(**plan_json)
    except ValidationError as e:
        yield {
            "step_id": None,
            "status": "fail",
            "action_type": "validation",
            "description": "Plan validation failed",
            "error_reason": str(e),
            "selector": None,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "duration": "0.0s",
        }
        return

    # 2. Setup Queues and State
    # We use a queue to decouple event generation (steps vs frames)
    event_queue: asyncio.Queue[Optional[Dict[str, Any]]] = asyncio.Queue()
    frame_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=FRAMES_QUEUE_MAXSIZE)
    
    # Shared state for frame tagging
    execution_state = {"step_id": None}

    # 3. Define internal tasks
    async def steps_worker(page: Page):
        log: List[str] = []
        dialog_errors: List[Dict[str, Any]] = []
        dialog_context_step_id: Optional[int] = None
        dialog_context_action: Optional[str] = None
        has_failure = False
        first_error_obj = None

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
                step_start_time = time.time()
                step_id = step.step_id
                desc = step.description
                action = step.action
                target = step.target
                data = step.data

                execution_state["step_id"] = step_id # Update shared state

                log.append(f"[{step_id}] {desc} ({action})")

                step_failed = False
                step_fail_reason = None

                try:
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
                            step_end_time = time.time()
                            duration = f"{step_end_time - step_start_time:.1f}s"

                            await event_queue.put({
                                "step_id": step_id,
                                "status": "pass",
                                "action_type": action,
                                "description": f"Read value: {text}",
                                "error_reason": None,
                                "selector": target.selector if target else "",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "duration": duration,
                            })
                            continue

                        # Check for errors immediately after interaction
                        if action in {"click", "fill", "press"}:
                            await asyncio.sleep(0.5)

                            # 1. Dialog errors
                            if dialog_errors:
                                for d in dialog_errors:
                                    has_failure = True
                                    await event_queue.put({
                                        "step_id": d.get("step_id"),
                                        "status": "fail",
                                        "action_type": "dialog",
                                        "description": f"Dialog detected: {d['message']}",
                                        "error_reason": f"Type: {d['type']}",
                                        "selector": "",
                                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                                        "duration": "0.0s",
                                    })
                                dialog_errors = []

                            # 2. UI errors
                            ui_errors = await collect_visible_error_text(page)
                            if ui_errors:
                                step_failed = True
                                step_fail_reason = f"UI Error: {'; '.join(ui_errors)}"

                except PlaywrightTimeoutError as e:
                    step_failed = True
                    step_fail_reason = f"Timeout: {e}"
                except Exception as e:
                    step_failed = True
                    step_fail_reason = f"Error: {e}"

                step_end_time = time.time()
                duration = f"{step_end_time - step_start_time:.1f}s"
                selector_str = target.selector if target else ""
                timestamp_str = datetime.now().strftime("%H:%M:%S")

                if step_failed:
                    has_failure = True
                    log.append(f"[{step_id}] FAILURE: {step_fail_reason}")
                    await event_queue.put({
                        "step_id": step_id,
                        "status": "fail",
                        "action_type": action,
                        "description": desc,
                        "error_reason": step_fail_reason,
                        "selector": selector_str,
                        "timestamp": timestamp_str,
                        "duration": duration,
                    })
                    if first_error_obj is None:
                        first_error_obj = {"step_id": step_id, "action": action, "message": step_fail_reason}

                elif action != "read":
                    await event_queue.put({
                        "step_id": step_id,
                        "status": "pass",
                        "action_type": action,
                        "description": desc,
                        "error_reason": None,
                        "selector": selector_str,
                        "timestamp": timestamp_str,
                        "duration": duration,
                    })

            # Final completion event
            if has_failure:
                await event_queue.put({
                    "step_id": None,
                    "status": "fail",
                    "action_type": "complete",
                    "description": "Execution completed with failures",
                    "error_reason": "One or more steps failed",
                    "selector": None,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "duration": "0.0s",
                })
            else:
                await event_queue.put({
                    "step_id": None,
                    "status": "pass",
                    "action_type": "complete",
                    "description": "Execution completed successfully",
                    "error_reason": None,
                    "selector": None,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "duration": "0.0s",
                })

        except Exception as e:
            log.append(f"GLOBAL ERROR: {type(e).__name__}: {e}")
            await event_queue.put({
                "step_id": None,
                "status": "fail",
                "action_type": "complete",
                "description": "Execution stopped due to global error",
                "error_reason": str(e),
                "selector": None,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "duration": "0.0s",
            })
        finally:
            await event_queue.put(None) # Sentinel to stop main loop

    async def frame_bridge_worker():
        """Reads frames from frame_queue and puts them into event_queue."""
        while True:
            try:
                data_url = await frame_queue.get()
                await event_queue.put({
                    "step_id": execution_state["step_id"],
                    "status": "running",
                    "action_type": "frame",
                    "description": "frame",
                    "error_reason": None,
                    "selector": None,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "duration": "0.0s",
                    "frame": data_url,
                })
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    # 4. Launch Browser and Tasks
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo_ms,
            args=["--start-maximized"] if not headless else [],
        )

        context: BrowserContext = await browser.new_context(viewport=VIEWPORT)
        page: Page = await context.new_page()
        page.set_default_timeout(default_timeout_ms)

        tasks = []
        
        # Start execution
        exec_task = asyncio.create_task(steps_worker(page))
        tasks.append(exec_task)

        # Start frames
        frames_task = None
        bridge_task = None
        if emit_frames:
            frames_task = asyncio.create_task(stream_frames_cdp(page, frame_queue))
            bridge_task = asyncio.create_task(frame_bridge_worker())
            tasks.append(frames_task)
            tasks.append(bridge_task)

        # 5. Yield events from queue
        try:
            while True:
                event = await event_queue.get()
                if event is None:
                    break
                yield event
        finally:
            # Cleanup
            if bridge_task: bridge_task.cancel()
            if frames_task: frames_task.cancel()
            if exec_task and not exec_task.done(): exec_task.cancel()
            
            # Wait for tasks to clean up if needed
            # We don't strictly need to await them if we are closing the browser anyway
            
            await context.close()
            await browser.close()


async def run_plan_cli(plan_json: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Async wrapper for CLI usage that prints events."""
    async for event in run_execution_plan(plan_json, **kwargs):
        print(json.dumps(event, ensure_ascii=False))
    return {}


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run AI JSON plan with async Playwright + frames.")
    parser.add_argument("--plan-file", required=True, help="Path to JSON file.")
    parser.add_argument("--headed", action="store_true", help="Run headed.")
    parser.add_argument("--slowmo", type=int, default=0, help="Slow motion ms.")
    parser.add_argument("--no-frames", action="store_true", help="Disable frames.")
    args = parser.parse_args()

    with open(args.plan_file, "r", encoding="utf-8") as f:
        plan = json.load(f)

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    asyncio.run(
        run_plan_cli(
            plan,
            headless=not args.headed,
            slow_mo_ms=args.slowmo,
            emit_frames=not args.no_frames,
        )
    )
