#!/usr/bin/env python3
"""Verify real decoded foley playback, its lifecycle, and UI/BGM independence.

The browser audit wraps native Web Audio methods without replacing decoding or
playback. Delayed/failed HTTP responses exercise loading failure paths only.
Run against the range-capable preview: python tests/sfx_smoke.py
"""
import argparse
import re
import shutil
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import expect, sync_playwright

EFFECTS = ("tick", "page", "stamp", "crack", "quill", "chime")
WAV_URL = re.compile(r"\.wav(?:\?|$)")
AUDIT = r"""(() => {
  const Native = window.AudioContext || window.webkitAudioContext;
  const contexts = [], buffers = [], sources = [], decoded = new WeakMap();
  const now = () => performance.now();
  const active = () => sources.filter(s => s.started && !s.ended && s.ctx.currentTime < s.stopAt);
  let peak = 0;
  function bufferInfo(buffer) {
    if (!decoded.has(buffer)) {
      const values = buffer.getChannelData(0);
      let squares = 0, maximum = 0;
      for (let i=0;i<values.length;i++) { squares += values[i]*values[i]; maximum=Math.max(maximum,Math.abs(values[i])); }
      const info = {id:buffers.length, duration:buffer.duration, rate:buffer.sampleRate,
        channels:buffer.numberOfChannels, peak:maximum, rms:Math.sqrt(squares/values.length)};
      decoded.set(buffer,info); buffers.push(info);
    }
    return buffer;
  }
  if (Native) {
    const Wrapped = new Proxy(Native, {construct(target,args) {
      const ctx = Reflect.construct(target,args);
      contexts.push({ctx,at:now()});
      const decode = ctx.decodeAudioData.bind(ctx), create = ctx.createBufferSource.bind(ctx);
      ctx.decodeAudioData = function(data, success, failure) {
        const promise = decode(data, typeof success === 'function' ? b => success(bufferInfo(b)) : undefined, failure);
        return promise.then(bufferInfo);
      };
      ctx.createBufferSource = function() {
        const node = create(), start = node.start.bind(node), stop = node.stop.bind(node);
        const entry = {ctx,started:false,ended:false,stopAt:Infinity,at:0,buffer:null,stops:[]};
        sources.push(entry);
        node.start = function(...args) {
          const result = start(...args);
          entry.started = true; entry.at = now(); entry.buffer = decoded.get(node.buffer) || null;
          peak = Math.max(peak,active().length); return result;
        };
        node.stop = function(...args) {
          const result = stop(...args), when = Number(args[0]);
          entry.stopAt = Math.min(entry.stopAt, Number.isFinite(when) && when > 0 ? when : ctx.currentTime);
          entry.stops.push({at:now(),delay:Math.max(0,entry.stopAt-ctx.currentTime)}); return result;
        };
        node.addEventListener('ended',() => { entry.ended=true; });
        return node;
      };
      return ctx;
    }});
    window.AudioContext = Wrapped;
    if (window.webkitAudioContext) window.webkitAudioContext = Wrapped;
  }
  window.__sfxAudit = {
    snapshot: () => ({contexts:contexts.map(x=>({at:x.at,state:x.ctx.state,time:x.ctx.currentTime})),
      buffers, starts:sources.filter(x=>x.started).map(x=>({at:x.at,buffer:x.buffer,ended:x.ended,stops:x.stops})),
      active:active().length,peak}),
    resetPeak: () => { peak=active().length; }
  };
})();"""


def passed(message):
    print(f"PASS sfx: {message}", flush=True)


def state(page):
    return page.evaluate("ERNSFX.getState()")


def audit(page):
    return page.evaluate("__sfxAudit.snapshot()")


def fresh(browser, mobile=False):
    context = browser.new_context(viewport={"width": 390 if mobile else 1440, "height": 900},
                                  is_mobile=mobile, has_touch=mobile, reduced_motion="no-preference")
    context.add_init_script(AUDIT)
    page = context.new_page()
    page.set_default_timeout(15000)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    return context, page, errors


def open_page(page, base, path="home.html"):
    response = page.goto(urljoin(base, path), wait_until="load")
    assert response and response.ok, path
    page.wait_for_function("!!window.ERNSFX && typeof ERNSFX.getState === 'function'")


def wake(page):
    # A real input event on unused page margin unlocks the context; no fake play.
    page.mouse.click(2, 2)
    page.wait_for_function("ERNSFX.getState().ready")


def quiet(page):
    page.wait_for_function("ERNSFX.getState().active === 0 && __sfxAudit.snapshot().active === 0")


def assert_real_sources(page):
    snapshot = audit(page)
    assert snapshot["starts"], snapshot
    assert all(s["buffer"] and s["buffer"]["duration"] > 0 and s["buffer"]["rms"] > .000001
               for s in snapshot["starts"]), snapshot


def check_first_seal_and_files(browser, base):
    context, page, errors = fresh(browser)
    try:
        open_page(page, base, "index.html")
        config = page.locator("#sfx-data").evaluate("el => JSON.parse(el.textContent)")
        assert set(config["effects"]) == set(EFFECTS), config
        assert all(item["files"] and all(urlsplit(src).path.endswith(".wav") for src in item["files"])
                   for item in config["effects"].values()), config
        page.wait_for_timeout(300)
        assert not audit(page)["contexts"] and not audit(page)["starts"], audit(page)
        assert not state(page)["ready"]
        page.evaluate("document.body.dispatchEvent(new MouseEvent('click',{bubbles:true}))")
        assert not audit(page)["contexts"], "Untrusted script events must not unlock audio"
        page.locator("[data-seal]").click()
        page.wait_for_function("__sfxAudit.snapshot().starts.length > 0")
        snapshot = audit(page)
        # The wax response belongs to the gesture, not the extraction 800ms later.
        assert snapshot["starts"][0]["at"] - snapshot["contexts"][0]["at"] < 350, snapshot
        assert_real_sources(page)
        page.wait_for_function("ERNSFX.getState().ready")
        expect(page.locator("[data-writ]")).to_have_attribute("data-state", "ready", timeout=20000)
        quiet(page)
        for effect in EFFECTS:
            before = len(audit(page)["starts"])
            page.evaluate("name => ERNSFX.play(name,0)", effect)
            page.wait_for_function("n => __sfxAudit.snapshot().starts.length > n", arg=before)
            quiet(page)
        assert_real_sources(page)
        assert not errors, errors
        passed("load creates no AudioContext; first trusted seal and all six effects play real non-silent decoded WAV buffers")
    finally:
        context.close()


def check_late_load(browser, base):
    context, page, errors = fresh(browser)
    pending = []
    page.route(WAV_URL, lambda route: pending.append(route))
    try:
        open_page(page, base)
        page.mouse.click(2, 2)
        page.evaluate("() => { for(let i=0;i<8;i++) for(const name of ['tick','page','stamp','crack','quill','chime']) ERNSFX.play(name,0); }")
        # Long past every contracted event deadline (the longest is 180ms).
        page.wait_for_timeout(450)
        assert not audit(page)["starts"], audit(page)
        assert pending, "The delayed loading fixture did not intercept any real WAV requests"
        while pending:
            route = pending.pop(0)
            response = route.fetch()
            route.fulfill(response=response)
        page.unroute(WAV_URL)
        page.wait_for_function("ERNSFX.getState().ready")
        page.wait_for_timeout(200)
        assert not audit(page)["starts"] and state(page)["pending"] == 0, (audit(page), state(page))
        page.locator('[data-e="tax"]').click()
        page.wait_for_function("__sfxAudit.snapshot().starts.length === 1")
        assert_real_sources(page)
        assert not errors, errors
        passed("cold delayed loading drops expired bursts; only a fresh interaction plays after decoding")
    finally:
        context.close()


def check_mute_and_bgm(browser, base):
    context, page, errors = fresh(browser)
    try:
        open_page(page, base, "music.html")
        wake(page)
        page.locator('[data-music-page] [data-music-toggle]').click()
        page.wait_for_function("ERNMusic.getState().playing && document.querySelector('#ern-music-audio').currentTime > .2")
        page.evaluate("() => { ERNSFX.play('chime',0); window.__quillTimer=setInterval(()=>ERNSFX.play('quill',0),20); }")
        page.wait_for_function("ERNSFX.getState().active > 0")
        music = page.evaluate("({time:ERNMusic.getState().currentTime,volume:document.querySelector('#ern-music-audio').volume})")
        page.locator('.snd').click()
        assert not state(page)["on"] and state(page)["active"] == 0 and state(page)["pending"] == 0, state(page)
        expect(page.locator('.snd')).to_have_attribute('aria-pressed', 'false')
        count = len(audit(page)["starts"])
        page.wait_for_timeout(250)
        assert audit(page)["active"] == 0 and len(audit(page)["starts"]) == count, audit(page)
        page.evaluate("clearInterval(window.__quillTimer)")
        assert page.evaluate("localStorage.getItem('ern-sfx')") == "off"
        assert page.evaluate("t => document.querySelector('#ern-music-audio').currentTime > t", music["time"])
        assert page.evaluate("v => {const a=document.querySelector('#ern-music-audio'); return !a.paused&&!a.muted&&a.volume===v}", music["volume"])
        page.keyboard.press("m")
        assert state(page)["on"] and page.evaluate("localStorage.getItem('ern-sfx')") == "on"
        page.keyboard.press("M")
        assert not state(page)["on"]
        page.reload(wait_until="load")
        page.wait_for_function("!!window.ERNSFX")
        assert not state(page)["on"] and not audit(page)["contexts"], (state(page), audit(page))
        expect(page.locator('.snd')).to_have_attribute('aria-pressed', 'false')
        page.locator('.snd').click()
        page.wait_for_function("ERNSFX.getState().ready")
        assert state(page)["on"]
        assert not errors, errors
        passed("mute stops active/recurring quill immediately, M and preference persist, and real BGM keeps its clock and volume")
    finally:
        context.close()


def check_hover_click_and_voices(browser, base):
    context, page, errors = fresh(browser)
    try:
        open_page(page, base, "characters.html")
        wake(page)
        quiet(page)
        before = len(audit(page)["starts"])
        for code in ("b", "c", "d"):
            page.locator(f'.ro#{code}').hover()
            expect(page.locator(f'.ro#{code}')).to_have_class(re.compile(r'\bon\b'))
        page.locator('.tabs a').first.hover()
        assert len(audit(page)["starts"]) == before, audit(page)
        open_page(page, base, "world.html")
        wake(page)
        quiet(page)
        for code, keyboard in (("seril", False), ("kardun", True)):
            before = len(audit(page)["starts"])
            button = page.locator(f'.rg-list button[data-r="{code}"]')
            if keyboard:
                button.focus()
                page.keyboard.press("Space")
            else:
                button.click()
            page.wait_for_function("n => __sfxAudit.snapshot().starts.length > n", arg=before)
            page.wait_for_timeout(160)
            assert len(audit(page)["starts"]) == before+1, audit(page)
            expect(button).to_have_attribute("aria-current", "true")
            quiet(page)
        page.evaluate("__sfxAudit.resetPeak()")
        page.evaluate("() => { for(let i=0;i<20;i++) for(const name of ['tick','page','stamp','crack','quill','chime']) ERNSFX.play(name,0); }")
        assert 1 <= audit(page)["peak"] <= state(page)["maxVoices"] == 4, (audit(page), state(page))
        quiet(page)
        page.evaluate("() => { __sfxAudit.resetPeak(); window.__quillTimer=setInterval(()=>ERNSFX.play('quill',0),20); }")
        page.wait_for_timeout(650)
        page.evaluate("clearInterval(window.__quillTimer)")
        assert audit(page)["peak"] == 1 and state(page)["voices"]["quill"] <= 1, (audit(page), state(page))
        quiet(page)
        assert not errors, errors
        passed("roster/navigation hover stays silent; pointer and keyboard selections each play once; global/quill voices remain bounded")
    finally:
        context.close()


def check_lifecycle_and_failure(browser, base):
    context, page, errors = fresh(browser)
    try:
        open_page(page, base)
        wake(page)
        page.evaluate("ERNSFX.play('chime',0)")
        page.wait_for_function("ERNSFX.getState().active > 0")
        page.evaluate("""() => {
            Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});
            document.dispatchEvent(new Event('visibilitychange'));
        }""")
        assert state(page)["active"] == 0 and state(page)["pending"] == 0, state(page)
        page.wait_for_timeout(25)
        assert audit(page)["active"] == 0, audit(page)
        before = len(audit(page)["starts"])
        page.evaluate("ERNSFX.play('stamp',0)")
        page.wait_for_timeout(100)
        assert len(audit(page)["starts"]) == before
        page.evaluate("() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); }")
        page.mouse.click(2, 2)
        page.wait_for_function("ERNSFX.getState().ready")
        page.evaluate("ERNSFX.play('page',0)")
        page.wait_for_function("ERNSFX.getState().active > 0")
        page.evaluate("window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))")
        assert state(page)["active"] == 0 and state(page)["pending"] == 0
        page.wait_for_timeout(25)
        assert audit(page)["active"] == 0
        assert not errors, errors
    finally:
        context.close()
    context, page, errors = fresh(browser)
    # This fixture isolates failed audio from core controls. Chromium can emit
    # native cross-document ViewTransition cancellation errors under intercepted
    # network requests; the site's supported reduced-motion path avoids that
    # unrelated animation while retaining strict page-error checks.
    page.emulate_media(reduced_motion="reduce")
    page.route(WAV_URL, lambda route: route.abort("failed"))
    try:
        open_page(page, base, "index.html")
        page.locator('[data-seal]').click()
        expect(page.locator('[data-writ]')).to_have_attribute('data-state', 'ready', timeout=20000)
        page.locator('[data-domain-input]').fill('소리검증')
        page.locator('[data-enter]').click()
        page.wait_for_url('**/home.html')
        expect(page.locator('[data-domain]').first).to_have_text('소리검증')
        before = page.locator('[data-e="tax"]').get_attribute('aria-pressed')
        page.locator('[data-e="tax"]').click()
        expect(page.locator('[data-e="tax"]')).to_have_attribute('aria-pressed', 'false' if before == 'true' else 'true')
        page.locator('[data-g="4"]').click()
        expect(page.locator('[data-g-name]').first).to_have_text('도시')
        assert not audit(page)["starts"] and not errors, (audit(page), errors)
        passed("visibility/pagehide stop voices and pending work; failed WAV fetches leave seal, naming, navigation and controls usable")
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8767/')
    parser.add_argument('--chromium', default=shutil.which('chromium'))
    args = parser.parse_args()
    base = args.base_url.rstrip('/')+'/'
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, **({'executable_path':args.chromium} if args.chromium else {}))
        try:
            for check in (check_first_seal_and_files, check_late_load, check_mute_and_bgm,
                          check_hover_click_and_voices, check_lifecycle_and_failure):
                check(browser, base)
        finally:
            browser.close()


if __name__ == '__main__':
    main()
