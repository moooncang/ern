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
MOTION_VIEWPORTS = list(ENTRY_VIEWPORTS)


def assert_no_overflow(page, label):
    if page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"):
        return
    offenders = page.evaluate("""() => [...document.querySelectorAll('body *')]
        .filter(el => {
            const rect = el.getBoundingClientRect();
            return rect.width && rect.right > innerWidth + 1;
        }).slice(0, 10).map(el => ({
            tag: el.tagName, class: el.getAttribute('class'),
            right: Math.round(el.getBoundingClientRect().right),
        }))""")
    raise AssertionError(f"Horizontal overflow ({label}): {offenders}")


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


def check_browser(browser, base, mobile=False, motion="reduce", viewport=None):
    viewport = viewport or {"width": 390 if mobile else 1440, "height": 844 if mobile else 1000}
    mode = ("mobile" if mobile else "desktop") + f", {viewport['width']}px, {motion} motion"
    context = browser.new_context(
        viewport=viewport,
        is_mobile=mobile, has_touch=mobile, reduced_motion=motion,
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
        page.evaluate("document.fonts.ready")
        assert page.title() and page.locator("main").inner_text().strip(), path
        assert_no_overflow(page, f"{mode}: {path}")
        if path == "world.html" and viewport["width"] >= 1100:
            trailing_gaps = page.locator("main > .sec > .wrap.narrow").evaluate_all("""els => els.map(el => {
                const contentBottom = Math.max(...[...el.children].map(child => child.getBoundingClientRect().bottom));
                return Math.round(el.getBoundingClientRect().bottom - contentBottom);
            })""")
            # A spanning grid heading once created 29 empty rows below each
            # short lore section. Allow framing space, but not blank screens.
            assert all(gap <= 160 for gap in trailing_gaps), f"Empty space after world lore sections: {trailing_gaps}px"
        if path != "index.html":
            # Visit the foot of long pages so lazy artwork and scroll-triggered
            # decoration also participate in the overflow/resource checks.
            page.evaluate("scrollTo(0, document.documentElement.scrollHeight)")
            page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
            assert_no_overflow(page, f"{mode}: {path} after scroll")
    passed("all 18 original pages load without horizontal overflow")

    go("index.html")
    assert page.locator("body").evaluate("el => el.classList.contains('cover')")
    expect(page.locator("[data-seal]")).to_be_visible()
    if page.locator("[data-seal]").evaluate("el => el.tagName") == "A":
        assert page.locator("[data-seal]").get_attribute("href") == "home.html"
    page.locator("[data-seal]").click()
    expect(page.locator("[data-writ]")).to_have_attribute("data-state", "ready", timeout=15000)
    page.locator("[data-domain-input]").fill("검증영지")
    expect(page.locator("[data-domain-input]")).to_have_value("검증영지")
    page.locator("[data-enter]").click()
    page.wait_for_url("**/home.html")
    expect(page.locator("[data-domain]").first).to_have_text("검증영지")
    expect(page.locator("[data-domain-or]")).to_have_text("검증영지의 장부는 아직 비어 있습니다.")
    passed("original seal → writ → name → home entry flow")

    assert page.locator(".frieze .fg").evaluate_all("els => els.map(el => el.getAttribute('href'))") == [f"char/{code}.html" for code in FIGURES]
    assert page.locator(".frieze .fg img").evaluate_all("els => els.map(el => el.getAttribute('src'))") == [f"images/fig/{code}.jpg" for code in FIGURES]
    expect(page.locator(".frieze .fg img")).to_have_count(6)
    expect(page.locator(".deck .tilt")).to_have_count(12)
    assert page.locator(".tabs a:not([data-music-nav])").evaluate_all("els => els.map(el => el.getAttribute('href'))") == ["world.html", "domain.html", "characters.html", "start.html"]
    expect(page.locator(".tabs a[data-music-nav]")).to_have_count(1)
    expect(page.locator(".tabs a[data-music-nav]")).to_have_attribute("href", "music.html")
    assert page.locator(".tabs a").nth(4).get_attribute("data-music-nav") is not None
    assert page.locator(".tabs a").count() == 5
    passed("six original hero figures in order, twelve cards, original navigation")

    page.locator('.dial [data-season="spring"]').click()
    page.reload(wait_until="load")
    expect(page.locator("html")).to_have_attribute("data-season", "spring")
    expect(page.locator('.dial [data-season="spring"]')).to_have_attribute("aria-pressed", "true")
    passed("season selection and persistence")

    sound = page.locator(".snd")
    sound_before = sound.get_attribute("aria-pressed")
    sound.click()
    expect(sound).to_have_attribute("aria-pressed", "false" if sound_before == "true" else "true")
    page.keyboard.press("m")
    expect(sound).to_have_attribute("aria-pressed", sound_before)
    assert page.evaluate("localStorage.getItem('ern-sfx')") == ("on" if sound_before == "true" else "off")
    passed("sound icon, keyboard shortcut, and saved preference")

    page.locator("[data-g-range]").fill("4")
    expect(page.locator("[data-g-name]").first).to_have_text("도시")
    expect(page.locator("[data-g-pop]").first).to_have_text("20,000")
    stages = page.locator("[data-grow] .st[data-s]")
    assert stages.count() >= 6, "The six visual development stages must remain available"
    assert page.locator("[data-grow] .st.on").evaluate_all("els => els.every(el => +el.dataset.s <= 4)")
    page.locator('[data-g="0"]').click()
    expect(page.locator("[data-g-name]").first).to_have_text("개척지")
    expect(page.locator("[data-g-pop]").first).to_have_text("50")
    assert page.locator("[data-grow] .st.on").evaluate_all("els => els.every(el => +el.dataset.s === 0)")
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


def normal_motion(browser, base, viewport=(1280, 900), resize_to=None, ready_resize_to=None):
    width, height = viewport
    label = f"{width}×{height}" + (f" → {resize_to[0]}×{resize_to[1]}" if resize_to else "")
    context = browser.new_context(reduced_motion="no-preference", viewport={"width": width, "height": height})
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(urljoin(base, "index.html"), wait_until="load")
    source_copy = page.locator("p[data-ink]").all_text_contents()
    assert len(source_copy) == 2, "The two original writ paragraphs must remain intact"
    page.evaluate("""() => {
        window.__envelopeOpeningSamples = [];
        const sample = timestamp => {
            const writ = document.querySelector('[data-writ]');
            const envelope = document.querySelector('.envelope-art');
            const quill = document.querySelector('.writing-quill');
            const paragraphs = [...document.querySelectorAll('p[data-ink]')];
            const box = envelope.getBoundingClientRect();
            const planeStyle = getComputedStyle(envelope);
            let visible = true, opacity = 1;
            for (let node = envelope; node; node = node.parentElement) {
                const style = getComputedStyle(node);
                opacity *= +style.opacity;
                if (style.display === 'none' || style.visibility === 'hidden') visible = false;
            }
            window.__envelopeOpeningSamples.push({
                timestamp, state: writ.dataset.state,
                // A parked envelope may rotate; compare its physical plane, not
                // the axis-aligned bounding rectangle enlarged by that rotation.
                ratio: envelope.offsetWidth / envelope.offsetHeight,
                physicalWidth: envelope.offsetWidth,
                physicalHeight: envelope.offsetHeight,
                fractionalPlaneError: Math.abs(parseFloat(planeStyle.width) - 1.5 * parseFloat(planeStyle.height)),
                x: box.x + scrollX, y: box.y + scrollY,
                width: box.width, height: box.height,
                visible: visible && opacity >= .15,
                viewportWidth: innerWidth,
                viewportHeight: innerHeight,
                inkProgress: +(writ.dataset.inkProgress || 0),
                inert: document.querySelector('.writ-body').inert,
                quillVisible: +getComputedStyle(quill).opacity > .1 && getComputedStyle(quill).display !== 'none',
                paragraphsHidden: paragraphs.every(p => getComputedStyle(p).clipPath.includes('100%')),
                overflow: document.documentElement.scrollWidth > innerWidth + 1,
            });
            const current = window.__envelopeOpeningSamples.at(-1);
            const stroke = +quill.dataset.strokeProgress;
            if (writ.dataset.state === 'writing' && quill.classList.contains('tracing') && stroke > .05 && stroke < .95) {
                const paragraph = paragraphs[+quill.dataset.inkLine];
                const range = document.createRange();
                range.setStart(paragraph.firstChild, +quill.dataset.inkOffset);
                range.setEnd(paragraph.firstChild, +quill.dataset.inkEnd);
                const glyph = range.getBoundingClientRect();
                const nib = quill.querySelector('.quill-tip').getBoundingClientRect();
                const paragraphBox = paragraph.getBoundingClientRect();
                const edge = parseFloat(paragraph.style.clipPath.split(',')[3]);
                current.nibError = Math.hypot(nib.x - (glyph.left + glyph.width * stroke), nib.y - (glyph.bottom - 2));
                current.clipError = Math.abs(nib.x - (paragraphBox.left + edge));
            }
            if (writ.dataset.state !== 'ready') requestAnimationFrame(sample);
        };
        requestAnimationFrame(sample);
    }""")
    page.locator("[data-seal]").click()
    if resize_to:
        page.wait_for_function("document.querySelector('[data-writ]').dataset.state === 'writing' && +document.querySelector('[data-writ]').dataset.inkProgress > .08")
        page.set_viewport_size({"width": resize_to[0], "height": resize_to[1]})
        width, height = resize_to
    page.wait_for_function("!document.querySelector('[data-domain-input]').closest('[inert]')")
    samples = page.evaluate("window.__envelopeOpeningSamples")
    transition = [sample for sample in samples if sample["state"] not in ("sealed", "ready", "leaving", None)]
    assert len(transition) >= 3, f"{width}×{height}: opening animation was not sampled"
    sequence = list(dict.fromkeys(sample["state"] for sample in transition))
    assert sequence == ["breaking", "unfolding", "extracting", "presenting", "writing"], f"{label}: unexpected writing order {sequence}"
    before_writing = [sample for sample in transition if sample["state"] != "writing"]
    assert all(sample["paragraphsHidden"] for sample in before_writing), f"{label}: ink appeared before extraction/presentation completed"
    writing = [sample for sample in transition if sample["state"] == "writing"]
    assert len(writing) >= 10 and any(0 < sample["inkProgress"] < .9 for sample in writing), f"{label}: no progressive writing observed"
    assert all(sample["inert"] for sample in transition), f"{label}: name/entry enabled before all writing finished"
    regressions = [(before["inkProgress"], after["inkProgress"], after["timestamp"] - before["timestamp"])
                   for before, after in zip(writing, writing[1:]) if after["inkProgress"] < before["inkProgress"] - .0002]
    assert not regressions, f"{label}: writing progress moved backward: {regressions[:5]}"
    traced = [sample for sample in writing if "nibError" in sample]
    assert len(traced) >= 8, f"{label}: insufficient real quill/glyph tracing samples"
    assert max(sample["nibError"] for sample in traced) < 2.5, f"{label}: nib left the active glyph (max {max(sample['nibError'] for sample in traced):.1f}px)"
    assert all(sample["clipError"] is not None and sample["clipError"] < 2.5 for sample in traced), f"{label}: visible ink edge did not follow the nib"
    assert all(sample["quillVisible"] for sample in traced), f"{label}: quill not visible while tracing"
    assert page.locator("p[data-ink]").all_text_contents() == source_copy, f"{label}: animated writing changed the original copy"
    assert page.locator("p[data-ink]").evaluate_all("els => els.every(el => getComputedStyle(el).clipPath === 'none' && +el.dataset.inkProgress === 1)"), f"{label}: final ink is incomplete"
    assert page.locator("[data-writ]").get_attribute("data-ink-progress") == "1", f"{label}: final progress is incomplete"
    # Fractional CSS sizes retain the physical plane through landing. Integer
    # offset* measurements may round by up to1.25px; neither measurement includes
    # the deliberate parked rotation.
    assert all(sample["fractionalPlaneError"] <= 1.25 and abs(sample["physicalWidth"] - 1.5 * sample["physicalHeight"]) <= 1.25 for sample in transition if sample["visible"]), f"{width}×{height}: visible envelope stretched during opening"
    # Ignore hidden re-layouts and account for slow frames. A visible object must
    # travel continuously, rather than teleport when the reading layout changes.
    for previous, current in zip(samples, samples[1:]):
        if not (previous["visible"] and current["visible"]):
            continue
        if previous["viewportWidth"] != current["viewportWidth"] or previous["viewportHeight"] != current["viewportHeight"]:
            continue
        delta_ms = current["timestamp"] - previous["timestamp"]
        allowance = max(16, previous["width"] * .12) * max(1, delta_ms / 32)
        previous_center = (previous["x"] + previous["width"] / 2, previous["y"] + previous["height"] / 2)
        current_center = (current["x"] + current["width"] / 2, current["y"] + current["height"] / 2)
        distance = sum((a - b) ** 2 for a, b in zip(previous_center, current_center)) ** .5
        assert distance <= allowance, f"{width}×{height}: visible envelope jumped {distance:.1f}px in {delta_ms:.1f}ms"
        assert abs(current["width"] - previous["width"]) <= allowance, f"{width}×{height}: visible envelope resized abruptly"
    assert not any(sample["overflow"] for sample in samples), f"{width}×{height}: horizontal overflow during opening"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"{width}×{height}: horizontal overflow after opening"
    parked = page.locator(".envelope-art")
    expect(parked).to_be_visible()
    assert parked.evaluate("el => !el.hidden && +getComputedStyle(el).opacity >= .15"), f"{width}×{height}: parked envelope disappeared"
    physical_error = parked.evaluate("el => Math.abs(el.offsetWidth - 1.5 * el.offsetHeight)")
    assert physical_error <= 1.25, f"{width}×{height}: parked envelope plane stretched"
    if ready_resize_to:
        page.set_viewport_size({"width": ready_resize_to[0], "height": ready_resize_to[1]})
        width, height = ready_resize_to
        page.wait_for_function("""() => {
            const pen = document.querySelector('.quill-tip').getBoundingClientRect();
            const paper = document.querySelector('.letter-document').getBoundingClientRect();
            return pen.x >= paper.left && pen.x <= paper.right && pen.y >= paper.top && pen.y <= paper.bottom &&
                document.documentElement.scrollWidth <= innerWidth + 1;
        }""", timeout=1500)
        expect(page.locator("[data-writ]")).to_have_attribute("data-state", "ready")
        expect(page.locator("[data-writ]")).to_have_attribute("data-ink-progress", "1")
        assert page.locator("p[data-ink]").all_text_contents() == source_copy
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "Ready-state resize introduced horizontal overflow"
        expect(parked).to_be_visible()
        label += f" (ready resize → {width}×{height})"

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
    print(f"PASS [normal motion {label}]: five phases, synchronized quill/ink, gated controls, persistent envelope, complete copy and entry", flush=True)
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
        expect(writ).to_have_attribute("data-state", "ready")
        expect(writ).to_have_attribute("data-ink-progress", "1")
        assert page.locator("p[data-ink]").evaluate_all("els => els.length === 2 && els.every(el => getComputedStyle(el).clipPath === 'none')"), "Reduced motion left unfinished ink"
        assert page.locator(".writing-quill").evaluate("el => getComputedStyle(el).display === 'none' || +getComputedStyle(el).opacity === 0"), "Reduced motion should skip the quill animation"
        expect(page.locator(".envelope-art")).to_be_visible()
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


def map_name_edges(browser, base):
    """The supported twelve-character name must fit the mobile map and heading."""
    for width in (320, 390):
        context = browser.new_context(viewport={"width": width, "height": 844}, reduced_motion="reduce")
        page = context.new_page()
        page.goto(urljoin(base, "start.html"), wait_until="load")
        page.locator("[data-domain-input]").fill("가나다라마바사아자차카타")
        page.goto(urljoin(base, "world.html"), wait_until="load")
        expect(page.locator('.rg-info[data-r="home"] h2')).to_have_text("가나다라마바사아자차카타")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"{width}px: maximum domain name overflows the page"
        geometry = page.locator(".map").evaluate("""map => {
            const home = map.querySelector('[data-domain]');
            const label = home.getBoundingClientRect(), bounds = map.getBoundingClientRect();
            const collisions = [...map.querySelectorAll('.lb')].filter(el => el !== home).filter(el => {
                const other = el.getBoundingClientRect();
                const area = Math.max(0, Math.min(label.right, other.right) - Math.max(label.left, other.left)) *
                    Math.max(0, Math.min(label.bottom, other.bottom) - Math.max(label.top, other.top));
                return area > 1;
            }).map(el => el.textContent);
            return {inside: label.left >= bounds.left && label.right <= bounds.right, collisions};
        }""")
        assert geometry["inside"], f"{width}px: domain label extends outside the map"
        assert not geometry["collisions"], f"{width}px: domain label overlaps {geometry['collisions']}"
        print(f"PASS [map {width}px]: maximum-length name wraps in heading and fits between map labels", flush=True)
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8766/")
    parser.add_argument("--chromium", default=shutil.which("chromium"))
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--entry-only", action="store_true", help="Run only the five-size envelope accessibility checks")
    scope.add_argument("--writing-only", action="store_true", help="Run only staged-writing, resize, and reduced-motion entry checks")
    scope.add_argument("--site-only", action="store_true", help="Run the 18-page feature flows and map edges, skipping detailed entry matrices")
    args = parser.parse_args()
    base = args.base_url.rstrip("/") + "/"
    if not args.entry_only and not args.writing_only:
        check_http(base)
    with sync_playwright() as p:
        options = {"headless": True}
        if args.chromium:
            options["executable_path"] = args.chromium
        browser = p.chromium.launch(**options)
        try:
            if not args.entry_only and not args.writing_only:
                for motion in ("reduce", "no-preference"):
                    check_browser(browser, base, motion=motion)
                    check_browser(browser, base, mobile=True, motion=motion)
            if not args.entry_only and not args.site_only:
                for viewport in MOTION_VIEWPORTS:
                    normal_motion(browser, base, viewport, ready_resize_to=(390, 844) if viewport == (903, 1195) else None)
                normal_motion(browser, base, (903, 1195), resize_to=(390, 844))
                normal_motion(browser, base, (390, 844), resize_to=(844, 390))
            if not args.entry_only and not args.writing_only:
                map_name_edges(browser, base)
            if not args.site_only:
                entry_accessibility(browser, base)
        finally:
            browser.close()
    print("All original-site browser checks passed.", flush=True)


if __name__ == "__main__":
    main()
