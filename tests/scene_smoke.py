#!/usr/bin/env python3
"""Check scroll scenes without letting presentation change user choices.

Requires optional Playwright Python and Chromium plus a running static server.
Run: python3 tests/scene_smoke.py --base-url http://127.0.0.1:8766/
Use --width 390 --page world.html or --fallback-only for a focused follow-up.
"""
import argparse
import json
import re
import shutil
from urllib.parse import urljoin

from playwright.sync_api import expect, sync_playwright

from original_smoke import assert_no_overflow

PAGES = ("home.html", "world.html", "domain.html", "start.html", "characters.html", "char/a.html")


def frames(page):
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")


def sweep(page, label):
    """Use ordinary page scrolling; keep keyboard focus and choices untouched."""
    page.mouse.move(0, 0)
    for fraction in (0, .25, .5, .75, 1, .5, 0):
        page.evaluate("fraction => scrollTo({top: (document.documentElement.scrollHeight - innerHeight) * fraction, behavior: 'instant'})", fraction)
        frames(page)
        assert_no_overflow(page, label)


def choose(page, path):
    """Make an explicit choice, including keyboard activation, before scrolling."""
    if path == "home.html":
        slider = page.locator("[data-g-range]")
        slider.fill("3")
        slider.focus()
        page.keyboard.press("ArrowRight")
        expect(slider).to_have_value("4")
        page.locator('[data-e="tax"]').click()
        page.locator('.seasons [data-season="winter"]').focus()
        page.keyboard.press("Enter")
        expect(page.locator("html")).to_have_attribute("data-season", "winter")
        expect(page.locator('.season-observation [data-specimen].is-active')).to_have_attribute("data-specimen", "winter")
    elif path == "world.html":
        page.locator('.map .rg[data-r="kardun"]').focus()
        page.keyboard.press("Enter")
        expect(page.locator('.rg-info[data-r="kardun"]')).to_be_visible()
    elif path == "domain.html":
        page.locator('[data-tally] tbody tr').first.locator('[data-d="1"]').click()
        expect(page.locator('[data-total]')).to_have_text("1동화")
    elif path == "start.html":
        page.locator('.slot[data-m="free"]').focus()
        page.keyboard.press("Enter")
        page.locator('[data-n="출신"]').fill("기사")
        expect(page.locator('[data-note-out]')).to_contain_text("[시작 모드] 자유모드")
    elif path == "characters.html":
        page.locator('.sel-f button').nth(2).focus()
        page.keyboard.press("Space")
        character = page.locator('.roster > li:visible .ro').nth(1)
        character.focus()
        expect(page.locator('[data-f="이름"]')).to_have_text("두르간")
        expect(page.locator('[data-sel-img]')).to_have_attribute('src', json.loads(character.get_attribute('data-c'))['img'])
    else:
        button = page.locator('.face-tabs button').nth(2)
        source = button.get_attribute('data-src')
        button.focus()
        page.keyboard.press("Enter")
        expect(page.locator('[data-face]')).to_have_attribute('src', source)


def selection(page):
    return page.evaluate("""() => ({
        growth: document.querySelector('[data-g-range]')?.value,
        season: document.documentElement.dataset.season,
        edicts: [...document.querySelectorAll('[data-e][aria-pressed="true"]')].map(el => el.dataset.e),
        region: document.querySelector('.rg-list [aria-current="true"]')?.dataset.r,
        mode: document.querySelector('.slot[aria-selected="true"]')?.dataset.m,
        note: document.querySelector('[data-note-out]')?.textContent,
        filter: document.querySelector('.sel-f [aria-selected="true"]')?.dataset.f,
        character: document.querySelector('.ro.on')?.getAttribute('href'),
        expression: document.querySelector('[data-face]')?.getAttribute('src'),
        total: document.querySelector('[data-total]')?.textContent,
        quantities: [...document.querySelectorAll('[data-tally] tbody output')].map(el => el.textContent),
        focus: document.activeElement && {
            tag: document.activeElement.tagName,
            id: document.activeElement.id,
            href: document.activeElement.getAttribute('href'),
            data: {...document.activeElement.dataset},
            name: document.activeElement.getAttribute('name')
        },
        hash: location.hash
    })""")


def change_selection(page, path):
    """Start another real transition before the live motion-preference test."""
    if path == 'home.html':
        page.locator('[data-g="2"]').click()
    elif path == 'world.html':
        page.locator('.rg-list button[data-r="seril"]').click()
    elif path == 'domain.html':
        page.locator('[data-tally] tbody tr').first.locator('[data-d="1"]').click()
    elif path == 'start.html':
        page.locator('.slot[data-m="gyeseung"]').click()
    elif path == 'characters.html':
        character = page.locator('.roster > li:visible .ro').first
        character.focus()
        expect(page.locator('[data-f="이름"]')).to_have_text('시아렐')
        expect(page.locator('[data-sel-img]')).to_have_attribute('src', json.loads(character.get_attribute('data-c'))['img'])
    else:
        button = page.locator('.face-tabs button').nth(1)
        source = button.get_attribute('data-src')
        button.click()
        expect(page.locator('[data-face]')).to_have_attribute('src', source)


def assert_sticky_fits(page, label):
    oversized = page.locator('main *').evaluate_all("""els => els.flatMap(el => {
        const style = getComputedStyle(el), box = el.getBoundingClientRect();
        if (style.position !== 'sticky' || !box.height || !box.width) return [];
        const top = Number.parseFloat(style.top) || 0;
        return box.height + top > innerHeight + 1 ? [{class: el.className, height: box.height, top}] : [];
    })""")
    assert not oversized, f"{label}: sticky panel cannot fit its viewport: {oversized}"


def check_stationary_roster(page):
    """Scrolling beneath a stationary mouse must not replace the chosen person."""
    rows = page.locator('.roster .ro')
    first, second = rows.nth(0), rows.nth(1)
    first.hover()
    selected = page.locator('.ro.on').get_attribute('href')
    a, b = first.bounding_box(), second.bounding_box()
    pointer = {'x': a['x'] + a['width'] / 2, 'y': a['y'] + a['height'] / 2}
    page.evaluate("step => scrollBy({top: step, behavior: 'instant'})", b['y'] - a['y'])
    frames(page)
    beneath = page.evaluate("p => document.elementFromPoint(p.x, p.y)?.closest('.ro')?.getAttribute('href')", pointer)
    assert beneath and beneath != selected, 'Roster scroll test did not place another row under the stationary pointer'
    assert page.locator('.ro.on').get_attribute('href') == selected, 'Scrolling under a stationary mouse changed the selected character'
    page.mouse.move(pointer['x'] + 1, pointer['y'])
    expect(page.locator('.ro.on')).to_have_attribute('href', beneath)


def check_portrait_sizes(page):
    """A tall portrait scrolls normally; its name must remain reachable."""
    page.mouse.move(0, 0)
    for width, height in ((1440, 600), (1920, 900), (1440, 1000)):
        page.set_viewport_size({'width': width, 'height': height})
        frames(page)
        assert_sticky_fits(page, f'portrait {width}×{height}')
        plate = page.locator('.sel-stage .plate')
        plate.evaluate('el => el.scrollIntoView({block: "center", behavior: "instant"})')
        frames(page)
        box = plate.bounding_box()
        header = page.locator('.top').evaluate('el => el.offsetHeight')
        assert box['y'] >= header - 1 and box['y'] + box['height'] <= height + 1, \
            f'portrait {width}×{height}: name plate is obscured or trapped below the viewport: {box}'
        assert_no_overflow(page, f'portrait {width}×{height}')


def check_scenes(browser, base, width, pages=PAGES):
    context = browser.new_context(viewport={'width': width, 'height': 1000 if width > 720 else 844},
                                  reduced_motion='no-preference', is_mobile=width <= 720, has_touch=width <= 720)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    try:
        for path in pages:
            label = f'{width}px {path}'
            page.goto(urljoin(base, path), wait_until='load')
            page.evaluate('document.fonts.ready')
            expect(page.locator('body')).to_have_class(re.compile(r'.*\bscenes-ready\b.*'))
            scenes = page.locator('main > section.scene')
            assert scenes.count() == page.locator('main > section').count() > 0, label
            if path == 'characters.html' and width > 720:
                check_stationary_roster(page)
            choose(page, path)
            before = selection(page)
            sweep(page, label)
            assert selection(page) == before, f'{label}: scrolling changed selection, input, focus, or URL'
            assert_sticky_fits(page, label)

            # A reader can reach every chapter; progress is finite and bounded.
            # The first chapter's progress must respond to scrolling, without
            # requiring a particular easing curve or pixel implementation.
            progress = []
            positions = []
            first = scenes.first
            for align in ('end', 'start'):
                first.evaluate('(el, block) => el.scrollIntoView({block, behavior: "instant"})', align)
                frames(page)
                progress.append(float(first.evaluate('el => getComputedStyle(el).getPropertyValue("--scene-progress")')))
                positions.append(page.evaluate('scrollY'))
            if abs(positions[1] - positions[0]) > 10:
                assert (progress[1] - progress[0]) * (positions[1] - positions[0]) > 0, \
                    f'{label}: chapter progress {progress} does not follow scroll positions {positions}'
            for index in range(scenes.count()):
                scene = scenes.nth(index)
                scene.evaluate('el => el.scrollIntoView({block: "center", behavior: "instant"})')
                expect(scene).to_have_class(re.compile(r'.*\bscene-in\b.*'))
                page.wait_for_function("""index => [...document.querySelectorAll('main > section.scene')[index].querySelectorAll('h1,h2,h3,p')].every(el => {
                    const box = el.getBoundingClientRect();
                    if (!el.textContent.trim() || !box.width || box.bottom <= 0 || box.top >= innerHeight) return true;
                    let opacity = 1;
                    for (let node = el; node; node = node.parentElement) {
                        const style = getComputedStyle(node);
                        if (style.display === 'none' || style.visibility === 'hidden') return true;
                        opacity *= +style.opacity;
                    }
                    return opacity >= .1;
                })""", arg=index)
                value = scene.evaluate('el => Number(getComputedStyle(el).getPropertyValue("--scene-progress"))')
                assert 0 <= value <= 1, f'{label}: invalid chapter progress {value}'
            assert_no_overflow(page, label)

            # Switch the operating-system preference while a real selection
            # transition is pending, then confirm all movement stops and the
            # chosen state remains intact.
            change_selection(page, path)
            before = selection(page)
            page.emulate_media(reduced_motion='reduce')
            expect(page.locator('body')).to_have_class(re.compile(r'.*\bscenes-still\b.*'))
            page.wait_for_function("document.getAnimations().every(animation => animation.playState !== 'running')")
            still_progress = scenes.evaluate_all('els => els.map(el => getComputedStyle(el).getPropertyValue("--scene-progress"))')
            sweep(page, label + ' reduced')
            assert selection(page) == before, f'{label}: reduced-motion switch changed user state'
            assert scenes.evaluate_all('els => els.map(el => getComputedStyle(el).getPropertyValue("--scene-progress"))') == still_progress, \
                f'{label}: reduced-motion scrolling still drives scene movement'
            assert_sticky_fits(page, label + ' reduced')
            page.emulate_media(reduced_motion='no-preference')
            page.wait_for_function("!document.body.classList.contains('scenes-still')")
            assert selection(page) == before, f'{label}: restoring motion changed user state'
            if path == 'characters.html' and width > 720:
                check_portrait_sizes(page)
            print(f'PASS [scenes {label}]: scroll, explicit choices, focus, motion changes, sticky bounds', flush=True)
        assert not errors, f'{width}px: JavaScript errors: {errors}'
    finally:
        context.close()


def check_fallback(browser, base, width, javascript, pages=PAGES):
    mode = 'scene scripts unavailable' if javascript else 'JavaScript disabled'
    context = browser.new_context(viewport={'width': width, 'height': 1000 if width > 720 else 844},
                                  reduced_motion='reduce', java_script_enabled=javascript)
    if javascript:
        context.route(re.compile(r'/assets/js/scenes[^/]*\.js(?:\?|$)'), lambda route: route.abort())
    page = context.new_page()
    try:
        for path in pages:
            page.goto(urljoin(base, path), wait_until='load')
            page.evaluate('document.fonts.ready')
            assert not page.locator('body').evaluate("el => el.classList.contains('scenes-ready')")
            assert page.locator('main').inner_text().strip(), f'{path}: fallback has no content'
            for section in page.locator('main > section').all():
                section.evaluate('el => el.scrollIntoView({block: "center", behavior: "instant"})')
                # Disabled-script contexts do not execute scheduled RAF callbacks.
                # The computed-style read below flushes their static layout.
                if javascript:
                    frames(page)
                invisible = section.locator('h1,h2,h3,p').evaluate_all("""els => els.flatMap(el => {
                    if (!el.textContent.trim()) return [];
                    let opacity = 1;
                    for (let node = el; node; node = node.parentElement) {
                        const style = getComputedStyle(node);
                        if (style.display === 'none' || style.visibility === 'hidden') return [];
                        opacity *= +style.opacity;
                    }
                    return opacity < .1 ? [el.textContent.trim().slice(0, 80)] : [];
                })""")
                assert not invisible, f'{width}px {path} {mode}: hidden fallback copy: {invisible}'
                assert_no_overflow(page, f'{width}px {path} {mode}')
            assert page.locator('.tabs a[href$="world.html"]').get_attribute('href').endswith('world.html')
        print(f'PASS [fallback {width}px]: {len(pages)} representative pages readable with {mode}', flush=True)
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8766/')
    parser.add_argument('--chromium', default=shutil.which('chromium'))
    parser.add_argument('--width', type=int, action='append', choices=(320, 390, 1440))
    parser.add_argument('--page', action='append', choices=PAGES)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--fallback-only', action='store_true')
    mode.add_argument('--scenes-only', action='store_true')
    args = parser.parse_args()
    with sync_playwright() as p:
        options = {'headless': True}
        if args.chromium:
            options['executable_path'] = args.chromium
        browser = p.chromium.launch(**options)
        try:
            base = args.base_url.rstrip('/') + '/'
            widths = args.width or (1440, 390, 320)
            pages = args.page or PAGES
            if not args.fallback_only:
                for width in widths:
                    check_scenes(browser, base, width, pages)
            if not args.scenes_only:
                for width in widths:
                    for javascript in (False, True):
                        check_fallback(browser, base, width, javascript, pages)
        finally:
            browser.close()


if __name__ == '__main__':
    main()
