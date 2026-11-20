/* Short recorded foley. Its context and setting never control the music player. */
(() => {
  'use strict';
  if (window.ERNSFX) return;
  const doc = document, node = doc.getElementById('sfx-data');
  let config = {};
  try { config = node ? JSON.parse(node.textContent).effects || {} : {}; } catch {}
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  const names = ['tick', 'page', 'stamp', 'crack', 'quill', 'chime'];
  const ttl = { tick: 65, page: 120, stamp: 140, crack: 180, quill: 70, chime: 120 };
  const limits = { tick: 1, page: 1, stamp: 2, crack: 1, quill: 1, chime: 1 };
  const lengths = { tick: .12, page: .55, stamp: .4, crack: .4, quill: .16, chime: .5 };
  const minimums = { tick: 90, page: 110, stamp: 100, crack: 250, quill: 220, chime: 180 };
  const maxVoices = 4, masterLevel = .72, muteTime = .008;
  const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
  const number = (value, fallback) => Number.isFinite(Number(value)) ? Number(value) : fallback;
  const effects = new Map(names.filter(name => config[name] && Array.isArray(config[name].files)).map(name => [name, {
    files: [...new Set(config[name].files.filter(file => typeof file === 'string' && file))],
    gain: clamp(number(config[name].gain, .5), 0, 1),
    minGap: Math.max(minimums[name], number(config[name].minGap, minimums[name])),
    lastStart: -Infinity, lastFile: null,
  }]));
  let on = true;
  try { on = localStorage.getItem('ern-sfx') !== 'off'; } catch {}
  let ctx = null, master = null, destroyed = false, away = false, generation = 0;
  let suspendTimer = 0, lastGesture = null, gestureTime = -Infinity;
  let clickEvent = null, clickHasSound = false;
  const cache = new Map(), voices = new Set(), pending = new Map(), cleanup = [];
  const controller = new AbortController();

  function listen(target, type, listener, options) {
    target.addEventListener(type, listener, options);
    cleanup.push(() => target.removeEventListener(type, listener, options));
  }
  function paint() { doc.querySelectorAll('.snd').forEach(button => button.setAttribute('aria-pressed', String(on))); }
  function getState() {
    const counts = Object.fromEntries(names.map(name => [name, [...voices].filter(voice => voice.name === name).length]));
    return {
      on, ready: !!ctx && ctx.state === 'running' && effects.size > 0
        && [...effects.values()].every(effect => effect.files.some(file => cache.get(file)?.buffer)),
      contextState: ctx ? ctx.state : 'none', active: voices.size, pending: pending.size,
      loaded: [...cache.values()].filter(item => item.buffer).length,
      failed: [...cache.values()].filter(item => item.failed).length, voices: counts, maxVoices,
    };
  }
  function fetchFile(file) {
    if (cache.has(file)) return cache.get(file);
    const item = { bytes: null, buffer: null, failed: false, decoding: null, promise: null };
    cache.set(file, item);
    item.promise = fetch(file, { signal: controller.signal }).then(response => {
      if (!response.ok) throw new Error('Sound unavailable');
      return response.arrayBuffer();
    }).then(bytes => { item.bytes = bytes; return bytes; }).catch(() => { item.failed = true; return null; });
    return item;
  }
  function warm() {
    if (!on || destroyed) return;
    // Start the small seal transient first, then cache the rest without creating
    // an AudioContext or making any sound before a trusted gesture.
    ['crack', ...names.filter(name => name !== 'crack')].forEach(name => {
      const effect = effects.get(name);
      if (effect) effect.files.forEach(fetchFile);
    });
  }
  function decode(file) {
    if (!ctx || destroyed) return;
    const item = fetchFile(file);
    if (item.buffer || item.decoding || item.failed) return;
    const context = ctx;
    item.decoding = item.promise.then(bytes => bytes && !destroyed ? context.decodeAudioData(bytes.slice(0)) : null)
      .then(buffer => {
        if (destroyed || !buffer) return;
        item.buffer = buffer;
        flush();
      }).catch(() => { item.failed = true; });
  }
  function decodeAll() {
    ['crack', ...names.filter(name => name !== 'crack')].forEach(name => {
      const effect = effects.get(name);
      if (effect) effect.files.forEach(decode);
    });
  }
  function wake(event) {
    if (destroyed || !on || away || doc.hidden || !AudioContext || !event?.isTrusted) return;
    clearTimeout(suspendTimer);
    if (!ctx) {
      try {
        ctx = new AudioContext({ latencyHint: 'interactive' });
        master = ctx.createGain(); master.gain.value = 0; master.connect(ctx.destination);
      } catch {
        if (ctx) ctx.close().catch(() => {});
        ctx = null; master = null; return;
      }
    }
    const token = generation;
    warm(); decodeAll();
    try {
      const resumed = ctx.state === 'running' ? Promise.resolve() : ctx.resume();
      Promise.resolve(resumed).then(() => {
        if (destroyed || token !== generation || !on || away || doc.hidden || ctx.state !== 'running') return;
        master.gain.cancelScheduledValues(ctx.currentTime);
        master.gain.setValueAtTime(master.gain.value, ctx.currentTime);
        master.gain.linearRampToValueAtTime(masterLevel, ctx.currentTime + muteTime);
        flush();
      }).catch(() => {});
    } catch { /* A later trusted gesture can retry a suspended context. */ }
  }
  function drop(name) {
    const request = pending.get(name);
    if (request) clearTimeout(request.timer);
    pending.delete(name);
  }
  function stopAll(suspend = true) {
    generation++;
    [...pending.keys()].forEach(drop);
    clearTimeout(suspendTimer);
    if (!ctx) return;
    const now = ctx.currentTime;
    master.gain.cancelScheduledValues(now);
    master.gain.setValueAtTime(master.gain.value, now);
    master.gain.linearRampToValueAtTime(0, now + muteTime);
    // A hidden/interrupted context may freeze its clock before a fade ends.
    // Stop those sources now so returning to the page cannot revive a tail.
    const stopAt = doc.hidden || away || ctx.state !== 'running' ? now : now + muteTime;
    voices.forEach(voice => { try { voice.source.stop(stopAt); } catch {} });
    voices.clear();
    if (suspend) {
      const token = generation;
      suspendTimer = setTimeout(() => {
        if (destroyed || token !== generation || !ctx || ctx.state !== 'running') return;
        ctx.suspend().catch(() => {});
      }, 12);
    }
  }
  function start(request) {
    const effect = effects.get(request.name), now = performance.now();
    if (!effect || destroyed || !on || away || doc.hidden || request.generation !== generation || now > request.deadline) return false;
    if (!ctx || ctx.state !== 'running') return false;
    if (now - effect.lastStart < request.gap) { drop(request.name); return false; }
    const available = effect.files.filter(file => cache.get(file)?.buffer);
    if (!available.length) return false;
    if (voices.size >= maxVoices || [...voices].filter(voice => voice.name === request.name).length >= limits[request.name]) {
      drop(request.name); return false;
    }
    const choices = available.length > 1 ? available.filter(file => file !== effect.lastFile) : available;
    const file = choices[Math.floor(Math.random() * choices.length)], buffer = cache.get(file).buffer;
    const source = ctx.createBufferSource(), gain = ctx.createGain();
    const jitter = request.name === 'quill' ? .035 : .018;
    const rate = 1 + (Math.random() * 2 - 1) * jitter;
    const seconds = Math.min(buffer.duration, lengths[request.name]);
    const at = ctx.currentTime, end = at + seconds / rate;
    const fade = Math.min(request.name === 'quill' ? .018 : .012, seconds / 3);
    const level = effect.gain * Math.pow(10, ((Math.random() * 2 - 1) * .65) / 20);
    source.buffer = buffer; source.playbackRate.value = rate;
    gain.gain.setValueAtTime(0, at);
    gain.gain.linearRampToValueAtTime(level, at + Math.min(.003, seconds / 4));
    gain.gain.setValueAtTime(level, Math.max(at + .003, end - fade));
    gain.gain.linearRampToValueAtTime(0, end);
    source.connect(gain); gain.connect(master);
    const voice = { source, gain, name: request.name };
    source.onended = () => { voices.delete(voice); source.disconnect(); gain.disconnect(); };
    try {
      source.start(at, 0, seconds); voices.add(voice);
      effect.lastStart = now; effect.lastFile = file; drop(request.name); return true;
    } catch { source.disconnect(); gain.disconnect(); drop(request.name); return false; }
  }
  function flush() {
    [...pending.values()].forEach(request => {
      if (request.generation !== generation || performance.now() > request.deadline) drop(request.name);
      else start(request);
    });
  }
  function play(name, gap) {
    if (clickEvent && clickEvent.eventPhase) clickHasSound = true;
    const effect = effects.get(name);
    if (!effect || !on || destroyed || away || doc.hidden || !ctx) return false;
    const now = performance.now(), interval = Math.max(effect.minGap, number(gap, effect.minGap));
    if (now - effect.lastStart < interval) return false;
    drop(name);
    const request = { name, gap: interval, generation, deadline: now + ttl[name], timer: 0 };
    if (start(request)) return true;
    // At capacity, drop rather than queue sounds behind other voices.
    if (voices.size >= maxVoices || [...voices].filter(voice => voice.name === name).length >= limits[name]) return false;
    request.timer = setTimeout(() => { if (pending.get(name) === request) drop(name); }, ttl[name] + 1);
    pending.set(name, request);
    effect.files.forEach(decode);
    return false;
  }
  function toggle(event) {
    if (destroyed) return;
    on = !on;
    try { localStorage.setItem('ern-sfx', on ? 'on' : 'off'); } catch {}
    paint();
    if (!on) { stopAll(); return; }
    // A deliberate re-enable can retry failed downloads; failures never block UI.
    [...cache.entries()].forEach(([file, item]) => { if (item.failed) cache.delete(file); });
    warm();
    const gesture = event?.isTrusted ? event : performance.now() - gestureTime < 150 ? lastGesture : null;
    wake(gesture); play('stamp');
  }
  function capture(event) {
    if (event.type === 'click') { clickEvent = event; clickHasSound = false; }
    if (!event.isTrusted || event.isComposing) return;
    lastGesture = event; gestureTime = performance.now(); wake(event);
  }
  ['pointerdown', 'keydown', 'click'].forEach(type => listen(doc, type, capture, { capture: true, passive: true }));
  listen(doc, 'click', event => {
    const button = event.target.closest && event.target.closest('.snd');
    if (button) { event.stopPropagation(); toggle(event); return; }
    if (clickHasSound || event.target.closest?.('[data-music-ui]')) return;
    const target = event.target.closest?.('.tabs a, .foot a, .brand, .btn, .deed, .tilt, .fg, .ro, .rep, .prof-nav a, .fief');
    if (target && !target.matches('[data-enter], [data-copy]')) play('page');
  });
  listen(doc, 'visibilitychange', () => { if (doc.hidden) stopAll(); });
  listen(window, 'pagehide', () => { away = true; stopAll(); });
  listen(window, 'pageshow', () => {
    away = false;
    // A cached document may have missed another page's preference change.
    try { on = localStorage.getItem('ern-sfx') !== 'off'; } catch {}
    paint();
    if (!on) stopAll(); else warm();
  });
  listen(window, 'storage', event => {
    if (event.key !== 'ern-sfx') return;
    on = event.newValue !== 'off'; paint();
    if (!on) stopAll(); else warm();
  });
  function destroy() {
    if (destroyed) return;
    stopAll(false); destroyed = true; clearTimeout(suspendTimer);
    cleanup.forEach(remove => remove()); controller.abort();
    if (ctx) ctx.close().catch(() => {});
  }
  window.ERNSFX = Object.freeze({ play, toggle, getState, destroy });
  paint(); warm();
})();
