#!/usr/bin/env python3
"""Check only the four authorized margin notes on home/world at three widths.

Requires optional Playwright Python and Chromium plus a running static server.
"""
import argparse
import shutil
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import expect, sync_playwright

from original_smoke import assert_no_overflow
from preserve_plan import LORD_NOTES


def check_notes(browser, base, width):
    context = browser.new_context(viewport={"width": width, "height": 900 if width > 720 else 844}, reduced_motion="reduce")
    page = context.new_page()
    errors, failures = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("response", lambda response: failures.append(f"{response.status}: {response.url}")
            if urlsplit(response.url).netloc == urlsplit(base).netloc and response.status >= 400 else None)
    try:
        for path, expected in LORD_NOTES.items():
            page.goto(urljoin(base, path), wait_until="load")
            page.evaluate("document.fonts.ready")
            notes = page.locator("[data-lord-note]")
            assert sorted(notes.all_text_contents()) == sorted(expected), f"{width}px {path}: note text changed"
            assert page.evaluate("[...document.fonts].some(font => font.family.includes('ERN Margin Pen') && font.status === 'loaded')"), "Handwriting font did not load"
            assert_no_overflow(page, f"{width}px {path}")
            for index in range(notes.count()):
                note = notes.nth(index)
                note.evaluate("el => el.scrollIntoView({block: 'center', behavior: 'instant'})")
                expect(note).to_be_visible()
                # Rotated notes yield fractional IntersectionObserver ratios;
                # the actual ink bounds below still enforce every screen edge.
                expect(note).to_be_in_viewport(ratio=.99)
                geometry = note.evaluate("""note => {
                    const range = document.createRange(); range.selectNodeContents(note);
                    const ink = [...range.getClientRects()].filter(r => r.width && r.height);
                    const area = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) *
                        Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
                    const candidates = [...document.querySelectorAll('main a, main button, main input, main select, main textarea, main p, main h1, main h2, main h3, main dt, main dd, main td, main th')]
                        .filter(el => !note.contains(el) && !el.contains(note) && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
                    const collisions = candidates.filter(el => ink.some(r => area(r, el.getBoundingClientRect()) > 2))
                        .map(el => ({tag: el.tagName, text: el.textContent.trim().slice(0, 70)}));
                    const box = note.getBoundingClientRect(), hit = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2);
                    return {
                        inside: ink.every(r => r.left >= -1 && r.right <= innerWidth + 1 && r.top >= -1 && r.bottom <= innerHeight + 1),
                        unobstructed: hit === note || note.contains(hit),
                        collisions,
                        interactive: note.querySelectorAll('a,button,input,select,textarea,[tabindex],[contenteditable]').length,
                        generatedText: [note, ...note.querySelectorAll('*')].flatMap(el => ['::before', '::after'].map(pseudo => getComputedStyle(el, pseudo).content))
                            .filter(content => !['none', 'normal', '\"\"', "''"].includes(content)),
                    };
                }""")
                assert geometry["inside"], f"{width}px {path}: note ink extends beyond the screen"
                assert geometry["unobstructed"], f"{width}px {path}: note is covered by another element"
                assert not geometry["interactive"], f"{width}px {path}: note acquired an interactive child"
                assert not geometry["generatedText"], f"{width}px {path}: note has additional generated text"
                assert not geometry["collisions"], f"{width}px {path}: note overlaps original text/controls: {geometry['collisions']}"
                assert_no_overflow(page, f"{width}px {path} note {index + 1}")
            print(f"PASS notes {width}px {path}: exact text, handwriting font, visible, no overlap or overflow", flush=True)
        assert not errors, errors
        assert not failures, failures
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
            for width in (320, 390, 1440):
                check_notes(browser, args.base_url.rstrip("/") + "/", width)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
