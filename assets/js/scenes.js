/* Scroll scenes enhance the existing game presentation; main.js owns game state. */
(() => {
  'use strict';
  const doc = document, body = doc.body;
  if (body.classList.contains('cover')) return;
  const motion = (window.ERNPresentation ||= { motion: matchMedia('(prefers-reduced-motion: reduce)') }).motion;
  const fine = matchMedia('(hover: hover) and (pointer: fine)');
  const $ = (selector, root = doc) => root.querySelector(selector);
  const $$ = (selector, root = doc) => [...root.querySelectorAll(selector)];
  const sections = $$('main > section');
  const near = new Set(), active = new Map(), lastProgress = new WeakMap();
  let frame = 0;

  function setProgress(section, progress) {
    // Only artwork that consumes progress needs it; the registered property does not inherit.
    // Resolve current artwork so a later-loading atlas module is included as well.
    const targets = [section, ...$$('.scene-frontispiece .fg, .scene-growth .town, .season-observation, .survey-orbit', section)];
    targets.forEach(target => target.style.setProperty('--scene-progress', progress));
  }

  function animate(node, frames, options = {}) {
    if (!node || motion.matches || doc.hidden || !node.animate) return;
    const bounds = node.getBoundingClientRect();
    if (bounds.bottom < 0 || bounds.top > innerHeight) return;
    active.get(node)?.cancel();
    const animation = node.animate(frames, {
      duration: 650, easing: 'cubic-bezier(.16,1,.3,1)', ...options
    });
    active.set(node, animation);
    animation.finished.then(() => {
      if (active.get(node) === animation) active.delete(node);
    }).catch(() => {});
  }
  function enter(section) {
    if (section.classList.contains('scene-in')) return;
    section.classList.add('scene-in');
    animate($('.hd', section), [
      { opacity: .1, translate: '0 25px' }, { opacity: 1, translate: '0 0' }
    ], { duration: 700 });
    if (section.matches('.hero')) {
      $$('.fg', section).forEach((figure, index) => animate(figure,
        [{ opacity: 0, translate: '0 55px' }, { opacity: 1, translate: '0 0' }],
        { delay: index * 65, duration: 950, fill: 'backwards' }));
    }
    if (section.matches('.scene-growth')) animate($('.town', section),
      [{ opacity: .2, translate: '-28px 40px' }, { opacity: 1, translate: '0 0' }], { duration: 950 });
    if (section.matches('.scene-estates')) {
      animate($('.est-board', section),
        [{ opacity: .2, translate: '-30px 28px' }, { opacity: 1, translate: '0 0' }], { duration: 850 });
      animate($('.est-ctl', section),
        [{ opacity: .2, translate: '30px 45px' }, { opacity: 1, translate: '0 0' }], { duration: 850, delay: 140 });
    }
    if (section.matches('.scene-beginnings')) $$('.deed', section).forEach((sheet, index) => animate(sheet,
      [{ opacity: .1, translate: '0 60px' }, { opacity: 1, translate: '0 0' }],
      { duration: 800, delay: index * 100, fill: 'backwards' }));
    section.dispatchEvent(new CustomEvent('ern:scene-enter', { bubbles: true }));
  }
  function paint() {
    frame = 0;
    if (motion.matches || doc.hidden) return;
    const height = innerHeight;
    const updates = [];
    // Read every section before writing styles, avoiding a forced style flush per section.
    near.forEach(section => {
      const rect = section.getBoundingClientRect();
      const progress = Math.max(0, Math.min(1, (height - rect.top) / (height + rect.height)));
      if (Math.abs((lastProgress.get(section) ?? -1) - progress) > .001) {
        updates.push([section, progress]);
      }
    });
    updates.forEach(([section, progress]) => {
      setProgress(section, progress.toFixed(4));
      lastProgress.set(section, progress);
    });
  }
  function schedule() {
    if (!frame && !motion.matches && !doc.hidden) frame = requestAnimationFrame(paint);
  }
  sections.forEach(section => {
    section.classList.add('scene');
    section.style.setProperty('--scene-progress', '.5');
  });
  if ('IntersectionObserver' in window) {
    const entrance = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { enter(entry.target); entrance.unobserve(entry.target); }
    }), { threshold: .03, rootMargin: '0px 0px -7% 0px' });
    const vicinity = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        entry.isIntersecting ? near.add(entry.target) : near.delete(entry.target);
        entry.target.classList.toggle('scene-near', entry.isIntersecting);
      });
      schedule();
    }, { rootMargin: '30% 0px 30% 0px' });
    sections.forEach(section => { entrance.observe(section); vicinity.observe(section); });
  } else sections.forEach(section => { near.add(section); enter(section); });

  const header = $('.top');
  function measureHeader() {
    if (header) doc.documentElement.style.setProperty('--scene-header', `${header.offsetHeight}px`);
    schedule();
  }
  if (header && 'ResizeObserver' in window) new ResizeObserver(measureHeader).observe(header);
  addEventListener('scroll', schedule, { passive: true });
  addEventListener('resize', measureHeader, { passive: true });
  addEventListener('pageshow', () => { preference(); measureHeader(); });
  doc.addEventListener('load', schedule, true);
  doc.fonts.ready.then(measureHeader);

  // The selected specimen follows the existing global season buttons, including the header.
  const specimenStage = $('.season-observation');
  const specimens = $$('[data-specimen]');
  let season = '';
  function showSeason() {
    const next = doc.documentElement.dataset.season || 'autumn';
    if (next === season) return;
    const previous = season;
    season = next;
    specimens.forEach(specimen => specimen.classList.toggle('is-active', specimen.dataset.specimen === next));
    const selected = specimens.find(specimen => specimen.dataset.specimen === next);
    if (previous) animate(selected, [
      { opacity: .2, transform: 'rotate(-7deg) scale(.93)' },
      { opacity: 1, transform: 'rotate(0deg) scale(1)' }
    ], { duration: 720 });
    if (previous) animate($('.specimen-leaf', specimenStage), [
      { opacity: .3, transform: 'translate(22px, 12px) rotate(3deg)' },
      { opacity: 1, transform: 'translate(0, 0) rotate(-7deg)' }
    ], { duration: 650 });
  }
  if (specimenStage) {
    showSeason();
    new MutationObserver(showSeason).observe(doc.documentElement, { attributes: true, attributeFilter: ['data-season'] });
  }

  const growth = $('[data-grow]');
  if (growth) new MutationObserver(() => {
    const layers = $$('.st.on', growth);
    animate(layers.at(-1), [
      { opacity: .25, translate: '20px 5px' }, { opacity: 1, translate: '0 0' }
    ], { duration: 530 });
  }).observe($('.g-name', growth), { childList: true });

  const estateOutput = $('[data-est-out]');
  if (estateOutput) new MutationObserver(() => {
    $$('.est-col em').forEach((label, index) => animate(label,
      [{ opacity: .25, translate: '0 8px' }, { opacity: 1, translate: '0 0' }],
      { duration: 450, delay: index * 35 }));
  }).observe(estateOutput, { childList: true });

  // Small bounded pointer depth on the specimen, with no touch-scroll interception.
  let pointerFrame = 0, pointerX = 0, pointerY = 0;
  function resetPointer() {
    cancelAnimationFrame(pointerFrame); pointerFrame = 0;
    specimenStage?.style.removeProperty('--specimen-x');
    specimenStage?.style.removeProperty('--specimen-y');
  }
  if (specimenStage) {
    specimenStage.addEventListener('pointermove', event => {
      if (!fine.matches || motion.matches || event.pointerType === 'touch') return;
      const rect = specimenStage.getBoundingClientRect();
      pointerX = (event.clientX - rect.left) / rect.width - .5;
      pointerY = (event.clientY - rect.top) / rect.height - .5;
      if (!pointerFrame) pointerFrame = requestAnimationFrame(() => {
        pointerFrame = 0;
        specimenStage.style.setProperty('--specimen-x', `${(pointerX * 12).toFixed(2)}px`);
        specimenStage.style.setProperty('--specimen-y', `${(pointerY * 12).toFixed(2)}px`);
      });
    }, { passive: true });
    specimenStage.addEventListener('pointerleave', resetPointer);
  }
  function preference() {
    body.classList.toggle('scenes-still', motion.matches);
    if (motion.matches) {
      cancelAnimationFrame(frame); frame = 0;
      active.forEach(animation => animation.cancel()); active.clear();
      resetPointer();
      sections.forEach(section => {
        section.classList.add('scene-in');
        setProgress(section, '.5');
        lastProgress.delete(section);
      });
    } else schedule();
  }
  motion.addEventListener('change', preference);
  fine.addEventListener('change', resetPointer);
  doc.addEventListener('visibilitychange', () => {
    if (doc.hidden) {
      cancelAnimationFrame(frame); frame = 0;
      resetPointer();
      active.forEach(animation => animation.cancel()); active.clear();
    } else { preference(); schedule(); }
  });
  body.classList.add('scenes-ready');
  preference();
  measureHeader();
})();
