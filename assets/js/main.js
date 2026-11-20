/* 변경의 신임 영주가 되었다 — 사이트 동작 */
(() => {
  const d = document, root = d.documentElement;
  const $ = (s, r = d) => r.querySelector(s);
  const $$ = (s, r = d) => [...r.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch {} },
  };
  const typing = () => /INPUT|TEXTAREA|SELECT/.test(d.activeElement ? d.activeElement.tagName : '');
  const isCover = d.body.classList.contains('cover');

  /* 녹음된 효과음 엔진. 기존 선택/입장 타이밍과 효과음 설정을 그대로 쓴다. */
  const sfx = window.ERNSFX || { play() {}, toggle() {} };

  /* ── 공기: 계절마다 다른 것이 떠다닌다(입장 화면은 금빛 먼지) ── */
  const air = (() => {
    const cv = $('.air');
    if (!cv || reduce || !isCover) return { reset() {} };
    const g = cv.getContext('2d'), dpr = Math.min(devicePixelRatio || 1, 2);
    const KIND = {
      spring: { n: 22, col: '196,112,128', vy: [.25, .7], vx: [-.2, .5], size: [3, 6], shape: 'petal' },
      summer: { n: 18, col: '168,132,63', vy: [-.35, -.08], vx: [-.2, .2], size: [1.2, 2.6], shape: 'dot' },
      autumn: { n: 20, col: '176,96,38', vy: [.4, 1], vx: [-.4, .7], size: [4, 8], shape: 'leaf' },
      winter: { n: 34, col: '110,132,156', vy: [.3, .9], vx: [-.2, .3], size: [1.2, 3], shape: 'dot' },
      dust: { n: 28, col: '168,132,63', vy: [-.22, -.05], vx: [-.1, .12], size: [.8, 2.2], shape: 'dot' },
    };
    let W = 0, H = 0, ps = [], kind, raf = 0;
    const rnd = (a, b) => a + Math.random() * (b - a);
    function size() { W = cv.width = innerWidth * dpr; H = cv.height = innerHeight * dpr; }
    function make(k, anywhere) {
      return { x: rnd(0, W), y: anywhere ? rnd(0, H) : (k.vy[0] > 0 ? -20 : H + 20), vx: rnd(k.vx[0], k.vx[1]) * dpr, vy: rnd(k.vy[0], k.vy[1]) * dpr,
        s: rnd(k.size[0], k.size[1]) * dpr, rot: rnd(0, 6.28), vr: rnd(-.02, .02), ph: rnd(0, 6.28), a: rnd(.22, .6) };
    }
    function reset() {
      kind = KIND[isCover ? 'dust' : root.dataset.season] || KIND.autumn;
      const count = Math.round(kind.n * Math.min(1, innerWidth / 900 + .35));
      ps = Array.from({ length: count }, () => make(kind, true));
    }
    function frame() {
      raf = requestAnimationFrame(frame);
      g.clearRect(0, 0, W, H);
      for (const p of ps) {
        p.ph += .012; p.rot += p.vr; p.x += p.vx + Math.sin(p.ph) * .35 * dpr; p.y += p.vy;
        if (p.y > H + 24 || p.y < -24 || p.x > W + 24 || p.x < -24) Object.assign(p, make(kind, false));
        g.save(); g.translate(p.x, p.y); g.rotate(p.rot);
        g.fillStyle = `rgba(${kind.col},${p.a * (kind.shape === 'dot' ? .7 + .3 * Math.sin(p.ph * 3) : 1)})`;
        g.beginPath();
        if (kind.shape === 'dot') g.arc(0, 0, p.s, 0, 6.28);
        else if (kind.shape === 'petal') g.ellipse(0, 0, p.s, p.s * .55, 0, 0, 6.28);
        else { g.moveTo(-p.s, 0); g.quadraticCurveTo(0, -p.s * .7, p.s, 0); g.quadraticCurveTo(0, p.s * .7, -p.s, 0); }
        g.fill(); g.restore();
      }
    }
    size(); reset(); frame();
    addEventListener('resize', () => { size(); reset(); });
    d.addEventListener('visibilitychange', () => { cancelAnimationFrame(raf); if (!d.hidden) frame(); });
    return { reset };
  })();

  /* ── 영지 이름: 입장 화면·시작 쪽에서 적으면 사이트 전체에 쓰인다 ── */
  const DEF = d.body.dataset.defaultDomain || '';
  const getName = () => (store.get('ern-domain') || '').trim().slice(0, 12);
  function paintName() {
    const nm = getName();
    root.style.setProperty('--domain-length', Array.from(nm || DEF).length);
    $$('[data-domain]').forEach(el => { el.textContent = nm || DEF; });
    $$('[data-domain-or]').forEach(el => { el.textContent = nm ? `${nm}의 장부는 아직 비어 있습니다.` : el.dataset.domainOr; });
    root.classList.toggle('named', !!nm);
  }
  $$('[data-domain-input]').forEach(inp => {
    inp.value = getName();
    inp.addEventListener('input', () => { store.set('ern-domain', inp.value.trim()); paintName(); d.dispatchEvent(new Event('ern:change')); });
  });
  paintName();

  /* ── 계절 ── */
  function setSeason(s, user) {
    root.dataset.season = s;
    $$('button[data-season]').forEach(b => b.setAttribute('aria-pressed', b.dataset.season === s));
    if (user) { store.set('ern-season', s); sfx.play('chime', 0); air.reset(); }
  }
  $$('button[data-season]').forEach(b => b.addEventListener('click', () => setSeason(b.dataset.season, true)));
  setSeason(root.dataset.season);

  /* ── 등장 ── */
  const rv = $$('[data-rv]');
  if ('IntersectionObserver' in window && !reduce) {
    const io = new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } }),
      { rootMargin: '0px 0px -7% 0px' });
    rv.forEach(el => io.observe(el));
  } else rv.forEach(el => el.classList.add('in'));
  function onceVisible(el, fn) {
    if (!('IntersectionObserver' in window)) return fn();
    const io = new IntersectionObserver(es => { if (es[0].isIntersecting) { io.disconnect(); fn(); } }, { threshold: .45 });
    io.observe(el);
  }

  /* ── 숫자 키로 메뉴 이동, M으로 소리 ── */
  d.addEventListener('keydown', e => {
    if (isCover || typing() || e.metaKey || e.ctrlKey || e.altKey) return;
    const a = $$('.tabs a')[e.key - 1];
    if (a) { sfx.play('page'); location.href = a.href; return; }
    if (e.key === 'm' || e.key === 'M') sfx.toggle();
  });

  /* ── 입장: 봉투를 열고, 꺼낸 서임장에 깃펜으로 칙서를 적는다. ── */
  const writ = $('[data-writ]');
  if (writ) {
    const seal = $('[data-seal]', writ), inp = $('[data-domain-input]', writ);
    const enter = $('[data-enter]', writ), body = $('.writ-body', writ), lines = $$('.ln', writ);
    const scene = $('.envelope-art', writ), paper = $('.letter-document', writ);
    const title = $('.writ-title', writ), titleSlot = $('.letter-title-slot', writ);
    const destination = $('.reading-slot', writ), stationery = $('.stationery', writ);
    const quill = $('.writing-quill', writ), nib = $('.quill-tip', quill), ink = $$('[data-ink]', writ);
    const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
    const timing = { duration: 650, easing: 'cubic-bezier(.4,0,.2,1)', fill: 'forwards' };
    let state = 'sealed';
    const phase = value => { state = value; writ.dataset.state = value; };
    body.inert = true;

    const frames = (duration, draw) => new Promise(resolve => {
      const start = performance.now();
      const tick = now => {
        const progress = Math.max(0, Math.min(1, (now - start) / duration));
        draw(progress);
        if (progress < 1) requestAnimationFrame(tick); else resolve();
      };
      requestAnimationFrame(tick);
    });
    const glyphRect = (node, start, end) => {
      const range = d.createRange(); range.setStart(node, start); range.setEnd(node, end);
      return range.getBoundingClientRect();
    };
    const placePen = (x, y) => {
      const sheet = paper.getBoundingClientRect();
      quill.style.transform = 'translate('+(x-sheet.left)+'px,'+(y-sheet.top)+'px)';
      const size = parseFloat(getComputedStyle(quill).getPropertyValue('--quill-size'));
      const room = innerWidth - 16 - x;
      // Fit the entire transparent image plane, including its bottom-right
      // corner, so turning the feather cannot create mobile scroll overflow.
      const reach = size*Math.hypot(.92,.04);
      const angle = room >= reach ? 0 : -(Math.atan2(.04,.92)+Math.acos(Math.max(0,Math.min(1,room/reach))))*180/Math.PI;
      quill.style.setProperty('--quill-angle', angle+'deg');
    };
    const movePen = async (target, duration) => {
      const from = nib.getBoundingClientRect();
      quill.classList.remove('tracing'); quill.classList.add('lifted');
      await frames(duration, t => {
        const to = target(), ease = t*t*(3-2*t);
        placePen(from.left+(to.x-from.left)*ease, from.top+(to.y-from.top)*ease-Math.sin(t*Math.PI)*13);
      });
      quill.classList.remove('lifted');
    };
    const writeWrit = async () => {
      phase('writing');
      if (d.fonts) await d.fonts.ready;
      const segmenter = typeof Intl.Segmenter === 'function' ? new Intl.Segmenter('ko', {granularity:'grapheme'}) : null;
      const texts = ink.map(paragraph => {
        const text = paragraph.textContent;
        let offset = 0;
        const chunks = segmenter ? Array.from(segmenter.segment(text), part => part.segment) : Array.from(text);
        return chunks.map(value => {const start=offset;offset+=value.length;return {value,start,end:offset};});
      });
      const total = texts.reduce((sum, row) => sum+row.length, 0);
      let completed = 0, first = true;
      for (let line = 0; line < ink.length; line++) {
        const paragraph = ink[line], node = paragraph.firstChild;
        let previous = null;
        for (let index = 0; index < texts[line].length; index++) {
          const glyph = texts[line][index], rect = () => glyphRect(node,glyph.start,glyph.end);
          const target = () => {const r=rect();return {x:r.left,y:r.bottom-2};};
          const current = rect(), prior = previous ? glyphRect(node,previous.start,previous.end) : null;
          const newRow = !prior || Math.abs(current.top-prior.top)>current.height*.6;
          if (newRow && (current.top < 60 || current.bottom > innerHeight-60)) {
            paragraph.scrollIntoView({block:'center',behavior:'instant'});
          }
          if (first) {
            const point=target();placePen(point.x,point.y);quill.classList.add('active');first=false;await pause(150);
          } else if (newRow) {
            await movePen(target, 140);
          }
          quill.classList.add('tracing');
          quill.dataset.inkLine = line; quill.dataset.inkOffset = glyph.start; quill.dataset.inkEnd = glyph.end;
          const duration = /[,.!?]/.test(glyph.value) ? 95 : /\s/.test(glyph.value) ? 15 : 34;
          await frames(duration, t => {
            // Measure the real glyph every frame: line wrapping follows font and viewport changes.
            const r=rect(), p=paragraph.getBoundingClientRect(), x=r.left+r.width*t;
            const top=Math.max(0,r.top-p.top-2), bottom=Math.min(p.height,r.bottom-p.top+2);
            const edge=Math.max(0,Math.min(p.width,x-p.left));
            paragraph.style.clipPath='polygon(0 0,100% 0,100% '+top+'px,'+edge+'px '+top+'px,'+edge+'px '+bottom+'px,0 '+bottom+'px)';
            placePen(x,r.bottom-2-Math.sin(t*Math.PI)*.8);
            paragraph.dataset.inkProgress=((index+t)/texts[line].length).toFixed(4);
            writ.dataset.inkProgress=((completed+index+t)/total).toFixed(4);
            quill.dataset.strokeProgress=t.toFixed(4);
          });
          if (!/\s/.test(glyph.value)) sfx.play('quill',220);
          previous=glyph;
        }
        completed+=texts[line].length;
        paragraph.classList.add('written','on'); paragraph.style.removeProperty('clip-path'); paragraph.dataset.inkProgress='1';
        quill.classList.remove('tracing');
        await pause(170);
      }
      writ.dataset.inkProgress='1';
      quill.classList.add('resting');
      await movePen(() => {const r=paper.getBoundingClientRect();return {x:r.right-82,y:r.bottom-20};},320);
    };
    const ready = () => {
      phase('ready'); writ.removeAttribute('aria-busy'); body.inert = false;
      ink.forEach(line => {line.classList.add('written');line.style.removeProperty('clip-path');line.dataset.inkProgress='1';});
      writ.dataset.inkProgress='1'; lines.forEach(line => line.classList.add('on'));
      inp.focus({ preventScroll: true }); scene.setAttribute('aria-hidden','true');
      const box = inp.getBoundingClientRect();
      if (box.top < 16 || box.bottom > innerHeight - 16) inp.scrollIntoView({ block: 'center', behavior: 'instant' });
    };
    const open = async () => {
      if (state !== 'sealed') return;
      const box = scene.getBoundingClientRect();
      phase('breaking'); writ.setAttribute('aria-busy', 'true');
      seal.setAttribute('aria-expanded', 'true'); seal.setAttribute('tabindex', '-1');
      if (reduce) {
        titleSlot.append(title); destination.append(paper); d.body.classList.add('open');
        scene.classList.add('unsealed','flap-open','flap-behind','parked'); ready(); return;
      }
      d.body.append(scene);
      Object.assign(scene.style, {position:'fixed',left:box.left+'px',top:box.top+'px',width:box.width+'px',height:box.height+'px',right:'auto',bottom:'auto',zIndex:'20'});
      scene.classList.add('unsealed'); sfx.play('crack');
      await pause(200);
      phase('unfolding'); scene.classList.add('flap-open');
      await pause(350); scene.classList.add('flap-behind');
      await pause(250);
      titleSlot.append(title); phase('extracting'); sfx.play('page');
      const envelopeMotion = scene.animate([{transform:'translateY(0)'},{transform:'translateY('+box.height*.28+'px)'}],timing);
      const extraction = paper.animate([{transform:'translateY(0)'},{transform:'translateY('+(-box.height*.55)+'px)'}],timing);
      await Promise.all([envelopeMotion.finished, extraction.finished]);
      const before = paper.getBoundingClientRect(), envelopeBefore = scene.getBoundingClientRect();
      phase('presenting'); destination.append(paper); extraction.cancel(); d.body.classList.add('open');
      const after = paper.getBoundingClientRect();
      const from = 'translate('+(before.left-after.left)+'px,'+(before.top-after.top)+'px) scale('+(before.width/after.width)+','+(before.height/after.height)+')';
      const presentation = paper.animate([{transform:from},{transform:'none'}],{duration:650,easing:'cubic-bezier(.2,.75,.25,1)',fill:'both'});
      // Move the same envelope below the sheet, keep its opacity, and leave it there.
      envelopeMotion.cancel(); stationery.append(scene); scene.removeAttribute('style'); scene.classList.add('parked');
      const stage = stationery.getBoundingClientRect();
      const parked = getComputedStyle(scene);
      const landing = scene.animate([
        {left:(envelopeBefore.left-stage.left)+'px',top:(envelopeBefore.top-stage.top)+'px',width:envelopeBefore.width+'px',height:envelopeBefore.height+'px',transform:'rotate(0deg)'},
        {left:parked.left,top:parked.top,width:parked.width,height:parked.height,transform:'rotate(-5deg)'}
      ],{duration:650,easing:'cubic-bezier(.2,.75,.25,1)',fill:'both'});
      await Promise.all([presentation.finished,landing.finished]); presentation.cancel(); landing.cancel();
      await writeWrit(); ready();
    };
    addEventListener('resize', () => {
      if (state !== 'ready' || !quill.classList.contains('active')) return;
      const sheet = paper.getBoundingClientRect();
      placePen(sheet.right-82, sheet.bottom-20);
    });
    const go = () => {
      if (state !== 'ready') return;
      phase('leaving'); sfx.play('stamp'); d.body.classList.add('go');
      setTimeout(() => { location.href = enter.href; }, reduce ? 0 : 400);
    };
    seal.addEventListener('click', event => { event.preventDefault(); open(); });
    seal.addEventListener('keydown', event => { if (event.key === ' ' && !event.isComposing) { event.preventDefault(); open(); } });
    enter.addEventListener('click', event => { event.preventDefault(); go(); });
    inp.addEventListener('keydown', event => { if (event.key === 'Enter' && !event.isComposing) { event.preventDefault(); enter.focus(); } });
    addEventListener('pageshow', event => {
      if (!event.persisted) return;
      d.body.classList.remove('go');
      if (state === 'leaving') { phase('ready'); body.inert = false; }
    });
  }

  /* ── home: 첫 화면 인물 띠가 마우스를 따라 살짝 움직인다 ── */
  const hero = $('[data-hero]');
  if (hero && fine && !reduce) hero.addEventListener('pointermove', e => {
    hero.style.setProperty('--mx', (e.clientX / innerWidth * 2 - 1).toFixed(3));
  });

  /* ── home: 인물 카드 기울기 ── */
  if (fine && !reduce) $$('.tilt').forEach(t => {
    t.addEventListener('pointermove', e => {
      const r = t.getBoundingClientRect();
      t.style.setProperty('--ry', ((e.clientX - r.left) / r.width - .5) * 12 + 'deg');
      t.style.setProperty('--rx', (.5 - (e.clientY - r.top) / r.height) * 10 + 'deg');
    });
    t.addEventListener('pointerleave', () => { t.style.removeProperty('--rx'); t.style.removeProperty('--ry'); });
  });

  /* ── home: 자라는 영지 ── */
  const grow = $('[data-grow]');
  if (grow) {
    const st = JSON.parse(grow.dataset.stages), range = $('[data-g-range]', grow), groups = $$('.st', grow), pops = $$('[data-g-pop]', grow);
    let cur = -1, shown = 0, raf = 0, touched = false;
    function count(to) {
      cancelAnimationFrame(raf);
      const from = shown, t0 = performance.now(), dur = reduce ? 0 : 700;
      (function step(t) {
        const p = dur ? Math.min(1, (t - t0) / dur) : 1;
        shown = Math.round(from + (to - from) * (1 - Math.pow(1 - p, 3)));
        pops.forEach(el => { el.textContent = shown.toLocaleString('ko-KR'); });
        if (p < 1) raf = requestAnimationFrame(step);
      })(t0);
    }
    function set(i, user) {
      i = +i; if (i === cur) return;
      cur = i; range.value = i; grow.style.setProperty('--p', i / (st.length - 1));
      groups.forEach(gp => {
        const stage = +gp.dataset.s;
        gp.classList.toggle('on', stage <= i);
        if (stage === i && gp.dataset.caption) $('.town', grow).setAttribute('aria-label', gp.dataset.caption);
      });
      $$('[data-g-name]', grow).forEach(el => { el.textContent = st[i][0]; });
      $('[data-g-fac]', grow).textContent = st[i][2];
      $('[data-g-cap]', grow).textContent = i === st.length - 1 ? ' 이상' : '까지';
      $$('[data-g]', grow).forEach(b => { +b.dataset.g === i ? b.setAttribute('aria-current', 'true') : b.removeAttribute('aria-current'); });
      count(st[i][1]);
      if (user) { touched = true; sfx.play(i >= 3 ? 'stamp' : 'page'); }
    }
    range.addEventListener('input', () => set(range.value, true));
    $$('[data-g]', grow).forEach(b => b.addEventListener('click', () => set(b.dataset.g, true)));
    set(0);
    /* 처음 보일 때 한 번, 개척지에서 마을까지 자라는 모습을 보여 준다 */
    if (!reduce) onceVisible(grow, () => [1, 2].forEach((i, k) => setTimeout(() => { if (!touched) set(i); }, 900 + k * 1300)));
  }

  /* ── home: 네 세력 — 결정을 누르면 깃발이 오르내린다 ── */
  const est = $('[data-est]');
  if (est) {
    const ed = JSON.parse(est.dataset.edicts), lv = JSON.parse(est.dataset.levels), out = $('[data-est-out]', est), base = out.textContent;
    const paint = () => {
      const on = $$('.edict[aria-pressed="true"]', est).map(b => b.dataset.e);
      $$('.est-col', est).forEach(c => {
        const v = on.reduce((s, k) => s + (ed[k].fx[c.dataset.k] || 0), 2);
        c.style.setProperty('--lv', v); $('[data-lv]', c).textContent = lv[v];
        c.dataset.dir = v > 2 ? 'up' : v < 2 ? 'down' : '';
      });
      out.textContent = on.length ? on.map(k => ed[k].out).join(' ') : base;
    };
    $$('.edict', est).forEach(b => b.addEventListener('click', () => {
      b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') !== 'true'); sfx.play('stamp', 0); paint();
    }));
  }

  /* 그림을 다 받은 뒤에 바꿔 끼운다 */
  function swap(img, src, alt, still) {
    img.classList.add('out');
    const im = new Image();
    im.onload = im.onerror = () => { if (!still()) return; img.src = src; if (alt != null) img.alt = alt; img.classList.remove('out'); };
    im.src = src;
  }

  /* ── 인물: 고르는 화면 ── */
  const sel = $('[data-select]');
  if (sel) {
    const img = $('[data-sel-img]', sel), ros = $$('.ro', sel), link = $('[data-f-link]', sel), F = {};
    $$('[data-f]:not(button)', sel).forEach(el => { F[el.dataset.f] = el; });
    let cur = null;
    function pick(a, quiet, silent = false) {
      if (!a || a === cur) return;
      const c = JSON.parse(a.dataset.c);
      if (cur) cur.classList.remove('on');
      a.classList.add('on'); cur = a;
      Object.keys(F).forEach(k => { F[k].textContent = c[k]; });
      link.href = a.href;
      if (!quiet) { if (!silent) sfx.play('page', 90); sel.classList.remove('swap'); void sel.offsetWidth; sel.classList.add('swap'); }
      swap(img, c.img, null, () => cur === a);
    }
    // Layout and scrolling can fire mouseenter beneath a stationary pointer.
    // Preview only an intentional pointer movement; focus and touch keep their controls.
    let pointerX = null, pointerY = null;
    d.addEventListener('pointermove', event => {
      if (!fine || event.pointerType === 'touch') return;
      if (event.clientX === pointerX && event.clientY === pointerY) return;
      pointerX = event.clientX; pointerY = event.clientY;
      const link = event.target.closest && event.target.closest('.ro');
      if (link && sel.contains(link)) pick(link, false, true);
    }, { passive: true });
    ros.forEach(a => {
      a.addEventListener('pointerdown', () => { a._was = a === cur; });
      a.addEventListener('focus', () => pick(a));
      /* 손가락으로는 첫 누름이 고르기, 고른 것을 다시 누르면 기록으로 간다 */
      a.addEventListener('click', e => { if (!fine && a._was === false) { e.preventDefault(); pick(a); } });
    });
    $$('.sel-f button', sel).forEach(b => b.addEventListener('click', () => {
      $$('.sel-f button', sel).forEach(x => x.setAttribute('aria-selected', x === b));
      $$('.roster > li', sel).forEach(li => { li.hidden = b.dataset.f !== 'all' && li.dataset.g !== b.dataset.f; });
      pick($('.roster > li:not([hidden]) .ro', sel));
    }));
    sel.addEventListener('keydown', e => {
      if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
      const list = $$('.roster > li:not([hidden]) .ro', sel);
      let i = list.indexOf(d.activeElement); if (i < 0) i = list.indexOf(cur);
      const nx = list[(i + (e.key === 'ArrowDown' ? 1 : list.length - 1)) % list.length];
      if (nx) { nx.focus(); e.preventDefault(); }
    });
    pick(d.getElementById(location.hash.slice(1)) || ros[0], true);
  }

  /* ── 인물 상세: 표정 ── */
  const faces = $('[data-faces]');
  if (faces) {
    const img = $('[data-face]', faces), bs = $$('.face-tabs button', faces);
    let cur = bs[0];
    const show = b => {
      if (b === cur) return;
      cur = b; bs.forEach(x => x.setAttribute('aria-pressed', x === b)); sfx.play('page', 90);
      swap(img, b.dataset.src, b.dataset.alt, () => cur === b);
    };
    bs.forEach(b => b.addEventListener('click', () => show(b)));
    d.addEventListener('keydown', e => {
      if (typing() || e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { show(bs[(bs.indexOf(cur) + (e.key === 'ArrowRight' ? 1 : bs.length - 1)) % bs.length]); e.preventDefault(); }
      const nav = e.key === 'q' || e.key === 'Q' ? $('[data-prev]') : e.key === 'e' || e.key === 'E' ? $('[data-next]') : null;
      if (nav) location.href = nav.href;
    });
    /* 한가할 때 나머지 표정을 미리 받아 둔다 */
    const saver = navigator.connection && navigator.connection.saveData;
    if (!saver) (window.requestIdleCallback || setTimeout)(() => bs.forEach(b => { new Image().src = b.dataset.src; }), { timeout: 3000 });
  }

  /* ── 세계: 약도에서 지역을 고른다 ── */
  const atlas = $('[data-atlas]');
  if (atlas) {
    const keys = $$('.rg-list button', atlas).map(b => b.dataset.r);
    let cur = '';
    function go(k, user) {
      if (k === cur || keys.indexOf(k) < 0) return;
      cur = k;
      $$('[data-r]', atlas).forEach(el => {
        const on = el.dataset.r === k;
        if (el.matches('.rg-info')) el.hidden = !on;
        else if (el.matches('button')) on ? el.setAttribute('aria-current', 'true') : el.removeAttribute('aria-current');
        else el.classList.toggle('on', on);
      });
      if (user) { sfx.play('page'); history.replaceState(null, '', '#' + k); }
    }
    atlas.addEventListener('click', e => {
      const t = e.target.closest('[data-r]');
      if (t && !t.matches('.rg-info')) go(t.dataset.r, true);
    });
    atlas.addEventListener('keydown', e => {
      const rg = e.target.closest('.rg');
      if (rg && (e.key === 'Enter' || e.key === ' ')) { go(rg.dataset.r, true); e.preventDefault(); return; }
      if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
      go(keys[(keys.indexOf(cur) + (e.key === 'ArrowDown' ? 1 : keys.length - 1)) % keys.length], true); e.preventDefault();
    });
    go(keys.indexOf(location.hash.slice(1)) >= 0 ? location.hash.slice(1) : keys[0]);
  }

  /* ── 영지: 시세표에서 수량을 눌러 셈한다 ── */
  const tally = $('[data-tally]');
  if (tally) {
    const coin = v => [[Math.floor(v / 100), '금화'], [Math.floor(v % 100 / 10), '은화'], [v % 10, '동화']]
      .filter(p => p[0]).map(p => p[0].toLocaleString('ko-KR') + p[1]).join(' ') || '0동화';
    const sum = () => {
      let t = 0;
      $$('tbody tr', tally).forEach(r => { const q = +$('output', r).textContent; t += q * r.dataset.v; r.classList.toggle('has', q > 0); });
      $('[data-total]', tally).textContent = coin(t);
    };
    tally.addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      if (b.hasAttribute('data-reset')) $$('tbody output', tally).forEach(o => { o.textContent = 0; });
      else { const o = $('output', b.parentNode); o.textContent = Math.max(0, Math.min(999, +o.textContent + +b.dataset.d)); }
      sfx.play('tick', 0); sum();
    });
  }

  /* ── 시작: 모드 고르기와 유저노트 초안 ── */
  const modes = $('[data-modes]');
  let modeName = '';
  if (modes) {
    const slots = $$('.slot', modes), panes = $$('.mode-pane', modes);
    const set = (k, user) => {
      slots.forEach(b => b.setAttribute('aria-selected', b.dataset.m === k));
      panes.forEach(p => { p.hidden = p.dataset.m !== k; if (!p.hidden) modeName = p.dataset.name; });
      if (user) { sfx.play('stamp', 0); history.replaceState(null, '', '#' + k); }
      d.dispatchEvent(new Event('ern:change'));
    };
    slots.forEach(b => b.addEventListener('click', () => set(b.dataset.m, true)));
    const h = location.hash.slice(1);
    set(panes.some(p => p.dataset.m === h) ? h : panes[0].dataset.m);
  }
  const note = $('[data-note]');
  if (note) {
    const out = $('[data-note-out]', note), said = $('[data-copied]', note);
    const draw = () => {
      const rows = [['시작 모드', modeName], ['영지 이름', getName() || DEF]].concat($$('[data-n]', note).map(i => [i.dataset.n, i.value.trim()]));
      out.textContent = rows.filter(r => r[1]).map(r => `[${r[0]}] ${r[1]}`).join('\n');
    };
    note.addEventListener('input', draw); d.addEventListener('ern:change', draw); draw();
    $('[data-copy]', note).addEventListener('click', () => {
      const fail = () => { said.textContent = '복사하지 못했습니다. 위 글을 직접 선택해 복사해 주십시오.'; };
      if (!navigator.clipboard) return fail();
      navigator.clipboard.writeText(out.textContent).then(() => { said.textContent = '복사했습니다.'; sfx.play('stamp', 0); }, fail);
    });
  }
})();
