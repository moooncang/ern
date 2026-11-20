#!/usr/bin/env python3
"""Exercise the manuscript's progressive visual controls in a real browser.

Requires the optional Playwright Python package and Chromium. Start the static
server, then run: python3 tests/visual_smoke.py --base-url http://127.0.0.1:8766/
"""
import argparse
import re
import shutil
from urllib.parse import urljoin

from playwright.sync_api import expect, sync_playwright

from original_smoke import assert_no_overflow


def check_visual(browser, base, width, motion):
    label = f"{width}px, {motion} motion"
    context = browser.new_context(
        viewport={"width": width, "height": 900 if width > 720 else 844},
        is_mobile=width <= 720, has_touch=width <= 720,
        reduced_motion=motion,
    )
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))

    def ribbon_at(index):
        page.wait_for_function("""index => {
            const marker = document.querySelector('.tab-ribbon');
            const link = document.querySelectorAll('.tabs a')[index];
            const a = marker.getBoundingClientRect(), b = link.getBoundingClientRect();
            return !marker.hidden && Math.abs(a.left - b.left) < 1 && Math.abs(a.width - b.width) < 1;
        }""", arg=index)

    try:
        page.goto(urljoin(base, "index.html"), wait_until="load")
        expect(page.locator(".tab-ribbon, .reading-progress, .deck-tools")).to_have_count(0)

        page.goto(urljoin(base, "world.html"), wait_until="load")
        page.evaluate("document.fonts.ready")
        expect(page.locator(".tab-ribbon")).to_have_attribute("aria-hidden", "true")
        expect(page.locator(".reading-progress")).to_have_attribute("aria-hidden", "true")
        ribbon_at(0)
        links = page.locator(".tabs a")
        links.nth(3).focus()
        ribbon_at(3)
        links.nth(3).evaluate("el => el.blur()")
        ribbon_at(0)
        if width > 720:
            links.nth(1).hover()
            ribbon_at(1)
            page.mouse.move(0, 0)
            ribbon_at(0)

        page.evaluate("scrollTo({top: document.documentElement.scrollHeight, behavior: 'instant'})")
        page.wait_for_function("new DOMMatrix(getComputedStyle(document.querySelector('.reading-progress')).transform).a > .99")
        expect(page.locator(".top")).to_have_class(re.compile(r".*\bhas-scrolled\b.*"))
        assert_no_overflow(page, f"{label}: world foot")
        page.evaluate("scrollTo({top: 0, behavior: 'instant'})")
        page.wait_for_function("new DOMMatrix(getComputedStyle(document.querySelector('.reading-progress')).transform).a < .01")
        page.wait_for_function("!document.querySelector('.top').classList.contains('has-scrolled')")

        links.nth(3).click()
        page.wait_for_url("**/start.html")
        expect(page.locator("main")).to_be_visible()
        page.go_back(wait_until="load")
        page.wait_for_url("**/world.html")
        expect(page.locator(".tab-ribbon")).to_have_count(1)
        expect(page.locator(".reading-progress")).to_have_count(1)
        expect(page.locator("main")).to_be_visible()
        page.evaluate("document.activeElement.blur()")
        page.mouse.move(0, 0)
        ribbon_at(0)

        page.goto(urljoin(base, "home.html"), wait_until="load")
        deck = page.locator(".deck")
        previous = page.get_by_role("button", name="이전 인물 카드", exact=True)
        following = page.get_by_role("button", name="다음 인물 카드", exact=True)
        counter = page.locator(".deck-count")
        expect(counter).to_have_text("01 / 12")
        expect(previous).to_be_disabled()
        expect(following).to_be_enabled()
        following.click()
        expect(counter).to_have_text("02 / 12")
        previous.click()
        expect(counter).to_have_text("01 / 12")
        expect(previous).to_be_disabled()
        deck.focus()
        page.keyboard.press("ArrowRight")
        expect(counter).to_have_text("02 / 12")
        assert deck.locator(".tilt").first.evaluate("""el => {
            const event = new KeyboardEvent('keydown', {key:'ArrowRight', bubbles:true, cancelable:true});
            el.dispatchEvent(event);
            return !event.defaultPrevented;
        }"""), "Deck handler captured arrow keys from a descendant link"
        deck.evaluate("el => el.scrollTo({left: el.scrollWidth, behavior: 'instant'})")
        expect(following).to_be_disabled()
        expect(counter).to_have_text("12 / 12")
        expect(previous).to_be_enabled()
        previous.click()
        expect(counter).to_have_text("11 / 12")
        expect(following).to_be_enabled()
        following.click()
        expect(counter).to_have_text("12 / 12")
        expect(following).to_be_disabled()
        assert_no_overflow(page, f"{label}: deck end")

        page.locator('[data-g="4"]').click()
        expect(page.locator("[data-g-name]").first).to_have_text("도시")
        if motion == "no-preference":
            page.wait_for_function("document.querySelector('.g-info').getAnimations().some(a => a.playState === 'running')")
            page.emulate_media(reduced_motion="reduce")
            page.wait_for_function("document.querySelector('.g-info').getAnimations().every(a => a.playState !== 'running')")
        else:
            assert page.locator(".g-info").evaluate("el => el.getAnimations().every(a => a.playState !== 'running')")
        page.locator('[data-e="tax"]').click()
        expect(page.locator('.est-col[data-k="knight"] [data-lv]')).to_have_text("지지")
        assert page.locator("[data-est-out]").evaluate("el => el.getAnimations().every(a => a.playState !== 'running')"), "Reduced-motion selection animated"
        assert_no_overflow(page, f"{label}: faction selection")
        assert not errors, f"{label}: JavaScript errors: {errors}"
        print(f"PASS [visual {label}]: ribbon, progress, navigation/back, gallery controls, keyboard scope, live motion preference", flush=True)
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8766/")
    parser.add_argument("--chromium", default=shutil.which("chromium"))
    args = parser.parse_args()
    with sync_playwright() as p:
        options = {"headless": True}
        if args.chromium:
            options["executable_path"] = args.chromium
        browser = p.chromium.launch(**options)
        try:
            for width in (1440, 390, 320):
                for motion in ("reduce", "no-preference"):
                    check_visual(browser, args.base_url.rstrip("/") + "/", width, motion)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
