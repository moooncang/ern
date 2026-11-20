/* The manuscript responds to reading and selection. Core controls stay in main.js. */
(() => {
  'use strict';
  const doc = document;
  if (doc.body.classList.contains('cover')) return;
  const motion = (window.ERNPresentation ||= { motion: matchMedia('(prefers-reduced-motion: reduce)') }).motion;
  const $ = (selector, root = doc) => root.querySelector(selector);
  const $$ = (selector, root = doc) => [...root.querySelectorAll(selector)];
  const decorative = (className, parent) => {
    const node = doc.createElement('span');
    node.className = className;
    node.setAttribute('aria-hidden', 'true');
    parent.append(node);
    return node;
  };

  const header = $('.top'), tabs = $('.tabs');
  if (header && tabs) {
    const ribbon = decorative('tab-ribbon', tabs);
    const current = () => $('a[aria-current]', tabs);
    function mark(link) {
      ribbon.hidden = !link;
      if (!link) return;
      ribbon.style.width = `${link.offsetWidth}px`;
      ribbon.style.transform = `translateX(${link.offsetLeft}px)`;
    }
    const restore = () => mark(tabs.contains(doc.activeElement) && doc.activeElement.matches('a') ? doc.activeElement : current());
    $$('a', tabs).forEach(link => {
      link.addEventListener('pointerenter', () => mark(link));
      link.addEventListener('focus', () => mark(link));
    });
    tabs.addEventListener('pointerleave', restore);
    tabs.addEventListener('focusout', () => requestAnimationFrame(restore));
    new ResizeObserver(restore).observe(tabs);
    doc.fonts.ready.then(restore);
    restore();

    const progress = decorative('reading-progress', header);
    let pending = false;
    const paint = () => {
      pending = false;
      const total = doc.documentElement.scrollHeight - innerHeight;
      progress.style.transform = `scaleX(${total > 0 ? Math.min(1, Math.max(0, scrollY / total)) : 0})`;
      header.classList.toggle('has-scrolled', scrollY > 24);
    };
    const schedule = () => { if (!pending) { pending = true; requestAnimationFrame(paint); } };
    addEventListener('scroll', schedule, { passive: true });
    addEventListener('resize', schedule);
    addEventListener('pageshow', schedule);
    new ResizeObserver(schedule).observe(doc.body);
    paint();
  }

  // Accessible controls supplement native horizontal scrolling and touch swiping.
  const deck = $('.deck');
  if (deck) {
    const cards = $$('.tilt', deck);
    const contactSheet = doc.createElement('div');
    contactSheet.className = 'deck-thumbs wrap';
    contactSheet.setAttribute('role', 'group');
    contactSheet.setAttribute('aria-label', deck.getAttribute('aria-label'));
    const thumbnails = cards.map((card, index) => {
      const source = $('img', card), button = doc.createElement('button'), thumbnail = doc.createElement('img');
      button.type = 'button'; button.className = 'deck-thumb';
      button.setAttribute('aria-label', source.alt);
      button.setAttribute('aria-pressed', 'false');
      thumbnail.src = source.currentSrc || source.src;
      thumbnail.alt = ''; thumbnail.loading = 'lazy'; thumbnail.decoding = 'async';
      thumbnail.width = +source.getAttribute('width'); thumbnail.height = +source.getAttribute('height');
      button.append(thumbnail); contactSheet.append(button);
      button.addEventListener('click', () => moveTo(index));
      return button;
    });
    const controls = doc.createElement('div');
    controls.className = 'deck-tools wrap';
    controls.setAttribute('role', 'group');
    controls.setAttribute('aria-label', '인물 카드 이동');
    const makeButton = (label, flip) => {
      const button = doc.createElement('button');
      button.type = 'button'; button.setAttribute('aria-label', label);
      button.innerHTML = `<svg class="ico${flip ? ' flip' : ''}" aria-hidden="true"><use href="#i-next"/></svg>`;
      return button;
    };
    const previous = makeButton('이전 인물 카드', true), next = makeButton('다음 인물 카드', false);
    const count = doc.createElement('span'); count.className = 'deck-count';
    count.setAttribute('aria-live', 'polite'); count.setAttribute('aria-atomic', 'true');
    controls.append(previous, count, next); deck.after(contactSheet, controls);
    let selected = 0, scheduled = false, requested = null;
    function revealThumbnail(index) {
      const button = thumbnails[index], box = button.getBoundingClientRect(), strip = contactSheet.getBoundingClientRect();
      const padding = parseFloat(getComputedStyle(contactSheet).paddingLeft);
      const left = strip.left + padding, right = strip.right - padding;
      const delta = box.left < left ? box.left - left : box.right > right ? box.right - right : 0;
      if (Math.abs(delta) > 1) contactSheet.scrollBy({ left: delta, behavior: 'instant' });
    }
    function paint() {
      scheduled = false;
      const bounds = deck.getBoundingClientRect();
      const start = bounds.left + parseFloat(getComputedStyle(deck).paddingLeft);
      let distance = Infinity;
      cards.forEach((card, index) => {
        const offset = Math.abs(card.getBoundingClientRect().left - start);
        if (offset < distance) { distance = offset; selected = index; }
      });
      previous.disabled = deck.scrollLeft < 2;
      next.disabled = deck.scrollLeft >= deck.scrollWidth - deck.clientWidth - 2;
      if (previous.disabled) selected = 0;
      else if (next.disabled) selected = cards.length - 1;
      const position = String(selected + 1).padStart(2, '0');
      const value = `${position} / ${String(cards.length).padStart(2, '0')}`;
      if (count.textContent !== value) count.textContent = value;
      cards.forEach((card, index) => card.classList.toggle('card-current', index === selected));
      thumbnails.forEach((button, index) => {
        const pressed = String(index === selected);
        if (button.getAttribute('aria-pressed') !== pressed) button.setAttribute('aria-pressed', pressed);
      });
      if (requested !== null && Math.abs(deck.scrollLeft - (cards[requested].offsetLeft - cards[0].offsetLeft)) < 2) requested = null;
      const focused = thumbnails.indexOf(doc.activeElement);
      revealThumbnail(requested !== null && focused === requested ? focused : selected);
    }
    function moveTo(index) {
      // Layout offsets ignore the pointer tilt and never move the page vertically.
      const target = Math.max(0, Math.min(cards.length - 1, index));
      requested = target;
      deck.scrollTo({ left: cards[target].offsetLeft - cards[0].offsetLeft, behavior: motion.matches ? 'instant' : 'smooth' });
    }
    function move(direction) {
      moveTo((requested ?? selected) + direction);
    }
    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    deck.addEventListener('keydown', event => {
      if (event.target !== deck || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault(); event.stopPropagation(); move(event.key === 'ArrowRight' ? 1 : -1);
    });
    contactSheet.addEventListener('keydown', event => {
      const index = thumbnails.indexOf(event.target);
      if (index < 0 || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault(); event.stopPropagation();
      const target = event.key === 'Home' ? 0 : event.key === 'End' ? cards.length - 1 :
        Math.max(0, Math.min(cards.length - 1, index + (event.key === 'ArrowRight' ? 1 : -1)));
      thumbnails[target].focus({ preventScroll: true });
      revealThumbnail(target); moveTo(target);
    });
    thumbnails.forEach((button, index) => button.addEventListener('focus', () => revealThumbnail(index)));
    deck.addEventListener('pointerdown', () => { requested = null; }, { passive: true });
    deck.addEventListener('wheel', () => { requested = null; }, { passive: true });
    motion.addEventListener('change', () => {
      if (motion.matches && requested !== null) moveTo(requested);
    });
    deck.addEventListener('scroll', () => { if (!scheduled) { scheduled = true; requestAnimationFrame(paint); } }, { passive: true });
    new ResizeObserver(paint).observe(deck);
    paint();
  }

  const active = new Map();
  function inkSettle(node) {
    if (!node || motion.matches) return;
    active.get(node)?.cancel();
    const animation = node.animate([
      { opacity: .45, transform: 'translateY(7px)' },
      { opacity: 1, transform: 'translateY(0)' }
    ], { duration: 420, easing: 'cubic-bezier(.16,1,.3,1)' });
    active.set(node, animation);
    animation.finished.then(() => { if (active.get(node) === animation) active.delete(node); }).catch(() => {});
  }
  const growth = $('[data-grow]');
  if (growth) new MutationObserver(() => inkSettle($('.g-info', growth))).observe($('.g-name', growth), { childList: true });
  const estate = $('[data-est-out]');
  if (estate) new MutationObserver(() => inkSettle(estate)).observe(estate, { childList: true });
  motion.addEventListener('change', () => {
    if (motion.matches) { active.forEach(animation => animation.cancel()); active.clear(); }
  });
})();
