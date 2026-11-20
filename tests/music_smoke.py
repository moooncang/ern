#!/usr/bin/env python3
"""Exercise real MP3 playback and the music UI, independently of sound effects.

Requires Playwright/Chromium and a server supporting HTTP byte ranges (as the
deployed static host does). For example:
    python tests/music_smoke.py --base-url http://127.0.0.1:8767/

Media time and native ended events are checked; audio.play is never mocked as a
successful playback. One explicit rejection tests the browser-permission path.
"""
import argparse
from pathlib import Path
import shutil
import time
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from playwright.sync_api import expect, sync_playwright

TRACK_IDS = ("break-ground", "night-watch-on-the-wall", "village-fields-at-dawn")
AUDIO = "#ern-music-audio"
PAGE = "[data-music-page]"


def passed(message):
    print(f"PASS music: {message}", flush=True)


def frames(page):
    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")


def state(page):
    return page.evaluate("ERNMusic.getState()")


def open_page(page, base, path="music.html"):
    response = page.goto(urljoin(base, path), wait_until="load")
    assert response and response.ok, path
    page.wait_for_function("!!window.ERNMusic && document.querySelector('.music-dock')")
    expect(page.locator(AUDIO)).to_have_count(1)


def wait_playing(page, track_id=None):
    page.wait_for_function("""id => {
        const s = ERNMusic.getState(), a = document.querySelector('#ern-music-audio');
        return s.playing && !a.paused && a.readyState >= 2 && Number.isFinite(a.duration)
            && a.duration > 30 && (!id || s.trackId === id);
    }""", arg=track_id, timeout=15000)


def time_advances(page):
    before = page.locator(AUDIO).evaluate("a => a.currentTime")
    page.wait_for_function("t => document.querySelector('#ern-music-audio').currentTime > t + .3", arg=before)


def paused_stays_paused(page):
    assert page.locator(AUDIO).evaluate("a => a.paused")
    before = page.locator(AUDIO).evaluate("a => a.currentTime")
    page.wait_for_timeout(350)
    after = page.locator(AUDIO).evaluate("a => a.currentTime")
    assert abs(after - before) < .05 and not state(page)["wantsPlay"], (before, after, state(page))


def no_overflow(page, label):
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), label


def attach_errors(page):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    return errors


def check_transport(base):
    for track_id in TRACK_IDS:
        url = urljoin(base, f"audio/music/{track_id}.mp3")
        request = Request(url, headers={"Range": "bytes=0-1023"})
        with urlopen(request, timeout=20) as response:
            assert response.status == 206 and response.headers.get("Content-Range", "").startswith("bytes 0-1023/"), (
                f"Real MP3 seek/restore requires a byte-range server: {url} returned "
                f"{response.status}, Content-Range={response.headers.get('Content-Range')!r}. "
                "Use the range-capable preview server; Python SimpleHTTP alone is insufficient."
            )
            assert len(response.read()) == 1024
    passed("all three supplied MP3 files serve valid HTTP byte ranges")


def check_playback(browser, base):
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
    page = context.new_page()
    page.set_default_timeout(15000)
    errors = attach_errors(page)
    try:
        open_page(page, base)
        assert page.evaluate("ERNMusic.tracks.map(t => t.id)") == list(TRACK_IDS)
        expect(page.locator(f"{PAGE} [data-music-track]")).to_have_count(3)
        assert state(page)["status"] == "idle" and page.locator(AUDIO).evaluate("a => a.paused")
        page.locator(f"{PAGE} [data-music-toggle]").click()
        wait_playing(page, TRACK_IDS[0])
        time_advances(page)
        passed("user gesture starts decoded MP3 audio and real playback time advances")

        volume = page.locator(AUDIO).evaluate("a => a.volume")
        before = page.locator(".snd").get_attribute("aria-pressed")
        page.locator(".snd").click()
        expect(page.locator(".snd")).to_have_attribute("aria-pressed", "false" if before == "true" else "true")
        time_advances(page)
        page.keyboard.press("m")
        expect(page.locator(".snd")).to_have_attribute("aria-pressed", before)
        assert page.locator(AUDIO).evaluate("a => a.volume") == volume
        assert not page.locator(AUDIO).evaluate("a => a.muted")
        passed("effect mute and M remain independent of BGM playback/volume")

        page.locator(f'{PAGE} [data-music-track="{TRACK_IDS[1]}"]').click()
        wait_playing(page, TRACK_IDS[1])
        page.locator(f"{PAGE} [data-music-volume]").fill("23")
        page.locator(f"{PAGE} [data-music-seek]").fill("250")
        target = state(page)["duration"] * .25
        page.wait_for_function("t => Math.abs(document.querySelector('#ern-music-audio').currentTime - t) < 2", arg=target)
        assert abs(state(page)["volume"] - .23) < .001
        page.locator(f"{PAGE} [data-music-toggle]").click()
        expect(page.locator(".music-dock [data-music-toggle]")).to_have_attribute("aria-label", "재생")
        saved = state(page)
        paused_stays_paused(page)
        page.reload(wait_until="load")
        page.wait_for_function("!!window.ERNMusic")
        restored = state(page)
        assert restored["trackId"] == saved["trackId"] and abs(restored["volume"] - .23) < .001
        assert abs(restored["currentTime"] - saved["currentTime"]) < 1
        paused_stays_paused(page)
        passed("track, native seek position and volume survive reload while explicit pause stays paused")

        open_page(page, base, "char/h.html")
        assert state(page)["trackId"] == TRACK_IDS[1] and not state(page)["wantsPlay"]
        assert page.locator(".music-dock-link").get_attribute("href") == "../music.html"
        expected_src = urljoin(base, f"audio/music/{TRACK_IDS[1]}.mp3")
        assert page.locator(AUDIO).evaluate("a => a.src") == expected_src
        page.locator(".music-dock [data-music-toggle]").click()
        wait_playing(page, TRACK_IDS[1])
        assert page.locator(AUDIO).evaluate("a => a.currentTime") >= saved["currentTime"] - 1
        time_advances(page)
        page.locator(".music-dock-link").click()
        page.wait_for_url("**/music.html")
        page.wait_for_function("ERNMusic.getState().status !== 'loading'")
        if not state(page)["playing"]:
            # A new document may require a fresh gesture under browser policy.
            page.locator(f"{PAGE} [data-music-toggle]").click()
        wait_playing(page, TRACK_IDS[1])
        assert page.locator(AUDIO).evaluate("a => a.currentTime") >= saved["currentTime"] - 1
        passed("subdirectory audio/link URLs and position restoration across real page navigation")

        page.evaluate("""() => {
            ERNMusic.select(0, {play:true});
            ERNMusic.select(1, {play:true});
            ERNMusic.select(2, {play:true});
        }""")
        wait_playing(page, TRACK_IDS[2])
        time_advances(page)
        expect(page.locator(AUDIO)).to_have_count(1)
        assert page.locator(AUDIO).evaluate("a => a.currentSrc").endswith(f"/{TRACK_IDS[2]}.mp3")
        page.evaluate("ERNMusic.seek(document.querySelector('#ern-music-audio').duration - .35)")
        wait_playing(page, TRACK_IDS[0])
        time_advances(page)
        passed("rapid track changes keep one current audio; real file ending advances and wraps the playlist")

        page.evaluate("window.dispatchEvent(new PageTransitionEvent('pagehide', {persisted:true}))")
        assert page.locator(AUDIO).evaluate("a => a.paused")
        page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted:true}))")
        wait_playing(page, TRACK_IDS[0])
        page.evaluate("ERNMusic.pause()")
        assert not errors, errors
    finally:
        context.close()


def check_rejection_and_pending_seek(browser, base):
    context = browser.new_context(viewport={"width": 1000, "height": 900}, reduced_motion="reduce")
    context.add_init_script("""(() => {
        const play = HTMLMediaElement.prototype.play;
        HTMLMediaElement.prototype.play = function(...args) {
            if (this.id === 'ern-music-audio' && !window.__musicDeniedOnce) {
                window.__musicDeniedOnce = true;
                return Promise.reject(new DOMException('Deliberate permission test', 'NotAllowedError'));
            }
            return play.apply(this, args);
        };
    })();""")
    page = context.new_page()
    errors = attach_errors(page)
    try:
        open_page(page, base)
        # Before the first media load, seeking must remain pending until usable metadata/ranges exist.
        page.evaluate("ERNMusic.seek(19)")
        page.locator(f"{PAGE} [data-music-toggle]").click()
        page.wait_for_function("ERNMusic.getState().blocked")
        denied = state(page)
        assert denied["reason"] == "autoplay" and not denied["playing"]
        expect(page.locator(f"{PAGE} [data-music-status]")).to_contain_text("재생 버튼")
        expect(page.locator(f"{PAGE} [data-music-toggle]")).to_have_attribute("aria-label", "재생")
        page.locator(f"{PAGE} [data-music-toggle]").click()
        wait_playing(page)
        page.wait_for_function("document.querySelector('#ern-music-audio').currentTime >= 18")
        time_advances(page)
        assert not errors, errors
        passed("permission rejection is visible/retryable and a pre-metadata seek is applied on real playback")
    finally:
        context.close()


def check_cross_tab_and_cover(browser, base):
    context = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
    first = context.new_page()
    second = None
    try:
        open_page(first, base, "index.html")
        first.locator("[data-seal]").click()
        wait_playing(first, TRACK_IDS[0])
        time_advances(first)
        second = context.new_page()
        open_page(second, base)
        second.wait_for_function("ERNMusic.getState().reason === 'other-tab'")
        assert second.locator(AUDIO).evaluate("a => a.paused")
        second.locator(f"{PAGE} [data-music-toggle]").click()
        wait_playing(second)
        first.wait_for_function("ERNMusic.getState().reason === 'other-tab'")
        assert first.locator(AUDIO).evaluate("a => a.paused")
        expect(first.locator(".music-dock [data-music-toggle]")).to_have_attribute("aria-label", "배경 음악 재생")
        time_advances(second)
        second.evaluate("ERNMusic.pause()")
        second.close()
        second = None
        open_page(first, base, "index.html")
        first.locator("[data-seal]").click()
        paused_stays_paused(first)
        first.evaluate("ERNMusic.destroy()")
        expect(first.locator(AUDIO)).to_have_count(0)
        first.locator(".music-dock [data-music-toggle]").click()
        expect(first.locator(AUDIO)).to_have_count(0)
        passed("first seal opts in once, explicit cross-tab Play takes ownership, saved pause and destroy are respected")
    finally:
        context.close()


def check_stale_tab_navigation(browser, base):
    # A paused document can retain older state even after another tab takes
    # ownership. Its pagehide must never overwrite the newer track or intent.
    for newer_intent in ("play", "pause"):
        context = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        first = context.new_page()
        first.add_init_script("window.__musicStorageAtBoot = JSON.parse(localStorage.getItem('ern-music-state'))")
        second = context.new_page()
        try:
            open_page(first, base, "home.html")
            first.evaluate("() => { ERNMusic.pause(); ERNMusic.seek(12); }")
            assert state(first)["trackId"] == TRACK_IDS[0] and not state(first)["wantsPlay"]
            open_page(second, base)
            second.locator(f'{PAGE} [data-music-track="{TRACK_IDS[1]}"]').click()
            wait_playing(second, TRACK_IDS[1])
            second.evaluate("() => { ERNMusic.seek(78); ERNMusic.setVolume(.23); }")
            second.wait_for_function("Math.abs(document.querySelector('#ern-music-audio').currentTime - 78) < 2")
            if newer_intent == "pause":
                second.evaluate("ERNMusic.pause()")
            open_page(first, base, "start.html")
            # Capture at document initialization, before a later owner heartbeat
            # could repair a bad pagehide write and conceal the regression.
            snapshot = first.evaluate("window.__musicStorageAtBoot")
            assert snapshot["trackId"] == TRACK_IDS[1], snapshot
            assert abs(snapshot["currentTime"] - 78) < 3 and abs(snapshot["volume"] - .23) < .001, snapshot
            assert snapshot["intent"] == newer_intent, snapshot
            restored = state(first)
            assert restored["trackId"] == TRACK_IDS[1] and abs(restored["volume"] - .23) < .001, restored
            if newer_intent == "play":
                assert restored["reason"] == "other-tab" and first.locator(AUDIO).evaluate("a => a.paused"), restored
                wait_playing(second, TRACK_IDS[1])
            else:
                paused_stays_paused(first)
        finally:
            context.close()
    passed("stale paused-tab navigation preserves the newer owner's track, seek, volume and both play/pause intent")


def check_original_covers(browser, base):
    context = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
    page = context.new_page()
    errors = attach_errors(page)

    def check_cover(track_id, prefix, music_page):
        current = state(page)
        relative = f"{prefix}images/music/{track_id}.jpg"
        absolute = urljoin(base, f"images/music/{track_id}.jpg")
        assert current["cover"] == relative, current
        page.wait_for_function("""src => [...document.querySelectorAll('[data-music-cover]')].every(img =>
            !img.hidden && img.src === src && img.complete && img.naturalWidth === 1920 && img.naturalHeight === 1080)
        """, arg=absolute)
        expect(page.locator(".music-dock [data-music-cover]")).to_have_attribute("alt", "")
        if music_page:
            expect(page.locator(f"{PAGE} [data-music-cover]")).to_have_attribute("alt", current["title"] + " 표지")
            thumbnail = page.locator(f'{PAGE} [data-music-track="{track_id}"] img')
            assert thumbnail.evaluate("img => img.src") == absolute
            expect(thumbnail).to_have_attribute("alt", "")
        metadata = page.evaluate("""() => ({title:navigator.mediaSession.metadata.title,
            artwork:[...navigator.mediaSession.metadata.artwork].map(a => ({src:a.src, type:a.type}))})""")
        assert metadata == {"title": current["title"], "artwork": [{"src": absolute, "type": "image/jpeg"}]}, metadata

    try:
        open_page(page, base)
        for track_id in TRACK_IDS:
            page.locator(f'{PAGE} [data-music-track="{track_id}"]').click()
            wait_playing(page, track_id)
            check_cover(track_id, "", True)
        page.evaluate("ERNMusic.pause()")
        open_page(page, base, "char/h.html")
        for track_id in TRACK_IDS:
            page.locator(".music-dock [data-music-next]").click()
            wait_playing(page, track_id)
            check_cover(track_id, "../", False)
        assert not errors, errors
        passed("all three original 1920×1080 covers, meaningful/decorative alt text and Media Session artwork follow track selection, including char subpaths")
    finally:
        context.close()


def check_layout_and_keys(browser, base, width, screenshots):
    context = browser.new_context(viewport={"width": width, "height": 844 if width < 721 else 1000},
                                  is_mobile=width < 721, has_touch=width < 721, reduced_motion="reduce")
    page = context.new_page()
    errors = attach_errors(page)
    try:
        for path in ("music.html", "home.html", "char/h.html", "start.html"):
            open_page(page, base, path)
            no_overflow(page, f"{width}px {path}")
            page.evaluate("scrollTo({top:document.documentElement.scrollHeight, behavior:'instant'})")
            frames(page)
            boxes = page.evaluate("""() => {
                const dock = document.querySelector('.music-dock').getBoundingClientRect();
                const links = [...document.querySelectorAll('.foot nav a')].map(a => a.getBoundingClientRect());
                return {dockTop:dock.top, dockBottom:dock.bottom, footerBottom:Math.max(...links.map(r=>r.bottom)),
                        reserved:parseFloat(getComputedStyle(document.body).paddingBottom), height:dock.height};
            }""")
            assert boxes["footerBottom"] <= boxes["dockTop"] - 1, (width, path, boxes)
            assert boxes["dockBottom"] <= page.viewport_size["height"] + 1, (width, path, boxes)
            assert boxes["reserved"] >= boxes["height"], (width, path, boxes)
        open_page(page, base)
        last = page.locator(f"{PAGE} [data-music-track]").last
        last.focus()
        frames(page)
        rect, dock = last.bounding_box(), page.locator(".music-dock").bounding_box()
        assert rect["y"] + rect["height"] <= dock["y"] + 1, (width, rect, dock)
        page.keyboard.press("Enter")
        wait_playing(page, TRACK_IDS[2])
        toggle = page.locator(f"{PAGE} [data-music-toggle]")
        toggle.focus()
        page.keyboard.press("Space")
        paused_stays_paused(page)
        volume = page.locator(f"{PAGE} [data-music-volume]")
        volume.focus()
        old = float(volume.input_value())
        page.keyboard.press("ArrowRight")
        assert abs(state(page)["volume"] - (old + 1) / 100) < .001
        page.keyboard.press("5")
        assert urlsplit(page.url).path.endswith("/music.html"), "typing/slider focus must not trigger menu navigation"
        summary = page.locator(".music-dock-volume summary")
        summary.click()
        expect(page.locator(".music-dock-volume")).to_have_attribute("open", "")
        panel = page.locator(".music-dock-volume label").bounding_box()
        assert panel["x"] >= -1 and panel["x"] + panel["width"] <= width + 1 and panel["y"] >= 0
        page.keyboard.press("Escape")
        expect(summary).to_be_focused()
        assert not page.locator(".music-dock-volume").evaluate("e => e.open")
        open_page(page, base, "char/h.html")
        page.keyboard.press("5")
        page.wait_for_url("**/music.html")
        if screenshots:
            page.screenshot(path=str(screenshots / f"music-{width}.png"), full_page=True)
        assert not errors, errors
        passed(f"{width}px player/footer clearance, track keyboard selection, native range keys, volume dismissal and fifth menu shortcut")
    finally:
        context.close()


def check_native_fallback(browser, base, width):
    context = browser.new_context(viewport={"width": width, "height": 844}, java_script_enabled=False)
    page = context.new_page()
    try:
        response = page.goto(urljoin(base, "music.html"), wait_until="load")
        assert response and response.ok
        native = page.locator(".music-fallback audio[controls]")
        expect(native).to_have_count(3)
        assert native.evaluate_all("els => els.every(a => a.controls && a.getAttribute('src').endsWith('.mp3'))")
        for item in native.all():
            expect(item).to_be_visible()
        no_overflow(page, f"{width}px no-JS music fallback")
        first = native.first
        first.scroll_into_view_if_needed()
        rect = first.bounding_box()
        page.mouse.click(rect["x"] + 25, rect["y"] + rect["height"] / 2)
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if first.evaluate("a => !a.paused && a.currentTime > .2"):
                break
            time.sleep(.1)
        else:
            raise AssertionError("Native controls did not start real MP3 playback with JavaScript disabled")
        passed(f"{width}px no-JS fallback provides three visible native audio controls and plays an MP3")
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8767/")
    parser.add_argument("--chromium", default=shutil.which("chromium"))
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--width", type=int, action="append", choices=(320, 390, 768, 1440))
    parser.add_argument("--layout-only", action="store_true")
    args = parser.parse_args()
    base = args.base_url.rstrip("/") + "/"
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    if not args.layout_only:
        check_transport(base)
    with sync_playwright() as p:
        options = {"headless": True}
        if args.chromium:
            options["executable_path"] = args.chromium
        browser = p.chromium.launch(**options)
        try:
            if not args.layout_only:
                check_playback(browser, base)
                check_rejection_and_pending_seek(browser, base)
                check_cross_tab_and_cover(browser, base)
                check_stale_tab_navigation(browser, base)
                check_original_covers(browser, base)
            for width in args.width or (1440, 390, 320):
                check_layout_and_keys(browser, base, width, args.screenshots)
            if not args.layout_only:
                for width in (1440, 320):
                    check_native_fallback(browser, base, width)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
