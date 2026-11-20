#!/usr/bin/env python3
"""Check complete gallery cards and unobstructed controls at every breakpoint.

Requires optional Playwright Python and Chromium plus a running static server.
Run: python3 tests/gallery_smoke.py --base-url http://127.0.0.1:8766/
"""
import argparse
from pathlib import Path
import shutil
from urllib.parse import urljoin

from playwright.sync_api import expect, sync_playwright

from original_smoke import assert_no_overflow


def check_geometry(page, label):
    controls = page.locator('.deck-tools')
    controls.evaluate('el => el.scrollIntoView({block: "center", behavior: "instant"})')
    result = controls.evaluate("""tools => {
        const scrollBottom = Math.max(...[...document.querySelectorAll('.deck, .deck-thumbs')].map(el => el.getBoundingClientRect().bottom));
        return [...tools.children].map(el => {
            const box = el.getBoundingClientRect(), style = getComputedStyle(el);
            const ring = el.matches(':focus-visible') ? parseFloat(style.outlineWidth) + Math.max(0, parseFloat(style.outlineOffset)) : 0;
            const hits = [.15, .5, .85].flatMap(x => [.1, .5, .9].map(y => {
                const hit = document.elementFromPoint(box.left + box.width * x, box.top + box.height * y);
                return hit === el || el.contains(hit);
            }));
            return {tag: el.tagName, text: el.textContent, hits,
                clear: box.top - ring >= scrollBottom - .5,
                fits: box.left - ring >= -1 && box.right + ring <= innerWidth + 1 &&
                    box.top - ring >= 0 && box.bottom + ring <= innerHeight,
                focus: el.matches(':focus-visible'), ring};
        });
    }""")
    assert all(item['clear'] for item in result), f'{label}: scrollbar/scroller overlaps controls or their focus ring: {result}'
    assert all(item['fits'] for item in result), f'{label}: controls extend beyond the viewport: {result}'
    assert all(all(item['hits']) for item in result), f'{label}: a control or its number is covered: {result}'
    assert_no_overflow(page, label)


def check_gallery(browser, base, width, motion, screenshots=None):
    label = f'{width}px {motion}'
    context = browser.new_context(viewport={'width': width, 'height': 1000 if width > 720 else 844},
                                  reduced_motion=motion, is_mobile=width <= 720, has_touch=width <= 720)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    try:
        page.goto(urljoin(base, 'home.html'), wait_until='load')
        page.evaluate('document.fonts.ready')
        deck = page.locator('.deck')
        cards = deck.locator('.tilt')
        previous = page.get_by_role('button', name='이전 인물 카드', exact=True)
        following = page.get_by_role('button', name='다음 인물 카드', exact=True)
        counter = page.locator('.deck-count')
        thumbnails = page.locator('.deck-thumb')
        expect(cards).to_have_count(12)
        expect(thumbnails).to_have_count(12)
        assert thumbnails.evaluate_all('els => els.map(el => el.getAttribute("aria-label"))') == cards.locator('img').evaluate_all('els => els.map(el => el.alt)'), 'Thumbnail names must reuse the original image descriptions'

        def inspect(index, vertical_position=None):
            expect(counter).to_have_text(f'{index + 1:02d} / 12')
            expect(page.locator('.deck-thumb[aria-pressed="true"]')).to_have_count(1)
            expect(thumbnails.nth(index)).to_have_attribute('aria-pressed', 'true')
            page.wait_for_function("""index => {
                const deck = document.querySelector('.deck'), card = deck.querySelectorAll('.tilt')[index];
                return Math.abs(card.getBoundingClientRect().left - deck.getBoundingClientRect().left - parseFloat(getComputedStyle(deck).paddingLeft)) < 1.5;
            }""", arg=index)
            image = cards.nth(index).locator('img')
            image.evaluate('el => el.decode()')
            image_geometry = image.evaluate("""image => {
                const card = image.closest('.tilt').getBoundingClientRect(), deck = image.closest('.deck').getBoundingClientRect();
                return {ratio: image.offsetWidth / image.offsetHeight, natural: image.naturalWidth / image.naturalHeight,
                    inside: card.left >= deck.left - 1 && card.right <= deck.right + 1 && card.top >= deck.top - 1 && card.bottom <= deck.bottom + 1};
            }""")
            assert abs(image_geometry['ratio'] - image_geometry['natural']) < .01, f'{label}: original card image is cropped or stretched'
            assert image_geometry['inside'], f'{label}: selected card is clipped by its scrolling viewport'
            if vertical_position is not None:
                assert abs(page.evaluate('scrollY') - vertical_position) < 1.5, f'{label}: thumbnail selection moved the page vertically'
            check_geometry(page, f'{label} card {index + 1}')
            if screenshots and index in (0, 11):
                page.locator('.scene-household').screenshot(path=str(screenshots / f'gallery-{width}-{motion}-{index + 1:02d}.png'))

        deck.evaluate('el => el.scrollIntoView({block: "center", behavior: "instant"})')
        inspect(0)
        expect(previous).to_be_disabled()
        following.click()
        inspect(1)
        cards.nth(5).evaluate("""card => {
            const deck = card.closest('.deck');
            deck.scrollTo({left: deck.scrollLeft + card.getBoundingClientRect().left - deck.getBoundingClientRect().left - parseFloat(getComputedStyle(deck).paddingLeft), behavior: 'instant'});
        }""")
        inspect(5)
        deck.focus()
        page.keyboard.press('ArrowRight')
        inspect(6)
        following.focus()
        assert following.evaluate("el => el.matches(':focus-visible')"), 'Keyboard focus indicator was not activated'
        check_geometry(page, f'{label} focused next button')
        page.keyboard.press('Enter')
        inspect(7)
        deck.evaluate("el => el.scrollTo({left: el.scrollWidth, behavior: 'instant'})")
        inspect(11)
        expect(following).to_be_disabled()
        previous.focus()
        check_geometry(page, f'{label} focused previous button')
        previous.click()
        inspect(10)
        following.click()
        inspect(11)
        strip = page.locator('.deck-thumbs')
        for index in (0, 5, 11):
            strip.evaluate('el => el.scrollIntoView({block: "center", behavior: "instant"})')
            thumbnails.nth(index).evaluate("""button => {
                const strip = button.closest('.deck-thumbs');
                strip.scrollBy({left: button.getBoundingClientRect().left - strip.getBoundingClientRect().left - parseFloat(getComputedStyle(strip).paddingLeft), behavior: 'instant'});
            }""")
            y = page.evaluate('scrollY')
            thumbnails.nth(index).tap() if width <= 720 else thumbnails.nth(index).click()
            inspect(index, y)
        for key, index in (('Home', 0), ('ArrowRight', 1), ('End', 11), ('ArrowLeft', 10)):
            y = page.evaluate('scrollY')
            page.keyboard.press(key)
            expect(thumbnails.nth(index)).to_be_focused()
            inspect(index, y)
            focus = thumbnails.nth(index).evaluate("""button => {
                const box = button.getBoundingClientRect(), strip = button.closest('.deck-thumbs'), clip = strip.getBoundingClientRect();
                const style = getComputedStyle(button), ring = parseFloat(style.outlineWidth) + Math.max(0, parseFloat(style.outlineOffset));
                return {visible: button.matches(':focus-visible'), fits: box.left - ring >= clip.left && box.right + ring <= clip.right &&
                    box.top - ring >= clip.top && box.bottom + ring <= clip.top + strip.clientHeight};
            }""")
            assert focus['visible'] and focus['fits'], f'{label}: thumbnail focus is clipped: {focus}'
        if motion == 'no-preference':
            y = page.evaluate('scrollY')
            page.keyboard.press('Home')
            page.emulate_media(reduced_motion='reduce')
            inspect(0, y)
            page.emulate_media(reduced_motion='no-preference')
            page.wait_for_function("!document.body.classList.contains('scenes-still')")
            y = page.evaluate('scrollY')
            page.keyboard.press('End')
            inspect(11, y)
        assert not errors, f'{label}: JavaScript errors: {errors}'
        print(f'PASS gallery {label}: complete cards, controls, thumbnail selection/focus, no vertical jump, 01/06/12 boundaries', flush=True)
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8766/')
    parser.add_argument('--chromium', default=shutil.which('chromium'))
    parser.add_argument('--screenshots', type=Path)
    args = parser.parse_args()
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        # Keep native scrollbars visible: their track exposed the original overlap.
        options = {'headless': True, 'ignore_default_args': ['--hide-scrollbars']}
        if args.chromium:
            options['executable_path'] = args.chromium
        browser = p.chromium.launch(**options)
        try:
            for width in (320, 390, 768, 1440):
                for motion in ('reduce', 'no-preference'):
                    check_gallery(browser, args.base_url.rstrip('/') + '/', width, motion, args.screenshots)
        finally:
            browser.close()


if __name__ == '__main__':
    main()
