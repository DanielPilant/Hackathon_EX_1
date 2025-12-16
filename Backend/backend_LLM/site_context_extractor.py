import argparse
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup


def fetch_html(url: str, mode: str = "requests", timeout: int = 15) -> str:
    mode = mode.lower().strip()

    if mode == "requests":
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.text

    if mode == "playwright":
        # NOTE: requires `pip install playwright` and `playwright install`
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            html = page.content()
            browser.close()
        return html

    raise ValueError("mode must be 'requests' or 'playwright'")


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def is_internal_link(base_url: str, href: str) -> bool:
    if not href:
        return False
    if href.startswith("#") or href.lower().startswith("javascript:") or href.lower().startswith("mailto:"):
        return False
    base = urlparse(base_url)
    full = urlparse(urljoin(base_url, href))
    return (full.scheme in ("http", "https")) and (full.netloc == base.netloc)


def guess_tech_hints(soup: BeautifulSoup) -> dict:
    hints = {"meta_generator": None, "script_hints": [], "notes": []}

    gen = soup.find("meta", attrs={"name": re.compile(r"generator", re.I)})
    if gen and gen.get("content"):
        hints["meta_generator"] = normalize_ws(gen.get("content"))

    script_srcs = []
    for s in soup.find_all("script"):
        src = s.get("src")
        if src:
            script_srcs.append(src.lower())

    patterns = [
        ("nextjs", "next"),
        ("react", "react"),
        ("angular", "angular"),
        ("vue", "vue"),
        ("svelte", "svelte"),
        ("nuxt", "nuxt"),
        ("gatsby", "gatsby"),
        ("webpack", "webpack"),
        ("vite", "vite"),
    ]
    found = set()
    for src in script_srcs:
        for label, token in patterns:
            if token in src:
                found.add(label)

    hints["script_hints"] = sorted(found)
    if "nextjs" in found:
        hints["notes"].append("Detected possible Next.js assets in script src.")
    return hints


def build_locator_candidates(tag) -> dict:
    
    text = normalize_ws(tag.get_text(" ", strip=True))
    aria = normalize_ws(tag.get("aria-label", ""))
    placeholder = normalize_ws(tag.get("placeholder", ""))
    _id = normalize_ws(tag.get("id", ""))
    name = normalize_ws(tag.get("name", ""))
    role = normalize_ws(tag.get("role", ""))  # אם יש
    testid = normalize_ws(tag.get("data-testid", ""))

    # locator "name" סמנטי: text/aria/placeholder
    semantic_name = text or aria or placeholder or ""

    candidates = {
        "preferred": None,
        "semantic_name": semantic_name[:120],
        "role": role[:60] if role else None,
        "aria_label": aria[:120] if aria else None,
        "placeholder": placeholder[:120] if placeholder else None,
        "id": _id[:120] if _id else None,
        "name": name[:120] if name else None,
        "data_testid": testid[:120] if testid else None,
        "css_suggestion": None,
    }

    # Preferred strategy decision
    if role and semantic_name:
        candidates["preferred"] = {"strategy": "role", "selector": semantic_name, "role_type": role}
    elif semantic_name:
        candidates["preferred"] = {"strategy": "text", "selector": semantic_name, "role_type": None}
    elif placeholder:
        candidates["preferred"] = {"strategy": "placeholder", "selector": placeholder, "role_type": None}
    elif testid:
        candidates["preferred"] = {"strategy": "css", "selector": f"[data-testid='{testid}']", "role_type": None}
    elif _id:
        candidates["preferred"] = {"strategy": "css", "selector": f"#{_id}", "role_type": None}
    elif name:
        candidates["preferred"] = {"strategy": "css", "selector": f"[name='{name}']", "role_type": None}
    else:
        candidates["preferred"] = {"strategy": "null", "selector": "", "role_type": None}

    # CSS suggestion (מאוד בסיסי, לא ארוך)
    if _id:
        candidates["css_suggestion"] = f"#{_id}"
    elif testid:
        candidates["css_suggestion"] = f"[data-testid='{testid}']"
    elif name:
        candidates["css_suggestion"] = f"{tag.name}[name='{name}']"
    else:
        candidates["css_suggestion"] = tag.name

    return candidates


def element_score(tag) -> int:
    
    score = 0
    text = normalize_ws(tag.get_text(" ", strip=True))
    aria = normalize_ws(tag.get("aria-label", ""))
    placeholder = normalize_ws(tag.get("placeholder", ""))
    _id = normalize_ws(tag.get("id", ""))
    name = normalize_ws(tag.get("name", ""))

    if tag.name == "button":
        score += 10
    if tag.name in ("input", "textarea", "select"):
        score += 9
    if tag.name == "a":
        score += 4

    if text:
        score += 6
    if aria:
        score += 5
    if placeholder:
        score += 5
    if _id:
        score += 2
    if name:
        score += 2

    t = text.lower()
    if any(k in t for k in ["login", "sign in", "register", "submit", "search", "add", "cart", "checkout", "save", "continue"]):
        score += 5

    return score


def extract_site_context(url: str, html: str, max_elements: int = 250, max_links: int = 80) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # remove noise
    for t in soup(["script", "style", "noscript"]):
        t.decompose()

    title = normalize_ws(soup.title.string if soup.title and soup.title.string else "")
    meta_desc = ""
    md = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if md and md.get("content"):
        meta_desc = normalize_ws(md.get("content"))

    lang = ""
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        lang = normalize_ws(html_tag.get("lang"))

    headings = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        txt = normalize_ws(h.get_text(" ", strip=True))
        if txt:
            headings.append({"tag": h.name, "text": txt[:200]})
    headings = headings[:60]

    # forms
    forms = []
    for f in soup.find_all("form"):
        action = normalize_ws(f.get("action", ""))
        method = normalize_ws(f.get("method", "GET")).upper()
        fields = []
        for inp in f.find_all(["input", "select", "textarea"]):
            fields.append({
                "tag": inp.name,
                "type": normalize_ws(inp.get("type", "")),
                "name": normalize_ws(inp.get("name", "")),
                "id": normalize_ws(inp.get("id", "")),
                "placeholder": normalize_ws(inp.get("placeholder", "")),
                "aria_label": normalize_ws(inp.get("aria-label", "")),
            })
        forms.append({
            "action": action[:200],
            "method": method,
            "fields": fields[:60],
        })
    forms = forms[:30]

    # interactive elements
    tags = soup.find_all(["button", "input", "a", "select", "textarea"])
    tags_sorted = sorted(tags, key=element_score, reverse=True)

    seen = set()
    interactives = []

    for tag in tags_sorted:
        text = normalize_ws(tag.get_text(" ", strip=True))[:120]
        aria = normalize_ws(tag.get("aria-label", ""))[:120]
        placeholder = normalize_ws(tag.get("placeholder", ""))[:120]
        _id = normalize_ws(tag.get("id", ""))[:120]
        name = normalize_ws(tag.get("name", ""))[:120]
        href = normalize_ws(tag.get("href", ""))[:200] if tag.name == "a" else ""

        key = (tag.name, text, aria, placeholder, _id, name, href)
        if key in seen:
            continue
        seen.add(key)

        interactives.append({
            "tag": tag.name,
            "text": text or None,
            "aria_label": aria or None,
            "placeholder": placeholder or None,
            "id": _id or None,
            "name": name or None,
            "type": normalize_ws(tag.get("type", ""))[:60] if tag.name == "input" else None,
            "href": href or None,
            "role": normalize_ws(tag.get("role", ""))[:60] or None,
            "data_testid": normalize_ws(tag.get("data-testid", ""))[:120] or None,
            "locators": build_locator_candidates(tag),
        })

        if len(interactives) >= max_elements:
            break

    # internal links (for future crawl / navigation)
    internal_links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and is_internal_link(url, href):
            full = urljoin(url, href)
            txt = normalize_ws(a.get_text(" ", strip=True))[:120]
            internal_links.append({"text": txt or None, "href": full})
    # dedup
    uniq = {}
    for l in internal_links:
        uniq[l["href"]] = l
    internal_links = list(uniq.values())[:max_links]

    body_text = ""
    body = soup.find("body")
    if body:
        body_text = normalize_ws(body.get_text(" ", strip=True))[:1500]

    return {
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "page": {
            "title": title or None,
            "meta_description": meta_desc or None,
            "lang": lang or None,
        },
        "tech_hints": guess_tech_hints(soup),
        "headings": headings,
        "forms": forms,
        "interactive_elements": interactives,
        "internal_links": internal_links,
        "text_snippet": body_text or None,
        "limits": {
            "max_elements": max_elements,
            "max_links": max_links,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Extract important site context into JSON for LLM research.")
    parser.add_argument("--url", required=True, help="Target URL (e.g., https://example.com)")
    parser.add_argument("--out", default="site_context.json", help="Output JSON file path")
    parser.add_argument("--mode", choices=["requests", "playwright"], default="requests", help="Fetch mode")
    parser.add_argument("--max-elements", type=int, default=250, help="Max interactive elements to include")
    parser.add_argument("--max-links", type=int, default=80, help="Max internal links to include")
    parser.add_argument("--save-html", default=None, help="Optional: save raw HTML to this file path")
    args = parser.parse_args()

    html = fetch_html(args.url, mode=args.mode)

    if args.save_html:
        with open(args.save_html, "w", encoding="utf-8") as f:
            f.write(html)

    context = extract_site_context(
        url=args.url,
        html=html,
        max_elements=args.max_elements,
        max_links=args.max_links,
    )

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)

    print(f"OK: wrote {args.out} (mode={args.mode})")


if __name__ == "__main__":
    main()
