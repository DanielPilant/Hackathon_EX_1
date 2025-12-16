import os
from playwright.sync_api import sync_playwright, TimeoutError

URL = "https://savingplan.web.app/"
USERNAME = "yossijosko@gmail.com"
PASSWORD = "Ry5563"

if not USERNAME or not PASSWORD:
    raise SystemExit("Set env vars: SAVINGPLAN_USERNAME and SAVINGPLAN_PASSWORD")

def highlight(locator, color="lime", ms=800):
    locator.evaluate(
        """(el, args) => {
            const prev = el.style.outline;
            el.style.outline = `3px solid ${args.color}`;
            setTimeout(() => el.style.outline = prev, args.ms);
        }""",
        {"color": color, "ms": ms},
    )

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=200)
    page = browser.new_page(viewport={"width": 1280, "height": 800})
    page.goto(URL, wait_until="domcontentloaded")

    email = page.locator("#loginEmail")
    password = page.locator("#loginPassword")
    submit = page.locator('form#loginForm button[type="submit"]')

    email.wait_for(state="visible")
    password.wait_for(state="visible")
    submit.wait_for(state="visible")

    # הקלדה "אנושית" יותר כדי להפעיל ולידציות/Listeners
    highlight(email); email.click()
    email.fill("")              # נקה
    email.type(USERNAME, delay=40)

    highlight(password); password.click()
    password.fill("")
    password.type(PASSWORD, delay=40)

    highlight(submit); submit.click()

    # נחכה לתנאי של הצלחה: appScreen נהיה active
    try:
        page.wait_for_function(
            """() => document.querySelector('#appScreen')?.classList.contains('active')""",
            timeout=8000
        )
        print("✅ Login success: appScreen is active")
    except TimeoutError:
        # אם לא הצליח – נשאב מידע ונצלם מסך
        login_active = page.evaluate("() => document.querySelector('#loginScreen')?.className")
        app_active = page.evaluate("() => document.querySelector('#appScreen')?.className")
        print("❌ Login did not switch screens")
        print("loginScreen class:", login_active)
        print("appScreen class:", app_active)
        page.screenshot(path="login_failed.png", full_page=True)
        print("Saved screenshot: login_failed.png")

    print("Browser stays open. Press Ctrl+C to exit.")
    page.wait_for_timeout(10_000_000)
