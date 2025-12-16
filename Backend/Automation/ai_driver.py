import json
from typing import Any, Dict, List, Optional, Tuple, Union

from playwright.sync_api import sync_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError


# --------- Strict Schema / Validation ---------

ALLOWED_ACTIONS = {"navigate", "click", "fill", "press", "read", "wait"}
ALLOWED_STRATEGIES = {"role", "text", "placeholder", "label", "css", "xpath"}


class PlanValidationError(ValueError):
    pass


def _expect(cond: bool, msg: str) -> None:
    if not cond:
        raise PlanValidationError(msg)


def validate_plan(plan_obj: Dict[str, Any]) -> None:
    _expect(isinstance(plan_obj, dict), "Root must be a JSON object.")
    _expect("plan" in plan_obj, "Missing required field: 'plan'.")
    _expect(isinstance(plan_obj["plan"], list), "'plan' must be an array.")

    seen_ids = set()
    for i, step in enumerate(plan_obj["plan"], start=1):
        _expect(isinstance(step, dict), f"Step #{i} must be an object.")

        # Required fields
        for k in ("step_id", "description", "action", "target", "data"):
            _expect(k in step, f"Step #{i}: missing required field '{k}'.")

        step_id = step["step_id"]
        _expect(isinstance(step_id, int), f"Step #{i}: 'step_id' must be int.")
        _expect(step_id not in seen_ids, f"Duplicate step_id: {step_id}")
        seen_ids.add(step_id)

        _expect(isinstance(step["description"], str), f"Step {step_id}: 'description' must be string.")
        action = step["action"]
        _expect(isinstance(action, str), f"Step {step_id}: 'action' must be string.")
        _expect(action in ALLOWED_ACTIONS, f"Step {step_id}: invalid action '{action}'.")

        target = step["target"]
        data = step["data"]

        # action-specific constraints
        if action == "navigate":
            _expect(target is None, f"Step {step_id}: 'target' must be null for navigate.")
            _expect(isinstance(data, str) and data.strip(), f"Step {step_id}: 'data' must be URL string for navigate.")

        elif action == "wait":
            _expect(target is None, f"Step {step_id}: 'target' must be null for wait.")
            _expect(data is not None, f"Step {step_id}: 'data' must be ms (int/str) for wait.")

        else:
            # click/fill/press/read require target
            _expect(isinstance(target, dict), f"Step {step_id}: 'target' must be object for action '{action}'.")
            _expect("strategy" in target, f"Step {step_id}: target missing 'strategy'.")
            _expect("role_type" in target, f"Step {step_id}: target missing 'role_type'.")
            _expect("selector" in target, f"Step {step_id}: target missing 'selector'.")

            strategy = target["strategy"]
            _expect(isinstance(strategy, str), f"Step {step_id}: target.strategy must be string.")
            _expect(strategy in ALLOWED_STRATEGIES, f"Step {step_id}: invalid strategy '{strategy}'.")

            role_type = target["role_type"]
            selector = target["selector"]

            if strategy == "role":
                _expect(isinstance(role_type, str) and role_type.strip(), f"Step {step_id}: role_type required for role strategy.")
                _expect(isinstance(selector, str) and selector.strip(), f"Step {step_id}: selector required for role strategy (accessible name).")
            else:
                _expect(role_type is None, f"Step {step_id}: role_type must be null unless strategy=='role'.")
                _expect(isinstance(selector, str) and selector.strip(), f"Step {step_id}: selector required for strategy '{strategy}'.")

            # data constraints
            if action in {"fill", "press"}:
                _expect(isinstance(data, str), f"Step {step_id}: 'data' must be string for action '{action}'.")
            elif action in {"click", "read"}:
                _expect(data is None, f"Step {step_id}: 'data' must be null for action '{action}'.")


# --------- Locator Builder ---------

def build_locator(page: Page, target: Dict[str, Any]) -> Locator:
    strategy = target["strategy"]
    role_type = target["role_type"]
    selector = target["selector"]

    if strategy == "role":
        # Accessible name matching via name=
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
        # Playwright Python: use locator("xpath=...")
        return page.locator(f"xpath={selector}")

    raise RuntimeError(f"Unsupported strategy: {strategy}")


# --------- Runner ---------

def parse_json_strict(json_text: str) -> Dict[str, Any]:
    # strict: must be pure JSON; json.loads will fail if there is extra text
    return json.loads(json_text)


def _parse_wait_ms(value: Union[str, int, float]) -> int:
    if isinstance(value, (int, float)):
        ms = int(value)
    elif isinstance(value, str) and value.strip().isdigit():
        ms = int(value.strip())
    else:
        raise PlanValidationError(f"wait.data must be milliseconds as int or numeric string. Got: {value!r}")
    _expect(ms >= 0, "wait.data must be non-negative.")
    return ms


def _collect_visible_error_text(page: Page) -> List[str]:
    """
    Collects common visible error messages after a failed submit/login.
    Works best if your UI uses role=alert or common classes.
    """
    candidates = [
        "[role='alert']",
        ".alert",
        ".error",
        ".error-message",
        ".toast",
        ".snackbar",
        ".notification",
        "#loginError",
        "#error",
    ]
    texts: List[str] = []
    for sel in candidates:
        loc = page.locator(sel)
        try:
            count = loc.count()
        except Exception:
            continue
        for i in range(min(count, 5)):
            item = loc.nth(i)
            try:
                if item.is_visible():
                    t = item.inner_text().strip()
                    if t:
                        texts.append(t)
            except Exception:
                continue
    # de-dup
    return list(dict.fromkeys(texts))


def infer_domain_failure(page: Page, *, expected_visible_selector: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Heuristic: if expected screen stayed hidden and login screen is visible,
    classify it as LOGIN_FAILED (common case in your app structure).
    """
    try:
        login_visible = page.locator("#loginScreen").is_visible()
    except Exception:
        login_visible = False

    expected_hidden = None
    if expected_visible_selector:
        try:
            loc = page.locator(expected_visible_selector)
            if loc.count() > 0:
                expected_hidden = not loc.first.is_visible()
        except Exception:
            expected_hidden = None

    if login_visible and (expected_hidden is True or expected_hidden is None):
        return {
            "code": "LOGIN_FAILED",
            "message": "Login did not transition to the expected app screen; still on login screen.",
            "details": {
                "login_screen_visible": login_visible,
                "expected_selector": expected_visible_selector,
                "expected_selector_visible": False if expected_hidden is True else None,
                "ui_errors": _collect_visible_error_text(page),
                "url": page.url,
            },
        }

    return None

def run_plan(
    plan_obj: Dict[str, Any],
    *,
    headless: bool = True,
    slow_mo_ms: int = 0,
    default_timeout_ms: int = 15_000
) -> Dict[str, Any]:
    validate_plan(plan_obj)

    log: List[str] = []
    results: Dict[str, Any] = {}
    error_obj: Optional[Dict[str, Any]] = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo_ms)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(default_timeout_ms)

        # ---- Dialog capture with stable attribution ----
        dialog_errors: List[Dict[str, Any]] = []

        # "current_step" = where we are in the loop (timeouts etc.)
        current_step_id: Optional[int] = None
        current_action: Optional[str] = None

        # "dialog_context" = last step that could realistically trigger a JS dialog
        dialog_context_step_id: Optional[int] = None
        dialog_context_action: Optional[str] = None

        def _on_dialog(dialog):
            dialog_errors.append({
                "type": dialog.type,       # alert / confirm / prompt
                "message": dialog.message,
                "step_id": dialog_context_step_id,   # 👈 IMPORTANT
                "action": dialog_context_action,     # 👈 IMPORTANT
            })
            dialog.accept()

        page.on("dialog", _on_dialog)

        def _set_dialog_context(step_id: int, action: str) -> None:
            nonlocal dialog_context_step_id, dialog_context_action
            dialog_context_step_id = step_id
            dialog_context_action = action

        try:
            for step in plan_obj["plan"]:
                step_id = step["step_id"]
                desc = step["description"]
                action = step["action"]
                target = step["target"]
                data = step["data"]

                current_step_id = step_id
                current_action = action

                log.append(f"[{step_id}] {desc} ({action})")

                if action == "navigate":
                    _set_dialog_context(step_id, action)
                    page.goto(data, wait_until="domcontentloaded")

                elif action == "wait":
                    # wait doesn't typically create dialogs, don't override context
                    ms = _parse_wait_ms(data)
                    page.wait_for_timeout(ms)

                else:
                    loc = build_locator(page, target)

                    # visible guard (can timeout)
                    loc.first.wait_for(state="visible")

                    if action == "click":
                        _set_dialog_context(step_id, action)
                        loc.first.click()

                    elif action == "fill":
                        _set_dialog_context(step_id, action)
                        loc.first.fill(data)

                    elif action == "press":
                        _set_dialog_context(step_id, action)
                        loc.first.press(data)

                    elif action == "read":
                        # read should NOT override dialog context (it can mis-attribute)
                        text = loc.first.inner_text()
                        results[str(step_id)] = {"read_text": text}

                    else:
                        raise RuntimeError(f"Unhandled action: {action}")

            return {"ok": True, "results": results, "log": log, "error": None}

        except PlaywrightTimeoutError as e:
            # If any JS dialog occurred, prefer returning it as the domain error,
            # and attribute it to the triggering step (dialog_context_*).
            if dialog_errors:
                last = dialog_errors[-1]
                error_obj = {
                    "type": "DOMAIN_ERROR",
                    "code": "AUTH_DIALOG_ERROR",
                    "step_id": last.get("step_id"),
                    "action": last.get("action"),
                    "dialog": {"type": last.get("type"), "message": last.get("message")},
                    "url": page.url
                }
                log.append(f"DOMAIN_ERROR: AUTH_DIALOG_ERROR: {last.get('message')}")
                return {"ok": False, "results": results, "log": log, "error": error_obj}

            # fallback: try infer domain failure
            expected_sel = None
            try:
                if isinstance(step.get("target"), dict):
                    t = step["target"]
                    if t.get("strategy") in {"css", "xpath"} and isinstance(t.get("selector"), str):
                        expected_sel = t["selector"] if t["strategy"] == "css" else f"xpath={t['selector']}"
            except Exception:
                expected_sel = None

            domain = infer_domain_failure(page, expected_visible_selector=expected_sel)

            if domain:
                error_obj = {
                    "type": "DOMAIN_ERROR",
                    "step_id": current_step_id,
                    "action": current_action,
                    "domain": domain,
                    "url": page.url
                }
                log.append(f"DOMAIN_ERROR: {domain['code']}: {domain['message']}")
            else:
                error_obj = {
                    "type": "PLAYWRIGHT_TIMEOUT",
                    "step_id": current_step_id,
                    "action": current_action,
                    "message": str(e),
                    "url": page.url
                }
                log.append(f"ERROR: TimeoutError: {e}")

            return {"ok": False, "results": results, "log": log, "error": error_obj}

        except Exception as e:
            error_obj = {
                "type": type(e).__name__,
                "step_id": current_step_id,
                "action": current_action,
                "message": str(e),
                "url": page.url
            }
            log.append(f"ERROR: {type(e).__name__}: {e}")
            return {"ok": False, "results": results, "log": log, "error": error_obj}

        finally:
            context.close()
            browser.close()


# --------- Example CLI usage ---------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run AI JSON plan with Playwright.")
    parser.add_argument("--plan-file", required=True, help="Path to JSON file containing the plan.")
    parser.add_argument("--headed", action="store_true", help="Run in headed mode (not headless).")
    parser.add_argument("--slowmo", type=int, default=0, help="Slow motion in ms per action.")
    args = parser.parse_args()

    with open(args.plan_file, "r", encoding="utf-8") as f:
        plan = json.load(f)

    out = run_plan(plan, headless=not args.headed, slow_mo_ms=args.slowmo)
    print(json.dumps(out, ensure_ascii=False, indent=2))
