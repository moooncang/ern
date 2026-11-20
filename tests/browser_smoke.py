#!/usr/bin/env python3
"""Exercise the generated site against a running HTTP server.

Requires the optional Playwright Python package and Chromium. Example:
    python3 -m http.server 8766 --bind 0.0.0.0
    python3 tests/browser_smoke.py --base-url http://127.0.0.1:8766
"""
import argparse
import re
import shutil
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import expect, sync_playwright


PAGES = ["index.html", "home.html", "world.html", "domain.html", "characters.html", "start.html"] + [
    f"char/{code}.html" for code in "abcdefghijkl"
]


def run(browser, base_url, mobile=False):
    label = "mobile" if mobile else "desktop"
    context = browser.new_context(
        viewport={"width": 390 if mobile else 1440, "height": 844 if mobile else 1000},
        is_mobile=mobile,
        has_touch=mobile,
        reduced_motion="reduce",
        permissions=["clipboard-read", "clipboard-write"],
    )
    page = context.new_page()
    page.set_default_timeout(10000)
    errors, broken = [], []
    origin = urlsplit(base_url).netloc
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("response", lambda response: broken.append(f"{response.status} {response.url}")
            if urlsplit(response.url).netloc == origin and response.status >= 400 else None)
    page.on("requestfailed", lambda request: broken.append(f"{request.failure} {request.url}")
            if urlsplit(request.url).netloc == origin and "ERR_ABORTED" not in (request.failure or "") else None)

    def go(path):
        response = page.goto(urljoin(base_url, path), wait_until="load")
        assert response and response.ok, path

    def passed(message):
        print(f"PASS [{label}] {message}", flush=True)

    for path in PAGES:
        go(path)
        assert page.title() and page.locator("main").inner_text().strip(), path
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"Horizontal overflow: {path}"
    passed("18 pages load without horizontal overflow")

    go("index.html")
    page.locator("[data-open-writ]").first.click()
    expect(page.locator("[data-ceremony]")).to_be_visible()
    page.locator("[data-seal]").click()
    page.locator("[data-ceremony] [data-domain-input]").fill("새벽영지")
    page.locator("[data-enter]").click()
    page.wait_for_url("**/start.html")
    expect(page.locator("[data-domain-input]")).to_have_value("새벽영지")
    expect(page.locator("[data-note-out]")).to_contain_text("[영지 이름] 새벽영지")
    passed("seal ceremony, naming, and arrival at the starting guide")

    go("index.html")
    if mobile:
        expect(page.locator("[data-menu-toggle]")).to_be_visible()
        assert page.locator("#site-nav").evaluate("nav => nav.inert")
        page.locator("[data-menu-toggle]").click()
        expect(page.locator("[data-menu-toggle]")).to_have_attribute("aria-expanded", "true")
        page.keyboard.press("Escape")
        expect(page.locator("[data-menu-toggle]")).to_have_attribute("aria-expanded", "false")
        expect(page.locator("[data-menu-toggle]")).to_be_focused()
        page.locator("[data-menu-toggle]").click()
        page.locator('#site-nav a[href="world.html"]').click()
        page.wait_for_url("**/world.html")
        expect(page.locator("[data-menu-toggle]")).to_have_attribute("aria-expanded", "false")
        go("index.html")
        passed("mobile navigation, Escape, focus return, and link navigation")

    if mobile:
        # The compact header omits the desktop keyboard-help button.
        page.keyboard.press("?")
    else:
        page.locator("[data-help]").click()
    expect(page.locator("[data-shortcuts]")).to_be_visible()
    before = page.url
    page.keyboard.press("1")
    assert page.url == before, "Background keyboard shortcut navigated through the dialog"
    page.keyboard.press("Escape")
    expect(page.locator("[data-shortcuts]")).not_to_be_visible()
    page.keyboard.press("?")
    expect(page.locator("[data-shortcuts]")).to_be_visible()
    page.locator("[data-close-help]").click()
    passed("help dialog, keyboard isolation, Escape, and ? shortcut")

    page.locator('button[data-season="spring"]').first.click()
    expect(page.locator("html")).to_have_attribute("data-season", "spring")
    page.reload(wait_until="load")
    expect(page.locator("html")).to_have_attribute("data-season", "spring")
    passed("season choice survives reload")

    gallery = page.locator("[data-gallery-track]")
    expect(page.locator("[data-gallery-prev]")).to_be_disabled()
    page.locator("[data-gallery-next]").click()
    page.wait_for_function('document.querySelector("[data-gallery-track]").scrollLeft > 0')
    expect(page.locator("[data-gallery-prev]")).to_be_enabled()
    # Reach the final card through the same next control users operate.
    for _ in range(20):
        page.wait_for_function('''() => {
            const track = document.querySelector('[data-gallery-track]');
            return document.querySelector('[data-gallery-next]').disabled ===
                (track.scrollLeft >= track.scrollWidth - track.clientWidth - 1);
        }''')
        if page.locator("[data-gallery-next]").is_disabled():
            break
        previous_position = gallery.evaluate("el => el.scrollLeft")
        page.locator("[data-gallery-next]").click()
        page.wait_for_function('before => document.querySelector("[data-gallery-track]").scrollLeft > before', arg=previous_position)
    expect(page.locator("[data-gallery-next]")).to_be_disabled()
    assert gallery.evaluate("el => el.scrollLeft + el.clientWidth >= el.scrollWidth - 2")
    passed("character gallery navigation and end boundary")

    growth = page.locator("[data-g-range]")
    growth.fill("4")
    expect(page.locator("[data-g-name]").first).to_have_text("도시")
    expect(page.locator("[data-g-pop]").first).to_have_text("20,000")
    page.locator('[data-g="0"]').click()
    expect(page.locator("[data-g-pop]").first).to_have_text("50")
    page.locator('[data-e="tax"]').click()
    expect(page.locator('.est-col[data-k="knight"] [data-lv]')).to_have_text("지지")
    expect(page.locator('.est-col[data-k="village"] [data-lv]')).to_have_text("불만")
    page.locator('[data-e="tax"]').click()
    expect(page.locator('.est-col[data-k="village"] [data-lv]')).to_have_text("중립")
    passed("settlement growth and reversible faction decisions")

    page.evaluate("scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_function('document.querySelector("[data-reading-progress]").style.transform === "scaleX(1)"')
    expect(page.locator("header.top")).to_have_class(re.compile(r".*\bscrolled\b.*"))
    passed("reading progress and scrolled header")

    go("characters.html")
    filters = page.locator(".sel-f button")
    assert filters.all_text_contents() == ["전체", "가신 · 영지", "변경 너머", "바깥"]
    filters.nth(2).click()
    expect(page.locator(".roster > li:visible")).to_have_count(2)
    expect(page.locator('[data-f="이름"]')).to_have_text("시아렐")
    target = page.locator(".roster > li:visible .ro").nth(1)
    if mobile:
        target.tap()
    else:
        target.hover()
    expect(page.locator('[data-f="이름"]')).to_have_text("두르간")
    assert filters.all_text_contents() == ["전체", "가신 · 영지", "변경 너머", "바깥"]
    page.locator("[data-f-link]").click()
    page.wait_for_url("**/char/h.html")
    expression = page.locator(".face-tabs button").nth(1)
    src = expression.get_attribute("data-src")
    expression.click()
    expect(page.locator("[data-face]")).to_have_attribute("src", src)
    page.keyboard.press("ArrowRight")
    expect(page.locator(".face-tabs button").nth(2)).to_have_attribute("aria-pressed", "true")
    passed("character filters retain labels, selection, details, and expression keys")

    go("world.html")
    page.locator('.rg-list button[data-r="seril"]').click()
    expect(page.locator('.rg-info[data-r="seril"]')).to_be_visible()
    expect(page.locator('.rg-info[data-r="home"]')).not_to_be_visible()
    assert page.url.endswith("#seril")
    passed("map selection and region URL")

    go("domain.html")
    row = page.locator("[data-tally] tbody tr").first
    row.locator('[data-d="-1"]').click()
    expect(row.locator("output")).to_have_text("0")
    row.locator('[data-d="1"]').click()
    expect(page.locator("[data-total]")).to_have_text("1동화")
    page.locator("[data-reset]").click()
    expect(page.locator("[data-total]")).to_have_text("0동화")
    passed("price calculator, nonnegative quantity, and reset")

    go("start.html")
    page.locator('.slot[data-m="free"]').click()
    page.locator('[data-n="출신"]').fill("몰락한 기사 가문")
    page.locator('[data-n="능력"]').fill("검술과 장부")
    expect(page.locator("[data-note-out]")).to_contain_text("[시작 모드] 자유모드")
    expect(page.locator("[data-note-out]")).to_contain_text("[영지 이름] 새벽영지")
    page.locator("[data-copy]").click()
    expect(page.locator("[data-copied]")).to_have_text("복사했습니다.")
    assert page.evaluate("navigator.clipboard.readText()") == page.locator("[data-note-out]").inner_text()
    go("start.html")
    expect(page.locator('[data-n="출신"]')).to_have_value("몰락한 기사 가문")
    expect(page.locator('.slot[data-m="free"]')).to_have_attribute("aria-selected", "true")
    expect(page.locator("[data-note-out]")).to_contain_text("[능력] 검술과 장부")
    go("home.html")
    go("start.html#hasa")
    expect(page.locator('.slot[data-m="hasa"]')).to_have_attribute("aria-selected", "true")
    passed("note generation, clipboard, saved draft, and explicit mode links")

    assert not errors, f"JavaScript exceptions: {errors}"
    assert not broken, f"Broken local resources: {broken}"
    passed("no JavaScript exceptions or broken local resource requests")
    context.close()


def normal_motion(browser, base_url):
    context = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="no-preference")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(urljoin(base_url, "index.html"), wait_until="load")
    page.locator("[data-open-writ]").first.click()
    page.locator("[data-seal]").click()
    page.locator("[data-ceremony] [data-domain-input]").fill("연출검증")
    page.locator("[data-enter]").click()
    page.wait_for_url("**/start.html")
    expect(page.locator("[data-domain-input]")).to_have_value("연출검증")
    assert not errors, errors
    print("PASS [normal motion] animated ceremony and navigation", flush=True)
    context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8765/", help="Running site URL")
    parser.add_argument("--chromium", default=shutil.which("chromium"), help="Optional system Chromium executable")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/") + "/"
    with sync_playwright() as playwright:
        options = {"headless": True}
        if args.chromium:
            options["executable_path"] = args.chromium
        browser = playwright.chromium.launch(**options)
        try:
            run(browser, base_url)
            run(browser, base_url, mobile=True)
            normal_motion(browser, base_url)
        finally:
            browser.close()
    print("All browser smoke checks passed.", flush=True)


if __name__ == "__main__":
    main()
