/* The manuscript responds to reading and selection. Core controls stay in main.js. */
(() => {
  'use strict';
  const doc = document;
  if (doc.body.classList.contains('cover')) return;
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
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
    controls.append(previous, count, next); deck.after(controls);
    let selected = 0, scheduled = false;
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
    }
    function move(direction) {
      const width = cards[0].getBoundingClientRect().width + parseFloat(getComputedStyle(deck).gap);
      deck.scrollBy({ left: width * direction, behavior: motion.matches ? 'instant' : 'smooth' });
    }
    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    deck.addEventListener('keydown', event => {
      if (event.target !== deck || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault(); event.stopPropagation(); move(event.key === 'ArrowRight' ? 1 : -1);
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
