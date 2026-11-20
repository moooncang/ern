/* One presentation layer for the music page and the compact player.
   ERNMusic owns audio, playback intent, persistence, and media-session state. */
(() => {
  'use strict';
  const doc = document;
  const $ = (selector, root = doc) => root.querySelector(selector);
  const $$ = (selector, root = doc) => [...root.querySelectorAll(selector)];
  let config = {};
  try { config = JSON.parse($('#music-data')?.textContent || '{}'); } catch (_) { /* Optional fallback data. */ }
  const entry = doc.body.classList.contains('cover');
  const page = $('[data-music-page]');
  if (page) page.setAttribute('data-music-ui', '');
  const pageUrl = config.pageUrl || (location.pathname.includes('/char/') ? '../music.html' : 'music.html');
  const symbols = {
    play: '<path d="m9 5 11 7-11 7Z"/>',
    pause: '<path d="M8 5v14M16 5v14"/>',
    prev: '<path d="M6 5v14m13-14L9 12l10 7Z"/>',
    next: '<path d="M18 5v14M5 5l10 7-10 7Z"/>',
    volume: '<path d="m11 5-5 4H3v6h3l5 4Zm4 3a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14"/>',
    music: '<path d="M9 18V5l11-2v13M9 8l11-2"/><ellipse cx="6" cy="18" rx="3" ry="2.5"/><ellipse cx="17" cy="16" rx="3" ry="2.5"/>'
  };
  const icon = name => `<svg class="music-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">${symbols[name]}</svg>`;
  const toggle = '<button type="button" data-music-toggle aria-label="재생">' + icon('play') + '<span class="music-toggle-label">재생</span></button>';
  const dock = doc.createElement('aside');
  dock.className = 'music-dock' + (entry ? ' music-dock--entry' : '');
  dock.setAttribute('data-music-ui', '');
  dock.setAttribute('aria-label', '배경 음악');
  if (entry) dock.innerHTML = toggle;
  else {
    dock.innerHTML = '<img class="music-dock-art" data-music-cover alt="" hidden>' +
      '<div class="music-dock-meta"><span class="music-dock-caption">SOUNDTRACK</span><span data-music-title>Break Ground</span></div>' +
      '<div class="music-dock-controls"><button type="button" data-music-prev aria-label="이전 곡">' + icon('prev') + '</button>' + toggle + '<button type="button" data-music-next aria-label="다음 곡">' + icon('next') + '</button></div>' +
      '<div class="music-dock-timeline"><input data-music-seek type="range" min="0" max="1000" value="0" aria-label="재생 위치"><span data-music-current>0:00</span><span data-music-duration>--:--</span></div>' +
      '<details class="music-dock-volume"><summary aria-label="음량" title="음량">' + icon('volume') + '</summary><label>음량<input data-music-volume type="range" min="0" max="100" step="1" value="40" aria-label="음량"></label></details>' +
      '<a class="music-dock-link" aria-label="음악 페이지" title="음악 페이지">' + icon('music') + '</a>';
    $('.music-dock-link', dock).href = pageUrl;
  }
  const dockStatus = doc.createElement('span');
  dockStatus.className = 'music-sr-only';
  dockStatus.setAttribute('data-music-status', '');
  dockStatus.setAttribute('role', 'status');
  dockStatus.setAttribute('aria-live', 'polite');
  dock.append(dockStatus);
  doc.body.append(dock);
  doc.body.classList.add('has-music-dock');
  doc.documentElement.classList.add('has-music-dock');

  // The body's reserved space follows the actual dock height, including small screens.
  let dockFrame = 0;
  function measureDock() {
    dockFrame = 0;
    const bottom = Number.parseFloat(getComputedStyle(dock).bottom) || 0;
    const space = Math.ceil(dock.getBoundingClientRect().height + bottom + 18);
    doc.documentElement.style.setProperty('--music-dock-space', `${space}px`);
    const roster = $('.select');
    const portrait = roster && $('.sel-stage', roster);
    if (portrait) {
      const headerHeight = $('.top')?.offsetHeight || 0;
      roster.classList.toggle('music-portrait-flow', portrait.offsetHeight + headerHeight + space > innerHeight + 2);
    }
    const atlas = $('[data-atlas]');
    const map = atlas && $('.map-wrap', atlas);
    if (map) {
      const headerHeight = $('.top')?.offsetHeight || 0;
      atlas.classList.toggle('music-atlas-flow', map.offsetHeight + headerHeight + 24 + space > innerHeight + 2);
    }
  }
  function scheduleMeasure() { if (!dockFrame) dockFrame = requestAnimationFrame(measureDock); }
  if ('ResizeObserver' in window) new ResizeObserver(scheduleMeasure).observe(dock);
  addEventListener('resize', scheduleMeasure, { passive: true });
  doc.fonts?.ready.then(scheduleMeasure);
  measureDock();

  // Give the server-rendered transport the same symbols without replacing its labels.
  if (page) {
    $$('[data-music-prev], [data-music-next], [data-music-toggle]', page).forEach(button => {
      const kind = button.hasAttribute('data-music-prev') ? 'prev' : button.hasAttribute('data-music-next') ? 'next' : 'play';
      const label = button.textContent.trim() || ({ prev: '이전 곡', next: '다음 곡', play: '재생' })[kind];
      button.innerHTML = icon(kind);
      button.setAttribute('aria-label', label);
      if (kind === 'play') {
        const text = doc.createElement('span');
        text.className = 'music-toggle-label';
        text.textContent = label;
        button.append(text);
      }
    });
  }

  const seeks = $$('[data-music-seek]');
  const volumes = $$('[data-music-volume]');
  const titles = $$('[data-music-title]');
  const covers = $$('[data-music-cover]');
  const toggles = $$('[data-music-toggle]');
  const statuses = $$('[data-music-status]');
  const tracks = $$('[data-music-track]');
  tracks.forEach(button => {
    const placeholder = $('.music-track-placeholder', button);
    if (placeholder) placeholder.textContent = $('b', button)?.textContent || '';
  });
  const sourceLink = page ? doc.createElement('a') : null;
  if (sourceLink) {
    sourceLink.className = 'music-source-link';
    sourceLink.textContent = '오디오 파일 열기';
    sourceLink.hidden = true;
    $('.music-console', page).append(sourceLink);
  }
  let state = null;
  let scrubbing = null;
  let lastToggle = '';
  let lastTrack = null;
  const seconds = value => Number.isFinite(Number(value)) ? Math.max(0, Number(value)) : 0;
  const clock = value => { const n = Math.floor(seconds(value)); return `${Math.floor(n / 60)}:${String(n % 60).padStart(2, '0')}`; };
  const durationClock = value => clock(Math.round(seconds(value)));
  const write = (node, value) => { if (node && node.textContent !== value) node.textContent = value; };
  const engine = () => window.ERNMusic;
  const list = () => engine()?.tracks || config.tracks || [];

  function update(next) {
    if (!next) return;
    state = next;
    const track = next.track || list().find(item => item.id === next.trackId) || list()[next.index || 0] || {};
    const title = next.title || track.title || 'Break Ground';
    const duration = seconds(next.duration || track.duration);
    const time = seconds(next.currentTime);
    const isActive = !!(next.playing || next.loading && next.wantsPlay && !next.blocked && !next.error);
    const label = isActive ? '일시정지' : '재생';
    const available = next.available !== false;
    dock.dataset.musicState = next.status || 'idle';
    if (page) page.dataset.musicState = next.status || 'idle';
    titles.forEach(node => write(node, title));
    if (lastTrack !== next.trackId || covers.some(img => (img.dataset.coverSource || '') !== (next.cover || track.cover || ''))) {
      lastTrack = next.trackId;
      const source = next.cover || track.cover || '';
      covers.forEach(img => {
        img.dataset.coverSource = source;
        img.hidden = !source;
        img.alt = source && page?.contains(img) ? `${title} 표지` : '';
        if (source && img.getAttribute('src') !== source) img.src = source;
        if (!source) img.removeAttribute('src');
      });
      const fallback = $('.music-art-fallback');
      write(fallback, title);
      if (fallback) fallback.hidden = !!source;
      dock.classList.toggle('has-cover', !entry && !!source);
    }
    if (lastToggle !== label) {
      lastToggle = label;
      toggles.forEach(button => {
        const svg = $('.music-icon', button);
        if (svg) svg.innerHTML = symbols[isActive ? 'pause' : 'play'];
        write($('.music-toggle-label', button), label);
        button.setAttribute('aria-label', (entry && dock.contains(button) ? '배경 음악 ' : '') + label);
        button.title = (entry && dock.contains(button) ? '배경 음악 ' : '') + label;
      });
    }
    $$('[data-music-prev], [data-music-next], [data-music-toggle]').forEach(button => { button.disabled = !available; });
    $$('[data-music-current]').forEach(node => write(node, clock(time)));
    $$('[data-music-duration]').forEach(node => write(node, duration ? durationClock(duration) : '--:--'));
    seeks.forEach(input => {
      input.disabled = !available || !duration;
      if (input !== scrubbing) input.value = String(duration ? Math.round(time / duration * 1000) : 0);
      input.style.setProperty('--music-fill', `${Number(input.value) / 10}%`);
      input.setAttribute('aria-valuetext', `${clock(time)} / ${duration ? durationClock(duration) : '--:--'}`);
    });
    volumes.forEach(input => {
      input.disabled = !available;
      if (input !== doc.activeElement) input.value = String(Math.round((next.volume ?? .4) * 100));
      input.style.setProperty('--music-fill', `${input.value}%`);
      input.setAttribute('aria-valuetext', `${input.value}%`);
    });
    tracks.forEach(button => {
      const selected = button.dataset.musicTrack === next.trackId;
      button.setAttribute('aria-pressed', String(selected));
      button.disabled = !available;
    });
    $$('[data-music-track-duration]').forEach(node => {
      const item = list().find(track => track.id === node.dataset.musicTrackDuration);
      const length = node.dataset.musicTrackDuration === next.trackId ? duration : seconds(item?.duration);
      write(node, length ? durationClock(length) : '--:--');
    });
    const status = !available ? '음악을 재생할 수 없습니다.' : next.error ? '재생할 수 없습니다. 다시 재생해 주세요.' : next.blocked ? '재생 버튼을 눌러 음악을 시작하세요.' : next.loading ? '불러오는 중' : next.playing ? '재생 중' : next.status === 'paused' ? '일시정지' : '';
    statuses.forEach(node => write(node, status));
    if (sourceLink) {
      sourceLink.hidden = !((next.error || !available) && track.src);
      if (track.src) sourceLink.href = track.src;
    }
    if (page) page.setAttribute('aria-busy', String(!!next.loading));
  }

  doc.addEventListener('click', event => {
    const target = event.target.closest('[data-music-toggle], [data-music-prev], [data-music-next], [data-music-track]');
    if (!target || target.disabled || !engine()) return;
    if (target.hasAttribute('data-music-toggle')) engine().toggle();
    else if (target.hasAttribute('data-music-prev')) engine().previous();
    else if (target.hasAttribute('data-music-next')) engine().next();
    else engine().select(target.dataset.musicTrack, { play: true });
  });
  seeks.forEach(input => {
    input.addEventListener('pointerdown', () => { scrubbing = input; });
    input.addEventListener('input', () => {
      const duration = seconds(state?.duration || state?.track?.duration);
      const time = duration * Number(input.value) / 1000;
      input.style.setProperty('--music-fill', `${Number(input.value) / 10}%`);
      input.setAttribute('aria-valuetext', `${clock(time)} / ${durationClock(duration)}`);
      engine()?.seek(time);
    });
    const finish = () => { if (scrubbing === input) scrubbing = null; if (engine()) update(engine().getState()); };
    input.addEventListener('change', finish);
    input.addEventListener('blur', finish);
    input.addEventListener('pointercancel', finish);
  });
  addEventListener('pointerup', () => { scrubbing = null; });
  volumes.forEach(input => input.addEventListener('input', () => {
    input.style.setProperty('--music-fill', `${input.value}%`);
    engine()?.setVolume(Number(input.value) / 100);
  }));
  const volumePanel = $('.music-dock-volume');
  let keyboardNavigation = false;
  doc.addEventListener('pointerdown', () => { keyboardNavigation = false; }, { passive: true });
  doc.addEventListener('keydown', event => {
    if (event.key === 'Tab') keyboardNavigation = true;
    if (event.key === 'Escape' && volumePanel?.open) {
      volumePanel.open = false;
      $('summary', volumePanel).focus();
    }
  });
  doc.addEventListener('click', event => {
    if (volumePanel?.open && !volumePanel.contains(event.target)) volumePanel.open = false;
  });
  doc.addEventListener('focusin', event => {
    const target = event.target;
    if (!keyboardNavigation || !(target instanceof HTMLElement) || dock.contains(target) || !target.closest('main')) return;
    requestAnimationFrame(() => {
      if (doc.activeElement !== target) return;
      const rect = target.getBoundingClientRect();
      const edge = dock.getBoundingClientRect().top - 12;
      if (rect.bottom > edge && rect.top < innerHeight) scrollBy({ top: rect.bottom - edge, behavior: 'instant' });
    });
  });
  addEventListener('ern:music-change', event => update(event.detail));
  addEventListener('ern:music-ready', event => update(event.detail || engine()?.getState()));
  if (engine()) update(engine().getState());
  else {
    update({ trackId: config.tracks?.[0]?.id, track: config.tracks?.[0], volume: .4, status: 'idle' });
    addEventListener('load', () => {
      if (!engine()) update({ trackId: config.tracks?.[0]?.id, track: config.tracks?.[0], volume: .4, available: false, status: 'error' });
    }, { once: true });
  }
})();
