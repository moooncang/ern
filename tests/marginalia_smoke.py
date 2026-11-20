#!/usr/bin/env python3
"""Check only the four authorized margin notes on home/world at three widths.

Requires optional Playwright Python and Chromium plus a running static server.
"""
import argparse
import json
import re
import shutil
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import expect, sync_playwright

from original_smoke import assert_no_overflow
from preserve_plan import LORD_NOTES


def background_graphic(locator):
    """Decode the actual CSS image, rather than accepting a nonempty URL."""
    result = locator.evaluate("""async el => {
        const style = getComputedStyle(el), match = style.backgroundImage.match(/url\\(["']?([^"')]+)["']?\\)/);
        if (!match) return null;
        const image = new Image(); image.src = match[1]; await image.decode();
        return {url: image.src, width: image.naturalWidth, height: image.naturalHeight, position: style.backgroundPosition};
    }""")
    assert result and result["width"] > 0 and result["height"] > 0, "Painted note/drawing image did not decode"
    assert re.search(r"\.(webp|png|jpe?g)$", urlsplit(result["url"]).path, re.I), "Notes must be painted raster artwork"
    return result


def check_notes(browser, base, width):
    context = browser.new_context(viewport={"width": width, "height": 900 if width > 720 else 844}, reduced_motion="reduce")
    page = context.new_page()
    errors, failures, font_requests = [], [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("request", lambda request: font_requests.append(request.url)
            if re.search(r"margin-font\.css|margin-pen|ern-margin-pen", request.url) else None)
    page.on("response", lambda response: failures.append(f"{response.status}: {response.url}")
            if urlsplit(response.url).netloc == urlsplit(base).netloc and response.status >= 400 else None)
    try:
        for path, expected in LORD_NOTES.items():
            page.goto(urljoin(base, path), wait_until="load")
            page.evaluate("document.fonts.ready")
            notes = page.locator("[data-lord-note]")
            assert sorted(notes.all_text_contents()) == sorted(expected), f"{width}px {path}: note text changed"
            assert not page.evaluate("[...document.fonts].some(font => font.family.includes('ERN Margin Pen'))"), "The removed handwriting font is still declared"
            assert page.locator('link[href*="margin-font.css"]').count() == 0, "The removed handwriting stylesheet is still linked"
            assert_no_overflow(page, f"{width}px {path}")
            for index in range(notes.count()):
                note = notes.nth(index)
                note.evaluate("el => el.scrollIntoView({block: 'center', behavior: 'instant'})")
                expect(note).to_be_visible()
                # Rotated notes yield fractional IntersectionObserver ratios;
                # the actual graphic bounds below still enforce every screen edge.
                expect(note).to_be_in_viewport(ratio=.99)
                background_graphic(note)
                assert note.text_content().strip() in note.aria_snapshot(), f"{width}px {path}: original note is missing from accessibility output"
                geometry = note.evaluate("""note => {
                    const box = note.getBoundingClientRect(), span = note.querySelector('span');
                    const textBox = span.getBoundingClientRect(), textStyle = getComputedStyle(span);
                    const area = (a, b) => Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) *
                        Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
                    const candidates = [...document.querySelectorAll('main a, main button, main input, main select, main textarea, main p, main h1, main h2, main h3, main dt, main dd, main td, main th')]
                        .filter(el => !note.contains(el) && !el.contains(note) && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
                    const collisions = candidates.filter(el => area(box, el.getBoundingClientRect()) > 2)
                        .map(el => ({tag: el.tagName, text: el.textContent.trim().slice(0, 70)}));
                    const hit = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2);
                    return {
                        inside: box.left >= -1 && box.right <= innerWidth + 1 && box.top >= -1 && box.bottom <= innerHeight + 1,
                        unobstructed: hit === note || note.contains(hit),
                        textClipped: textStyle.position === 'absolute' && textBox.width <= 1.5 && textBox.height <= 1.5 &&
                            (textStyle.overflow === 'hidden' || textStyle.clipPath !== 'none' || textStyle.clip !== 'auto') &&
                            textStyle.display !== 'none' && textStyle.visibility !== 'hidden',
                        collisions,
                        interactive: note.querySelectorAll('a,button,input,select,textarea,[tabindex],[contenteditable]').length,
                        generatedText: [note, ...note.querySelectorAll('*')].flatMap(el => ['::before', '::after'].map(pseudo => getComputedStyle(el, pseudo).content))
                            .filter(content => !['none', 'normal', '\"\"', "''"].includes(content)),
                    };
                }""")
                assert geometry["inside"], f"{width}px {path}: note ink extends beyond the screen"
                assert geometry["unobstructed"], f"{width}px {path}: note is covered by another element"
                assert geometry["textClipped"], f"{width}px {path}: accessible note text is not visually clipped"
                assert not geometry["interactive"], f"{width}px {path}: note acquired an interactive child"
                assert not geometry["generatedText"], f"{width}px {path}: note has additional generated text"
                assert not geometry["collisions"], f"{width}px {path}: note overlaps original text/controls: {geometry['collisions']}"
                assert_no_overflow(page, f"{width}px {path} note {index + 1}")
            if path == "home.html":
                stages = json.loads(page.locator("[data-grow]").get_attribute("data-stages"))
                assert len(stages) == 6
                positions = set()
                for index, stage in enumerate(stages):
                    page.locator("[data-g-range]").fill(str(index))
                    expect(page.locator("[data-g-name]").first).to_have_text(stage[0])
                    layer = page.locator(f'[data-grow] .st[data-s="{index}"]')
                    assert layer.evaluate("el => +getComputedStyle(el).opacity === 1"), f"{width}px: selected growth study is hidden"
                    caption = layer.get_attribute("data-caption")
                    assert caption and caption.startswith(stage[0] + " 구조도."), "Growth study is missing its stage description"
                    assert len([part for part in caption.split(".") if part.strip()]) == 5, "Each study must describe its four painted notes"
                    expect(page.locator("[data-grow] .town")).to_have_attribute("aria-label", caption)
                    art = background_graphic(layer)
                    positions.add(art["position"])
                    assert abs(art["width"] / art["height"] - 1.5) < .02, "Growth artwork must contain the six 3×2 studies"
                    assert_no_overflow(page, f"{width}px growth stage {index}")
                assert len(positions) == 6, "Growth stages reuse the same sprite position"
            print(f"PASS notes {width}px {path}: painted graphics, accessible exact text, no font, overlap or overflow" + (", six growth stages" if path == "home.html" else ""), flush=True)
        assert not errors, errors
        assert not failures, failures
        assert not font_requests, f"Removed handwriting font/stylesheet requested: {font_requests}"
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
