#!/usr/bin/env python3
"""Check the original 18-page site, including the preserved entry flow.

Optional test tools: Playwright Python package and Chromium.
Run a server in the repository, then:
    python3 tests/original_smoke.py --base-url http://127.0.0.1:8766/
"""
import argparse
from pathlib import Path
import re
import shutil
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["index.html", "home.html", "world.html", "domain.html", "characters.html", "start.html"] + [
    f"char/{code}.html" for code in "abcdefghijkl"
]
FIGURES = ["j", "f", "a", "b", "g", "l"]
REGIONS = ["home", "seril", "kardun", "waste", "reibek", "haster"]
FILTER_LABELS = ["전체", "가신 · 영지", "변경 너머", "바깥"]
ENTRY_VIEWPORTS = [(903, 1195), (1440, 900), (390, 844), (320, 640), (844, 390)]
MOTION_VIEWPORTS = [(1280, 900), (390, 844), (320, 640), (844, 390)]


def check_http(base):
    paths = [ROOT / name for name in PAGES]
    for directory in ("assets", "images"):
        paths.extend(p for p in (ROOT / directory).rglob("*") if p.is_file()
                     and p.suffix in (".css", ".js", ".jpg", ".png", ".webp", ".svg", ".woff2"))
    for path in paths:
        name = path.relative_to(ROOT).as_posix()
        with urlopen(urljoin(base, name), timeout=20) as response:
            assert response.status == 200 and response.read(), name
    print(f"PASS: {len(paths)} local pages/assets return nonempty HTTP 200", flush=True)


def check_browser(browser, base, mobile=False):
    mode = "mobile" if mobile else "desktop"
    context = browser.new_context(
        viewport={"width": 390 if mobile else 1440, "height": 844 if mobile else 1000},
        is_mobile=mobile, has_touch=mobile, reduced_motion="reduce",
        permissions=["clipboard-read", "clipboard-write"],
    )
    page = context.new_page()
    page.set_default_timeout(10000)
    errors, failed = [], []
    origin = urlsplit(base).netloc
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("response", lambda response: failed.append(f"{response.status}: {response.url}")
            if urlsplit(response.url).netloc == origin and response.status >= 400 else None)
    page.on("requestfailed", lambda request: failed.append(f"{request.failure}: {request.url}")
            if urlsplit(request.url).netloc == origin and "ERR_ABORTED" not in (request.failure or "") else None)

    def go(path):
        response = page.goto(urljoin(base, path), wait_until="load")
        assert response and response.ok, path

    def passed(message):
        print(f"PASS [{mode}]: {message}", flush=True)

    for path in PAGES:
        go(path)
        assert page.title() and page.locator("main").inner_text().strip(), path
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"Overflow: {path}"
    passed("all 18 original pages load without horizontal overflow")

    go("index.html")
    assert page.locator("body").evaluate("el => el.classList.contains('cover')")
    expect(page.locator("[data-seal]")).to_be_visible()
    if page.locator("[data-seal]").evaluate("el => el.tagName") == "A":
        assert page.locator("[data-seal]").get_attribute("href") == "home.html"
    page.locator("[data-seal]").click()
    page.locator("[data-domain-input]").fill("검증영지")
    page.locator("[data-enter]").click()
    page.wait_for_url("**/home.html")
    expect(page.locator("[data-domain]").first).to_have_text("검증영지")
    passed("original seal → writ → name → home entry flow")

    assert page.locator(".frieze .fg").evaluate_all("els => els.map(el => el.getAttribute('href'))") == [f"char/{code}.html" for code in FIGURES]
    assert page.locator(".frieze .fg img").evaluate_all("els => els.map(el => el.getAttribute('src'))") == [f"images/fig/{code}.jpg" for code in FIGURES]
    expect(page.locator(".frieze .fg img")).to_have_count(6)
    expect(page.locator(".deck .tilt")).to_have_count(12)
    assert page.locator(".tabs a").evaluate_all("els => els.map(el => el.getAttribute('href'))") == ["world.html", "domain.html", "characters.html", "start.html"]
    passed("six original hero figures in order, twelve cards, original navigation")

    page.locator('.dial [data-season="spring"]').click()
    page.reload(wait_until="load")
    expect(page.locator("html")).to_have_attribute("data-season", "spring")
    expect(page.locator('.dial [data-season="spring"]')).to_have_attribute("aria-pressed", "true")
    passed("season selection and persistence")

    page.locator("[data-g-range]").fill("4")
    expect(page.locator("[data-g-name]").first).to_have_text("도시")
    expect(page.locator("[data-g-pop]").first).to_have_text("20,000")
    assert page.locator(".town .st.on").evaluate_all("els => els.every(el => +el.dataset.s <= 4)")
    page.locator('[data-g="0"]').click()
    expect(page.locator("[data-g-name]").first).to_have_text("개척지")
    expect(page.locator("[data-g-pop]").first).to_have_text("50")
    assert page.locator(".town .st.on").evaluate_all("els => els.every(el => +el.dataset.s === 0)")
    page.locator('[data-e="tax"]').click()
    expect(page.locator('.est-col[data-k="knight"] [data-lv]')).to_have_text("지지")
    expect(page.locator('.est-col[data-k="village"] [data-lv]')).to_have_text("불만")
    page.locator('[data-e="tax"]').click()
    expect(page.locator('.est-col[data-k="village"] [data-lv]')).to_have_text("중립")
    passed("original growth slider/stages and reversible faction decisions")

    page.locator('.tabs a[href="characters.html"]').click()
    page.wait_for_url("**/characters.html")
    filters = page.locator(".sel-f button")
    assert filters.all_text_contents() == FILTER_LABELS
    filters.nth(2).click()
    expect(page.locator(".roster > li:visible")).to_have_count(2)
    expect(page.locator('[data-f="이름"]')).to_have_text("시아렐")
    second = page.locator(".roster > li:visible .ro").nth(1)
    second.tap() if mobile else second.hover()
    expect(page.locator('[data-f="이름"]')).to_have_text("두르간")
    assert filters.all_text_contents() == FILTER_LABELS
    page.locator("[data-f-link]").click()
    page.wait_for_url("**/char/h.html")
    expression = page.locator(".face-tabs button").nth(1)
    source = expression.get_attribute("data-src")
    expression.click()
    expect(page.locator("[data-face]")).to_have_attribute("src", source)
    page.keyboard.press("ArrowRight")
    expect(page.locator(".face-tabs button").nth(2)).to_have_attribute("aria-pressed", "true")
    passed("character filter labels, touch/hover selection, detail and expressions")

    go("world.html")
    assert page.locator(".map .rg").evaluate_all("els => els.map(el => el.dataset.r)") == REGIONS
    assert page.locator(".map").get_attribute("viewBox") == "0 0 900 560"
    for region in REGIONS:
        page.locator(f'.rg-list button[data-r="{region}"]').click()
        expect(page.locator(f'.rg-info[data-r="{region}"]')).to_be_visible()
        expect(page.locator(".rg-info:visible")).to_have_count(1)
        expect(page.locator(f'.rg-list button[data-r="{region}"]')).to_have_attribute("aria-current", "true")
        if region != "home":
            assert page.locator(f'.map .route[data-r="{region}"]').evaluate("el => el.classList.contains('on')")
    page.locator('.rg-list button[data-r="home"]').click()
    expect(page.locator('.rg-info[data-r="home"] h2')).to_have_text("검증영지")
    page.locator('.map .rg[data-r="seril"]').focus()
    page.keyboard.press("Enter")
    expect(page.locator('.rg-info[data-r="seril"]')).to_be_visible()
    passed("all six original map regions, routes, name, and keyboard selection")

    go("domain.html")
    row = page.locator("[data-tally] tbody tr").first
    row.locator('[data-d="-1"]').click()
    expect(row.locator("output")).to_have_text("0")
    row.locator('[data-d="1"]').click()
    expect(page.locator("[data-total]")).to_have_text("1동화")
    page.locator("[data-reset]").click()
    expect(page.locator("[data-total]")).to_have_text("0동화")
    passed("original price calculator and reset")

    go("start.html")
    page.locator('.slot[data-m="free"]').click()
    page.locator('[data-n="출신"]').fill("기사")
    expect(page.locator("[data-note-out]")).to_contain_text("[시작 모드] 자유모드")
    expect(page.locator("[data-note-out]")).to_contain_text("[영지 이름] 검증영지")
    expect(page.locator("[data-note-out]")).to_contain_text("[출신] 기사")
    page.locator("[data-copy]").click()
    expect(page.locator("[data-copied]")).to_have_text("복사했습니다.")
    assert page.evaluate("navigator.clipboard.readText()") == page.locator("[data-note-out]").inner_text()
    passed("original modes, note composition, and clipboard")

    assert not errors, f"JavaScript errors: {errors}"
    assert not failed, f"Broken local resource requests: {failed}"
    passed("no JavaScript errors or broken local resource requests")
    context.close()


def normal_motion(browser, base, viewport=(1280, 900)):
    width, height = viewport
    context = browser.new_context(reduced_motion="no-preference", viewport={"width": width, "height": height})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(urljoin(base, "index.html"), wait_until="load")
    page.evaluate("""() => {
        window.__envelopeOpeningSamples = [];
        const sample = () => {
            const writ = document.querySelector('[data-writ]');
            if (writ.dataset.state === 'opening') {
                const box = document.querySelector('.envelope-art').getBoundingClientRect();
                window.__envelopeOpeningSamples.push({
                    ratio: box.width / box.height,
                    overflow: document.documentElement.scrollWidth > innerWidth + 1,
                });
            }
            if (writ.dataset.state !== 'ready') requestAnimationFrame(sample);
        };
        requestAnimationFrame(sample);
    }""")
    page.locator("[data-seal]").click()
    page.wait_for_function("!document.querySelector('[data-domain-input]').closest('[inert]')")
    samples = page.evaluate("window.__envelopeOpeningSamples")
    assert len(samples) >= 3, f"{width}×{height}: opening animation was not sampled"
    assert all(abs(sample["ratio"] - 1.5) < .005 for sample in samples), f"{width}×{height}: envelope stretched during opening"
    assert not any(sample["overflow"] for sample in samples), f"{width}×{height}: horizontal overflow during opening"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"{width}×{height}: horizontal overflow after opening"

    for selector in ("[data-domain-input]", "[data-enter]"):
        control = page.locator(selector)
        control.scroll_into_view_if_needed()
        expect(control).to_be_in_viewport(ratio=1)
        assert control.evaluate("el => {const r=el.getBoundingClientRect(); const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2); return hit === el || el.contains(hit);}"), f"{width}×{height}: {selector} obstructed"
    page.locator("[data-domain-input]").fill("연출검증")
    expect(page.locator("[data-domain-input]")).to_have_value("연출검증")
    page.locator("[data-enter]").click()
    page.wait_for_url("**/home.html")
    expect(page.locator("[data-domain]").first).to_have_text("연출검증")
    assert not errors, errors
    print(f"PASS [normal motion {width}×{height}]: envelope stays 3:2, no horizontal overflow, controls reachable, name/entry work", flush=True)
    context.close()


def entry_accessibility(browser, base):
    """Exercise the approved envelope layout and keyboard flow at edge sizes."""
    for index, (width, height) in enumerate(ENTRY_VIEWPORTS):
        context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
        page = context.new_page()
        page.set_default_timeout(10000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(urljoin(base, "index.html"), wait_until="load")
        page.evaluate("document.fonts.ready")
        writ = page.locator("[data-writ]")
        seal = page.locator("[data-seal]")
        name = page.locator("[data-domain-input]")
        enter = page.locator("[data-enter]")
        box = writ.bounding_box()
        assert box, "Missing envelope bounds"
        horizontal_delta = abs(box["x"] + box["width"] / 2 - width / 2)
        assert horizontal_delta <= 1, f"{width}×{height}: envelope horizontal offset {horizontal_delta:.2f}px"
        if box["height"] + 32 <= height:
            vertical_delta = abs(box["y"] + box["height"] / 2 - height / 2)
            assert vertical_delta <= 2, f"{width}×{height}: entry group vertical offset {vertical_delta:.2f}px"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"{width}×{height}: horizontal overflow"

        # Closed letter controls must not steal Tab focus through a clipped panel.
        for _ in range(6):
            page.keyboard.press("Tab")
            assert not page.evaluate("document.activeElement.matches('[data-domain-input], [data-enter]')"), "Closed letter control received focus"
        page.evaluate("document.activeElement.blur()")
        for key in ("x", "ArrowDown", "Escape"):
            page.keyboard.press(key)
        assert not page.locator("body").evaluate("el => el.classList.contains('open')"), "Unrelated key opened the envelope"
        expect(page).to_have_url(re.compile(r"/index\.html$"))

        seal.focus()
        page.keyboard.press("Enter" if index % 2 == 0 else "Space")
        expect(name).to_be_editable()
        page.wait_for_function("!document.querySelector('[data-domain-input]').closest('[inert]')")
        name.scroll_into_view_if_needed()
        expect(name).to_be_visible()
        name.fill("중앙검증")

        def reachable(locator, description):
            locator.scroll_into_view_if_needed()
            bounds = locator.bounding_box()
            assert bounds and bounds["width"] > 0 and bounds["height"] > 0, description
            assert bounds["x"] >= -1 and bounds["x"] + bounds["width"] <= width + 1, description
            assert bounds["y"] >= -1 and bounds["y"] + bounds["height"] <= height + 1, description
            assert locator.evaluate("el => { const r=el.getBoundingClientRect(); const hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2); return hit === el || el.contains(hit); }"), f"{description} is covered by another layer"

        reachable(name, f"{width}×{height} name input")
        name.focus()
        page.keyboard.press("Enter")
        assert not page.locator("body").evaluate("el => el.classList.contains('go')"), "Input Enter unexpectedly left the letter"
        name.focus()
        name.dispatch_event("keydown", {"key": "Enter", "code": "Enter", "isComposing": True, "bubbles": True})
        assert not page.locator("body").evaluate("el => el.classList.contains('go')"), "IME composition Enter unexpectedly left the letter"
        expect(page).to_have_url(re.compile(r"/index\.html$"))
        reachable(enter, f"{width}×{height} entry link")
        enter.focus()
        page.keyboard.press("Enter")
        page.wait_for_url("**/home.html")
        expect(page.locator("[data-domain]").first).to_have_text("중앙검증")
        assert not errors, errors
        print(f"PASS [entry {width}×{height}]: centered envelope, reachable name/CTA, Tab/Enter/Space/IME safety", flush=True)
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8766/")
    parser.add_argument("--chromium", default=shutil.which("chromium"))
    parser.add_argument("--entry-only", action="store_true", help="Run only the five-size envelope accessibility checks")
    args = parser.parse_args()
    base = args.base_url.rstrip("/") + "/"
    if not args.entry_only:
        check_http(base)
    with sync_playwright() as p:
        options = {"headless": True}
        if args.chromium:
            options["executable_path"] = args.chromium
        browser = p.chromium.launch(**options)
        try:
            if not args.entry_only:
                check_browser(browser, base)
                check_browser(browser, base, mobile=True)
                for viewport in MOTION_VIEWPORTS:
                    normal_motion(browser, base, viewport)
            entry_accessibility(browser, base)
        finally:
            browser.close()
    print("All original-site browser checks passed.", flush=True)


if __name__ == "__main__":
    main()
