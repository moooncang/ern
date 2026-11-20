/* Bounded feedback for the existing inner-page controls. main.js owns their state. */
(() => {
  'use strict';
  const doc = document;
  if (!doc.querySelector('.select, .prof, [data-tally], [data-modes]')) return;

  const motion = (window.ERNPresentation ||= { motion: matchMedia('(prefers-reduced-motion: reduce)') }).motion;
  const active = new Map();
  const $ = (selector, root = doc) => root.querySelector(selector);
  const $$ = (selector, root = doc) => [...root.querySelectorAll(selector)];
  let draftTimer = 0;

  function play(node, frames, options = {}) {
    if (!node || motion.matches || doc.hidden || typeof node.animate !== 'function') return;
    active.get(node)?.cancel();
    const animation = node.animate(frames, {
      duration: 560,
      easing: 'cubic-bezier(.2,.75,.25,1)',
      fill: 'none',
      ...options
    });
    active.set(node, animation);
    const remove = () => { if (active.get(node) === animation) active.delete(node); };
    animation.finished.then(remove, remove);
  }

  function cancelMotion() {
    clearTimeout(draftTimer);
    draftTimer = 0;
    active.forEach(animation => animation.cancel());
    active.clear();
  }
  motion.addEventListener('change', () => { if (motion.matches) cancelMotion(); });
  addEventListener('pagehide', cancelMotion);
  doc.addEventListener('visibilitychange', () => { if (doc.hidden) cancelMotion(); });

  // All content is visible without this observer. Only entering motion is enhanced.
  const entries = $$('.prof .prof-hero img, .prof .prof-hero .plate, .prof .prof-lead, .prof .rec, .prof .faces, .tally, .modes .slots, [data-note]');
  if ('IntersectionObserver' in window) {
    const entryObserver = new IntersectionObserver(records => {
      records.forEach(record => {
        if (!record.isIntersecting) return;
        const node = record.target;
        node.classList.add('scene-in');
        entryObserver.unobserve(node);
        if (node.contains(doc.activeElement)) return;
        play(node, [
          { opacity: .3, transform: 'translateY(30px)' },
          { opacity: 1, transform: 'translateY(0)' }
        ], { duration: 800 });
      });
    }, { threshold: .08, rootMargin: '0px 0px -7% 0px' });
    entries.forEach(node => entryObserver.observe(node));
  } else entries.forEach(node => node.classList.add('scene-in'));

  function observePicture(img, after) {
    if (!img) return;
    let shown = img.getAttribute('src');
    function loaded() {
      const source = img.getAttribute('src');
      if (source === shown || !img.complete || !img.naturalWidth) return;
      shown = source;
      play(img, [
        { opacity: .16, transform: 'translateX(26px)' },
        { opacity: 1, transform: 'translateX(0)' }
      ], { duration: 650 });
      after?.();
    }
    img.addEventListener('load', loaded);
    new MutationObserver(loaded).observe(img, { attributes: true, attributeFilter: ['src'] });
  }

  const roster = $('[data-select]');
  if (roster) {
    const stage = $('.sel-stage', roster);
    const sweep = doc.createElement('span');
    sweep.className = 'scene-portrait-sweep';
    sweep.setAttribute('aria-hidden', 'true');
    stage.append(sweep);
    // Keep the complete portrait and its name reachable on short desktop windows.
    const header = $('.top');
    let portraitFrame = 0;
    function fitPortrait() {
      portraitFrame = 0;
      roster.classList.toggle('scene-portrait-flow', stage.offsetHeight + (header?.offsetHeight || 0) > innerHeight + 1);
    }
    function schedulePortraitFit() {
      if (!portraitFrame) portraitFrame = requestAnimationFrame(fitPortrait);
    }
    if ('ResizeObserver' in window) {
      const observer = new ResizeObserver(schedulePortraitFit);
      observer.observe(stage);
      if (header) observer.observe(header);
    }
    addEventListener('resize', schedulePortraitFit, { passive: true });
    doc.fonts.ready.then(schedulePortraitFit);
    fitPortrait();
    observePicture($('[data-sel-img]', roster), () => {
      play($('.plate', stage), [
        { opacity: .3, transform: 'translateY(15px)' },
        { opacity: 1, transform: 'translateY(0)' }
      ], { duration: 620 });
      play(sweep, [
        { opacity: 0, transform: 'translateX(0)' },
        { opacity: .6, transform: `translateX(${stage.clientWidth * .18}px)`, offset: .3 },
        { opacity: 0, transform: `translateX(${stage.clientWidth * .76}px)` }
      ], { duration: 670 });
    });
    let selected = $('.ro.on', roster);
    new MutationObserver(() => {
      const next = $('.ro.on', roster);
      if (next === selected) return;
      selected = next;
      play($('.sel-info', roster), [
        { opacity: .55, transform: 'translateY(10px)' },
        { opacity: 1, transform: 'translateY(0)' }
      ], { duration: 440 });
    }).observe($('.roster', roster), { subtree: true, attributes: true, attributeFilter: ['class'] });
  }

  observePicture($('[data-face]'));

  const modes = $('[data-modes]');
  if (modes) modes.addEventListener('click', event => {
    const slot = event.target.closest('.slot');
    if (!slot || !modes.contains(slot)) return;
    play($('.mode-pane:not([hidden])', modes), [
      { opacity: .4, transform: 'translateY(17px)' },
      { opacity: 1, transform: 'translateY(0)' }
    ], { duration: 480 });
    play($('.mark', slot), [
      { opacity: .2, transform: 'scale(1.3) rotate(-15deg)' },
      { opacity: 1, transform: 'scale(1) rotate(0)' }
    ], { duration: 380 });
  });

  const tally = $('[data-tally]');
  if (tally) {
    const values = new WeakMap();
    $$('output', tally).forEach(node => values.set(node, node.textContent));
    new MutationObserver(records => {
      const changed = new Set();
      records.forEach(record => {
        const element = record.target.nodeType === Node.ELEMENT_NODE ? record.target : record.target.parentElement;
        const output = element.closest('output');
        if (output) changed.add(output);
      });
      changed.forEach(output => {
        if (values.get(output) === output.textContent) return;
        values.set(output, output.textContent);
        play(output, [
          { opacity: .45, transform: 'translateY(-6px)' },
          { opacity: 1, transform: 'translateY(0)' }
        ], { duration: 330 });
      });
    }).observe(tally, { childList: true, characterData: true, subtree: true });
  }

  const note = $('[data-note]');
  if (note) {
    const draft = $('[data-note-out]', note);
    note.addEventListener('input', () => {
      clearTimeout(draftTimer);
      if (motion.matches) return;
      draftTimer = setTimeout(() => {
        draftTimer = 0;
        play(draft, [
          { borderColor: '#d3a36e' },
          { borderColor: getComputedStyle(draft).borderColor }
        ], { duration: 450 });
      }, 170);
    });
    const status = $('[data-copied]', note);
    let message = status.textContent;
    new MutationObserver(() => {
      if (message === status.textContent) return;
      message = status.textContent;
      play(status, [{ opacity: .3 }, { opacity: 1 }], { duration: 350 });
      if (message === '복사했습니다.') play($('[data-copy]', note), [
        { transform: 'translateY(0)' },
        { transform: 'translateY(2px)', offset: .35 },
        { transform: 'translateY(0)' }
      ], { duration: 260 });
    }).observe(status, { childList: true, characterData: true, subtree: true });
  }
})();
