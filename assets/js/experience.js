/* 조용히 돕는 장치들: 길잡이, 읽기 진행, 명부 넘기기, 초안 보관. */
(() => {
  'use strict';

  const d = document;
  const $ = (selector, scope = d) => scope.querySelector(selector);
  const $$ = (selector, scope = d) => [...scope.querySelectorAll(selector)];
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const mobile = matchMedia('(max-width: 760px)');
  const header = $('header.top');
  const toggle = $('[data-menu-toggle]');
  const nav = $('#site-nav');
  const progress = $('[data-reading-progress]');
  const dialog = $('dialog[data-shortcuts]');
  const ceremony = $('dialog[data-ceremony]');
  const typing = target => target instanceof Element && Boolean(target.closest('input, textarea, select, [contenteditable]:not([contenteditable="false"])'));

  // Keep the existing links usable without JavaScript; only enhance the mobile view.
  function setMenu(open, returnFocus = false) {
    if (!toggle || !nav) return;
    const expanded = Boolean(open && mobile.matches);
    toggle.setAttribute('aria-expanded', String(expanded));
    header?.classList.toggle('menu-open', expanded);
    d.body.classList.toggle('menu-open', expanded);
    nav.inert = mobile.matches && !expanded;
    if (returnFocus) toggle.focus();
  }

  if (toggle && nav) {
    toggle.setAttribute('aria-controls', nav.id);
    toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
    nav.addEventListener('click', event => {
      if (event.target.closest('a')) setMenu(false);
    });
    d.addEventListener('click', event => {
      if (mobile.matches && !nav.contains(event.target) && !toggle.contains(event.target)) setMenu(false);
    });
    mobile.addEventListener('change', () => setMenu(false));
    setMenu(false);
  }

  let scrollPending = false;
  function paintScroll() {
    scrollPending = false;
    header?.classList.toggle('scrolled', scrollY > 20);
    if (progress) {
      const distance = d.documentElement.scrollHeight - innerHeight;
      const fraction = distance > 0 ? Math.max(0, Math.min(1, scrollY / distance)) : 0;
      progress.style.transform = `scaleX(${fraction})`;
    }
  }
  function requestScrollPaint() {
    if (scrollPending) return;
    scrollPending = true;
    requestAnimationFrame(paintScroll);
  }
  addEventListener('scroll', requestScrollPaint, { passive: true });
  addEventListener('resize', requestScrollPaint, { passive: true });
  addEventListener('pageshow', requestScrollPaint);
  if ('ResizeObserver' in window && progress) new ResizeObserver(requestScrollPaint).observe(d.body);
  paintScroll();

  function openHelp() {
    if (!dialog || typeof dialog.showModal !== 'function' || dialog.open) return;
    setMenu(false);
    dialog.showModal();
  }
  if (dialog) {
    $$('[data-help]').forEach(button => button.addEventListener('click', openHelp));
    $$('[data-close-help]', dialog).forEach(button => button.addEventListener('click', () => dialog.close()));
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    });
  }
  if (ceremony) {
    $$('[data-open-writ]').forEach(link => link.addEventListener('click', event => {
      if (typeof ceremony.showModal !== 'function') return;
      event.preventDefault();
      setMenu(false);
      if (!ceremony.open) ceremony.showModal();
    }));
    $$('[data-close-writ]', ceremony).forEach(button => button.addEventListener('click', () => ceremony.close()));
    ceremony.addEventListener('click', event => {
      if (event.target !== ceremony) return;
      const bounds = ceremony.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) ceremony.close();
    });
  }
  // Capture prevents the site's 1–4/Q/E shortcuts from navigating behind a modal.
  d.addEventListener('keydown', event => {
    if (dialog?.open) {
      event.stopPropagation();
      return;
    }
    if (event.key === 'Escape' && toggle?.getAttribute('aria-expanded') === 'true') {
      event.preventDefault();
      event.stopPropagation();
      setMenu(false, true);
      return;
    }
    if (event.key === '?' && !ceremony?.open && !typing(event.target) && !event.ctrlKey && !event.metaKey && !event.altKey && dialog) {
      event.preventDefault();
      event.stopPropagation();
      openHelp();
    }
  }, true);

  $$('[data-gallery]').forEach(gallery => {
    const track = $('[data-gallery-track]', gallery);
    const previous = $('[data-gallery-prev]', gallery);
    const next = $('[data-gallery-next]', gallery);
    if (!track) return;
    const paint = () => {
      const end = Math.max(0, track.scrollWidth - track.clientWidth);
      if (previous) previous.disabled = track.scrollLeft <= 1;
      if (next) next.disabled = track.scrollLeft >= end - 1;
    };
    const move = direction => track.scrollBy({
      left: direction * track.clientWidth * .85,
      behavior: reducedMotion.matches ? 'instant' : 'smooth',
    });
    if (track.id) [previous, next].forEach(button => button?.setAttribute('aria-controls', track.id));
    previous?.addEventListener('click', () => move(-1));
    next?.addEventListener('click', () => move(1));
    track.addEventListener('scroll', paint, { passive: true });
    addEventListener('resize', paint, { passive: true });
    if ('ResizeObserver' in window) new ResizeObserver(paint).observe(track);
    paint();
  });

  // main.js owns the name and rendered note; restore fields and let it render.
  const note = $('[data-note]');
  if (note) {
    const fields = $$('input[data-n], textarea[data-n]', note);
    const slots = $$('[data-modes] .slot');
    const key = 'ern-note-v1';
    try {
      const saved = JSON.parse(localStorage.getItem(key) || 'null');
      if (saved && typeof saved === 'object') {
        fields.forEach(field => {
          const value = saved.fields?.[field.dataset.n];
          if (typeof value === 'string') field.value = value.slice(0, 4000);
        });
        if (!location.hash) {
          const chosen = slots.find(slot => slot.dataset.m === saved.mode);
          if (chosen) {
            const originalURL = location.href;
            chosen.click();
            history.replaceState(history.state, '', originalURL);
          }
        }
        note.dispatchEvent(new Event('input', { bubbles: true }));
      }
    } catch { /* Private browsing or a damaged draft must not block the form. */ }

    const save = () => {
      const saved = {
        mode: slots.find(slot => slot.getAttribute('aria-selected') === 'true')?.dataset.m,
        fields: Object.fromEntries(fields.map(field => [field.dataset.n, field.value.slice(0, 4000)])),
      };
      try { localStorage.setItem(key, JSON.stringify(saved)); } catch { /* Storage is optional. */ }
    };
    note.addEventListener('input', save);
    slots.forEach(slot => slot.addEventListener('click', save));
  }
})();
