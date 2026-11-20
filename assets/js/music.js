/* Shared BGM state for the static pages. Effects and the M shortcut stay independent. */
(() => {
  'use strict';
  if (window.ERNMusic) return;
  const data = document.getElementById('music-data');
  if (!data) return;
  let config;
  try { config = JSON.parse(data.textContent); } catch { return; }
  const tracks = Object.freeze((Array.isArray(config.tracks) ? config.tracks : [])
    .filter(track => track && typeof track.id === 'string' && typeof track.src === 'string' && track.src)
    .map(track => Object.freeze({
      id: track.id, title: String(track.title || track.id), src: track.src,
      cover: typeof track.cover === 'string' ? track.cover : null,
      duration: Number.isFinite(Number(track.duration)) ? Math.max(0, Number(track.duration)) : 0,
    })));
  const STATE_KEY = 'ern-music-state', OWNER_KEY = 'ern-music-owner';
  const LEASE_MS = 12000, HEARTBEAT_MS = 2500;
  const tabId = typeof crypto.randomUUID === 'function' ? crypto.randomUUID() : Date.now() + '-' + Math.random();
  const finite = (value, fallback = 0) => Number.isFinite(Number(value)) ? Number(value) : fallback;
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const read = key => { try { return JSON.parse(localStorage.getItem(key)); } catch { return null; } };
  const write = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch {} };
  const saved = read(STATE_KEY);
  let index = Math.max(0, tracks.findIndex(track => saved && track.id === saved.trackId));
  let intent = saved && ['play', 'pause'].includes(saved.intent) ? saved.intent : 'never';
  let pendingSeek = Math.max(0, finite(saved && saved.currentTime));
  let status = intent === 'never' ? 'idle' : 'paused', reason = null, error = null;
  let operation = 0, destroyed = false, suspended = false, owned = false;
  let lease = null, heartbeat = 0, lastSave = 0;
  let stateWritable = true, stateRevision = finite(saved && saved.updated);
  let mediaTrack = null;
  const listeners = new Set(), cleanup = [];
  const audio = document.createElement('audio');
  audio.id = 'ern-music-audio'; audio.dataset.ernMusic = ''; audio.hidden = true;
  audio.preload = 'none'; audio.volume = clamp(saved ? finite(saved.volume, .4) : .4, 0, 1);
  audio.setAttribute('aria-hidden', 'true');
  document.body.appendChild(audio);
  let channel = null;
  try { channel = new BroadcastChannel('ern-music'); } catch {}

  const track = () => tracks[index] || null;
  const sourceMatches = () => !!track() && audio.currentSrc === new URL(track().src, document.baseURI).href;
  const duration = () => sourceMatches() && Number.isFinite(audio.duration) ? audio.duration : (track() ? track().duration : 0);
  const position = () => pendingSeek !== null ? pendingSeek : (sourceMatches() ? finite(audio.currentTime) : 0);
  function getState() {
    const current = track();
    return Object.freeze({
      track: current, trackId: current ? current.id : null, index,
      title: current ? current.title : '', src: current ? current.src : null, cover: current ? current.cover : null,
      currentTime: position(), duration: duration(), volume: audio.volume, status,
      playing: status === 'playing' && !audio.paused && !audio.ended,
      wantsPlay: intent === 'play', loading: status === 'loading', blocked: status === 'blocked',
      error, reason, available: tracks.length > 0,
    });
  }
  function emit() {
    if (destroyed) return;
    const state = getState();
    updateMediaSession(state);
    window.dispatchEvent(new CustomEvent('ern:music-change', { detail: state }));
    listeners.forEach(listener => { try { listener(state); } catch (err) { console.error(err); } });
  }
  function persist(force = false) {
    if (destroyed || reason === 'other-tab' || !track()) return;
    const now = Date.now();
    if (!force && now - lastSave < 2000) return;
    const latest = read(STATE_KEY);
    if (otherOwner() || (!owned && latest && finite(latest.updated) > stateRevision)) stateWritable = false;
    if (!stateWritable) return;
    lastSave = now;
    stateRevision = Math.max(now, finite(latest && latest.updated) + 1);
    write(STATE_KEY, { version: 1, trackId: track().id, currentTime: position(), volume: audio.volume, intent, updated: stateRevision });
  }
  const validLease = value => value && typeof value.tabId === 'string' && typeof value.token === 'string'
    && Number.isFinite(value.claimed) && Number.isFinite(value.expires) && value.expires > Date.now();
  const newer = (a, b) => !b || a.claimed > b.claimed || (a.claimed === b.claimed && a.token > b.token);
  function otherOwner() {
    const stored = read(OWNER_KEY);
    if (validLease(stored) && (!validLease(lease) || newer(stored, lease) || stored.token === lease.token)) lease = stored;
    return validLease(lease) && lease.tabId !== tabId;
  }
  function announce(value) { if (channel) { try { channel.postMessage(value); } catch {} } }
  function stopHeartbeat() { clearInterval(heartbeat); heartbeat = 0; }
  function release() {
    stopHeartbeat();
    if (!owned) return;
    owned = false;
    const old = lease, stored = read(OWNER_KEY);
    if (old && stored && stored.token === old.token) { try { localStorage.removeItem(OWNER_KEY); } catch {} }
    if (old) announce({ type: 'release', token: old.token });
    lease = null;
  }
  function yieldTo(nextLease) {
    if (destroyed || suspended || !validLease(nextLease) || nextLease.tabId === tabId) return;
    if (validLease(lease) && !newer(nextLease, lease) && nextLease.token !== lease.token) return;
    lease = nextLease;
    stateWritable = false;
    if (!owned && (intent !== 'play' || status === 'paused')) return;
    owned = false; stopHeartbeat(); operation++;
    audio.pause(); status = 'paused'; reason = 'other-tab'; error = null; emit();
    // Do not save a pause here: the new owner is carrying the user's play intent.
  }
  function claim() {
    // BroadcastChannel handles live tabs immediately; the expiring storage
    // lease also covers navigation, unavailable channels, and crashed tabs.
    const stored = read(OWNER_KEY);
    const claimed = Math.max(Date.now(), finite(lease && lease.claimed) + 1, finite(stored && stored.claimed) + 1);
    lease = { tabId, token: tabId + ':' + claimed, claimed, expires: Date.now() + LEASE_MS };
    owned = true; stateWritable = true; write(OWNER_KEY, lease); announce({ type: 'claim', lease });
    stopHeartbeat();
    heartbeat = setInterval(() => {
      if (!owned || suspended || destroyed) return;
      const current = read(OWNER_KEY);
      if (validLease(current) && current.tabId !== tabId && newer(current, lease)) { yieldTo(current); return; }
      lease.expires = Date.now() + LEASE_MS;
      write(OWNER_KEY, lease); announce({ type: 'claim', lease });
    }, HEARTBEAT_MS);
  }
  function on(target, type, listener, options) {
    target.addEventListener(type, listener, options);
    cleanup.push(() => target.removeEventListener(type, listener, options));
  }
  function applySeek() {
    if (pendingSeek === null || !sourceMatches() || audio.readyState < 1) return;
    const end = duration();
    const value = end > 0 ? clamp(pendingSeek, 0, end) : Math.max(0, pendingSeek);
    // Metadata can arrive before an MP3 has a seekable range. Assigning then
    // silently clamps to zero in some browsers, losing a restored position.
    if (value > 0 && !Array.from({ length: audio.seekable.length }, (_, n) =>
      value >= audio.seekable.start(n) && value <= audio.seekable.end(n) + .05).some(Boolean)) return;
    try { audio.currentTime = value; pendingSeek = null; } catch { /* Retry when metadata becomes seekable. */ }
  }
  function ensureSource(reload = false) {
    if (!track()) return;
    const expected = new URL(track().src, document.baseURI).href;
    if (audio.src !== expected || reload) {
      audio.src = track().src;
      if (audio.preload !== 'none' || reload) audio.load();
    }
    applySeek();
  }
  function fail(err, token) {
    if (destroyed || suspended || token !== operation) return false;
    audio.pause(); release();
    if (err && err.name === 'NotAllowedError') { status = 'blocked'; reason = 'autoplay'; error = null; }
    else { status = 'error'; reason = 'media'; error = '음악을 재생하지 못했습니다. 다시 시도해 주세요.'; }
    persist(true); emit(); return false;
  }
  async function attemptPlay(explicit = true) {
    if (destroyed || suspended || !track()) return false;
    const token = ++operation;
    intent = 'play';
    if (!explicit && otherOwner()) {
      audio.pause(); status = 'paused'; reason = 'other-tab'; error = null; emit(); return false;
    }
    const reload = !!audio.error;
    reason = null; error = null; status = 'loading'; audio.preload = 'metadata';
    ensureSource(reload); claim(); persist(true); emit();
    try {
      await audio.play();
      if (destroyed || suspended || token !== operation) return false;
      if (!audio.paused) { status = 'playing'; emit(); return true; }
      return false;
    } catch (err) { return fail(err, token); }
  }
  function select(value, options = {}) {
    const selected = typeof value === 'number' && Number.isInteger(value) ? value : tracks.findIndex(item => item.id === value);
    if (destroyed || selected < 0 || selected >= tracks.length) return Promise.resolve(false);
    operation++; audio.pause();
    if (index !== selected) { index = selected; pendingSeek = 0; }
    status = 'paused'; reason = null; error = null;
    audio.preload = 'metadata'; ensureSource();
    if (options.play !== false) return attemptPlay(true);
    intent = 'pause'; release(); persist(true); emit(); return Promise.resolve(true);
  }
  function play(value) { return value === undefined ? attemptPlay(true) : select(value); }
  function pause() {
    if (destroyed) return;
    operation++; intent = 'pause'; audio.pause(); release();
    status = 'paused'; reason = null; error = null; persist(true); emit();
  }
  function toggle() {
    if (intent === 'play' && (status === 'playing' || status === 'loading')) { pause(); return Promise.resolve(false); }
    return play();
  }
  function next() { return tracks.length ? select((index + 1) % tracks.length) : Promise.resolve(false); }
  function previous() { return tracks.length ? select((index + tracks.length - 1) % tracks.length) : Promise.resolve(false); }
  function seek(value) {
    if (destroyed || !track() || !Number.isFinite(Number(value))) return;
    const end = duration(); pendingSeek = clamp(Number(value), 0, end > 0 ? end : Number.MAX_SAFE_INTEGER);
    audio.preload = 'metadata'; ensureSource(); applySeek(); persist(true); emit();
  }
  function setVolume(value) {
    if (destroyed || !Number.isFinite(Number(value))) return;
    audio.volume = clamp(Number(value), 0, 1); persist(true); emit();
  }
  function restore() {
    const latest = read(STATE_KEY);
    if (latest) {
      const selected = tracks.findIndex(item => item.id === latest.trackId);
      if (selected >= 0) index = selected;
      pendingSeek = Math.max(0, finite(latest.currentTime));
      audio.volume = clamp(finite(latest.volume, .4), 0, 1);
      intent = ['play', 'pause'].includes(latest.intent) ? latest.intent : 'never';
      stateRevision = finite(latest.updated);
    }
    stateWritable = !otherOwner();
    status = intent === 'never' ? 'idle' : 'paused'; reason = null; error = null;
    ensureSource(); emit();
    if (intent === 'play') attemptPlay(false);
  }
  function suspend() {
    if (suspended || destroyed) return;
    persist(true); suspended = true; operation++; audio.pause(); release();
  }
  function destroy() {
    if (destroyed) return;
    suspend(); destroyed = true;
    cleanup.forEach(remove => remove()); listeners.clear();
    if (channel) channel.close();
    if ('mediaSession' in navigator) {
      mediaActions.forEach(action => { try { navigator.mediaSession.setActionHandler(action, null); } catch {} });
      navigator.mediaSession.metadata = null; navigator.mediaSession.playbackState = 'none';
      try { navigator.mediaSession.setPositionState(); } catch {}
    }
    audio.removeAttribute('src'); audio.load(); audio.remove();
  }

  function updateMediaSession(state) {
    if (!('mediaSession' in navigator)) return;
    try {
      if (state.trackId !== mediaTrack && typeof MediaMetadata === 'function') {
        const artwork = [];
        if (state.cover) {
          const url = new URL(state.cover, document.baseURI);
          const suffix = url.pathname.split('.').pop().toLowerCase();
          const type = { webp: 'image/webp', png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', avif: 'image/avif' }[suffix];
          if (type) artwork.push({ src: url.href, type });
        }
        navigator.mediaSession.metadata = new MediaMetadata({ title: state.title, artwork });
        mediaTrack = state.trackId;
      }
      navigator.mediaSession.playbackState = state.playing ? 'playing' : (state.wantsPlay || intent === 'pause' ? 'paused' : 'none');
      if (state.duration > 0) navigator.mediaSession.setPositionState({
        duration: state.duration, playbackRate: 1, position: clamp(state.currentTime, 0, state.duration),
      });
    } catch { /* Media Session support differs across browsers. */ }
  }
  const mediaActions = ['play', 'pause', 'previoustrack', 'nexttrack', 'seekto', 'seekbackward', 'seekforward'];
  if ('mediaSession' in navigator) {
    const handlers = { play: () => play(), pause, previoustrack: previous, nexttrack: next,
      seekto: event => seek(event.seekTime),
      seekbackward: event => seek(position() - (event.seekOffset || 10)),
      seekforward: event => seek(position() + (event.seekOffset || 10)),
    };
    mediaActions.forEach(action => { try { navigator.mediaSession.setActionHandler(action, handlers[action]); } catch {} });
  }

  on(audio, 'loadedmetadata', () => { applySeek(); emit(); });
  on(audio, 'durationchange', () => { applySeek(); emit(); });
  on(audio, 'canplay', applySeek);
  on(audio, 'progress', applySeek);
  on(audio, 'timeupdate', () => { if (!suspended) { persist(); emit(); } });
  on(audio, 'seeked', () => { persist(true); emit(); });
  on(audio, 'volumechange', emit);
  on(audio, 'playing', () => {
    if (destroyed || suspended || intent !== 'play' || !owned) { audio.pause(); return; }
    status = 'playing'; reason = null; error = null; emit();
  });
  on(audio, 'waiting', () => { if (!suspended && intent === 'play' && !audio.paused && owned) { status = 'loading'; emit(); } });
  on(audio, 'pause', () => {
    if (destroyed || suspended || !audio.paused || audio.ended) return;
    if (status === 'playing') { status = 'paused'; persist(true); emit(); }
  });
  on(audio, 'ended', () => { if (!suspended && intent === 'play' && owned) next(); });
  on(audio, 'error', () => { if (!suspended && audio.error && sourceMatches()) fail(audio.error, operation); });
  on(window, 'pagehide', suspend);
  on(window, 'pageshow', event => { if (event.persisted && !destroyed) { suspended = false; restore(); } });
  on(document, 'visibilitychange', () => {
    persist(true);
    if (!document.hidden && owned) {
      const current = read(OWNER_KEY);
      if (validLease(current) && current.tabId !== tabId && newer(current, lease)) yieldTo(current);
    }
  });
  on(window, 'storage', event => { if (event.key === OWNER_KEY && event.newValue) { try { yieldTo(JSON.parse(event.newValue)); } catch {} } });
  if (channel) on(channel, 'message', event => {
    const message = event.data;
    if (!message) return;
    if (message.type === 'claim') yieldTo(message.lease);
    else if (message.type === 'release' && lease && lease.token === message.token && !owned) lease = null;
  });

  // Only the first deliberate seal opening opts a new listener in. A saved pause
  // wins over the seal. Other gestures can recover an already-requested autoplay.
  const gestures = new WeakMap();
  function captureGesture(event) {
    gestures.set(event, operation);
    if (!event.isTrusted || event.isComposing || intent !== 'never') return;
    if (event.type === 'keydown' && event.key !== ' ') return;
    const seal = event.target.closest && event.target.closest('[data-seal]');
    if (!seal || (event.type === 'keydown' && (event.ctrlKey || event.altKey || event.metaKey))) return;
    const writ = seal.closest('[data-writ]');
    if (writ && writ.dataset.state && writ.dataset.state !== 'sealed') return;
    const first = tracks.findIndex(item => item.id === 'break-ground');
    select(first >= 0 ? first : 0);
  }
  function resumeGesture(event) {
    if (!event.isTrusted || event.isComposing || gestures.get(event) !== operation || status !== 'blocked' || intent !== 'play') return;
    if (event.type === 'keydown' && !['Enter', ' '].includes(event.key)) return;
    if (event.ctrlKey || event.altKey || event.metaKey || (event.target.closest && event.target.closest('[data-music-ui], input, textarea, select, [contenteditable]'))) return;
    attemptPlay(false);
  }
  ['click', 'keydown'].forEach(type => { on(document, type, captureGesture, true); on(document, type, resumeGesture); });

  window.ERNMusic = Object.freeze({
    tracks, getState, play, pause, toggle, select, next, previous, prev: previous, seek, setVolume,
    subscribe(listener) {
      if (typeof listener !== 'function' || destroyed) return () => {};
      listeners.add(listener); listener(getState()); return () => listeners.delete(listener);
    },
    destroy,
  });
  stateWritable = !otherOwner();
  ensureSource();
  window.dispatchEvent(new CustomEvent('ern:music-ready', { detail: getState() }));
  emit();
  if (intent === 'play') attemptPlay(false);
})();
