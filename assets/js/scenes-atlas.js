/* Decorative survey motion; main.js remains the single owner of region selection. */
(() => {
  'use strict';
  const atlas = document.querySelector('[data-atlas]');
  if (!atlas || atlas.classList.contains('survey-ready')) return;
  const map = atlas.querySelector('.map');
  const board = atlas.querySelector('.map-wrap');
  if (!map || !board) return;
  const motion = (window.ERNPresentation ||= { motion: matchMedia('(prefers-reduced-motion: reduce)') }).motion;
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)');
  const ns = 'http://www.w3.org/2000/svg';

  const orbit = document.createElement('div');
  orbit.className = 'survey-orbit';
  orbit.setAttribute('aria-hidden', 'true');
  atlas.prepend(orbit);
  const instruments = document.createElement('div');
  instruments.className = 'survey-instruments';
  instruments.setAttribute('aria-hidden', 'true');
  board.append(instruments);

  const traces = document.createElementNS(ns, 'g');
  traces.classList.add('survey-traces');
  traces.setAttribute('aria-hidden', 'true');
  traces.setAttribute('pointer-events', 'none');
  const routes = [...map.querySelectorAll('.route')];
  routes.forEach((route, index) => {
    const line = document.createElementNS(ns, 'path');
    line.setAttribute('d', route.getAttribute('d'));
    line.setAttribute('pathLength', '1');
    line.classList.add('survey-trace');
    line.style.setProperty('--survey-route-index', index);
    traces.append(line);
  });
  if (routes.length) map.insertBefore(traces, routes[0]);

  atlas.querySelectorAll('.region-marker').forEach((marker, index) => {
    const halo = marker.querySelector('.node-halo');
    const art = marker.querySelector('.region-symbol-art');
    if (!halo || !art) return;
    const cx = +halo.getAttribute('cx'), cy = +halo.getAttribute('cy');
    // Enlarge the existing study around its exact original geographic anchor.
    art.setAttribute('x', cx - 72);
    art.setAttribute('y', cy - 72);
    art.setAttribute('width', '144');
    art.setAttribute('height', '144');
    const measure = document.createElementNS(ns, 'g');
    measure.classList.add('survey-measure');
    measure.setAttribute('aria-hidden', 'true');
    measure.setAttribute('pointer-events', 'none');
    measure.style.setProperty('--survey-marker-index', index);
    const ring = document.createElementNS(ns, 'circle');
    ring.classList.add('survey-measure-ring');
    ring.setAttribute('cx', cx);
    ring.setAttribute('cy', cy);
    ring.setAttribute('r', '67');
    const ticks = document.createElementNS(ns, 'path');
    ticks.setAttribute('d', `M${cx - 74} ${cy}h12M${cx + 62} ${cy}h12M${cx} ${cy - 74}v12M${cx} ${cy + 62}v12`);
    measure.append(ring, ticks);
    const bloom = document.createElementNS(ns, 'circle');
    bloom.classList.add('survey-ink-bloom');
    bloom.setAttribute('cx', cx);
    bloom.setAttribute('cy', cy);
    bloom.setAttribute('r', '59');
    bloom.style.transformOrigin = `${cx}px ${cy}px`;
    marker.insertBefore(measure, halo);
    marker.insertBefore(bloom, art);
  });

  atlas.querySelectorAll('.rg-list button').forEach(button => {
    const record = atlas.querySelector(`.rg-info[data-r="${button.dataset.r}"]`);
    const original = record?.querySelector('.region-symbol-art');
    if (!original) return;
    const miniature = document.createElement('span');
    miniature.className = 'survey-key-art';
    miniature.setAttribute('aria-hidden', 'true');
    miniature.append(original.cloneNode(true));
    button.append(miniature);
  });

  let pointerFrame = 0;
  let measureFrame = 0;
  let pointerPosition = null;
  const reactions = new Set();
  const stopReactions = () => {
    reactions.forEach(animation => animation.cancel());
    reactions.clear();
  };
  const react = (node, frames, options) => {
    if (!node || motion.matches || document.hidden || !node.animate) return null;
    const animation = node.animate(frames, options);
    reactions.add(animation);
    animation.finished.then(() => reactions.delete(animation)).catch(() => reactions.delete(animation));
    return animation;
  };
  let previousRegion = atlas.querySelector('.rg-info:not([hidden])')?.dataset.r;
  const resetDepth = () => {
    if (pointerFrame) cancelAnimationFrame(pointerFrame);
    pointerFrame = 0;
    pointerPosition = null;
    board.style.removeProperty('--survey-tilt-x');
    board.style.removeProperty('--survey-tilt-y');
  };
  const renderDepth = () => {
    pointerFrame = 0;
    if (!pointerPosition || motion.matches || !finePointer.matches) return;
    const rect = board.getBoundingClientRect();
    const x = Math.max(-.5, Math.min(.5, (pointerPosition.x - rect.left) / rect.width - .5));
    const y = Math.max(-.5, Math.min(.5, (pointerPosition.y - rect.top) / rect.height - .5));
    board.style.setProperty('--survey-tilt-x', `${(-y * 1.8).toFixed(3)}deg`);
    board.style.setProperty('--survey-tilt-y', `${(x * 1.8).toFixed(3)}deg`);
  };
  board.addEventListener('pointermove', event => {
    if (motion.matches || !finePointer.matches || event.pointerType === 'touch') return;
    pointerPosition = { x: event.clientX, y: event.clientY };
    if (!pointerFrame) pointerFrame = requestAnimationFrame(renderDepth);
  }, { passive: true });
  board.addEventListener('pointerleave', resetDepth);
  board.addEventListener('pointercancel', resetDepth);
  board.addEventListener('focusin', resetDepth);

  // A short viewport gets the complete folio in normal flow, including its note.
  const header = document.querySelector('.top');
  const measureBoard = () => {
    measureFrame = 0;
    const headerHeight = header?.offsetHeight || 0;
    atlas.classList.toggle('survey-overheight', board.offsetHeight + headerHeight + 36 > innerHeight);
  };
  const scheduleMeasure = () => {
    if (!measureFrame) measureFrame = requestAnimationFrame(measureBoard);
  };
  if ('ResizeObserver' in window) {
    const measureObserver = new ResizeObserver(scheduleMeasure);
    measureObserver.observe(board);
    if (header) measureObserver.observe(header);
  }
  addEventListener('resize', scheduleMeasure, { passive: true });
  document.fonts.ready.then(scheduleMeasure);

  const records = atlas.querySelector('.atlas-side > [aria-live]');
  if (records) {
    new MutationObserver(() => {
      const active = records.querySelector('.rg-info:not([hidden])');
      if (!active || active.dataset.r === previousRegion) return;
      previousRegion = active.dataset.r;
      atlas.dataset.surveyRegion = previousRegion;
      stopReactions();
      if (motion.matches || !active.animate) return;
      react(active, [
        { opacity: .35, transform: 'translate3d(14px, 10px, 0) rotate(.5deg)' },
        { opacity: 1, transform: 'translate3d(0, 0, 0) rotate(0)' }
      ], { duration: 520, easing: 'cubic-bezier(.16,1,.3,1)' });
      const marker = map.querySelector(`.region-marker[data-r="${previousRegion}"]`);
      react(marker?.querySelector('.region-symbol-art'), [
        { opacity: .45, transform: 'translateY(-5px)' },
        { opacity: 1, transform: 'translateY(0)' }
      ], { duration: 580, easing: 'cubic-bezier(.16,1,.3,1)' });
      react(marker?.querySelector('.survey-ink-bloom'), [
        { opacity: 0, transform: 'scale(.72)' },
        { opacity: .18, offset: .3 },
        { opacity: 0, transform: 'scale(1.14)' }
      ], { duration: 650, easing: 'ease-out' });
      react(map.querySelector('.route.on'), [
        { strokeDashoffset: 1, opacity: .45 },
        { strokeDashoffset: 0, opacity: 1 }
      ], { duration: 700, easing: 'cubic-bezier(.22,.61,.36,1)' });
    }).observe(records, { subtree: true, attributes: true, attributeFilter: ['hidden'] });
  }
  const syncMotion = () => {
    resetDepth();
    if (motion.matches) stopReactions();
  };
  motion.addEventListener('change', syncMotion);
  finePointer.addEventListener('change', syncMotion);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { resetDepth(); stopReactions(); }
  });
  atlas.dataset.surveyRegion = previousRegion || 'home';
  atlas.classList.add('survey-ready');
  measureBoard();
})();
