"""data.py를 읽어 사이트 루트에 HTML을 찍는다.  실행: python _build/build.py"""
import json
import random
import re
from html import escape as e
from pathlib import Path

import data as d

ROOT = Path(__file__).resolve().parent.parent
BY = {c["코드"]: c for c in d.인물}
BOOT = ("(function(r){r.className='js';var s;try{s=localStorage.getItem('ern-season')}catch(e){}"
        "if(!s){var m=new Date().getMonth();s=m<2||m>10?'winter':m<5?'spring':m<8?'summer':'autumn'}"
        "r.dataset.season=s})(document.documentElement)")

# 모든 쪽에 들어가는 그림 조각: 밀랍 인장, 계절 넷, 소리, 화살표
SPRITE = """<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<symbol id="wax" viewBox="0 0 100 100">
<path fill="#8f2020" d="M50 3c9-2 15 5 23 7s17 2 20 11-2 15 0 23 6 16 2 24-13 8-18 15-8 14-17 15-14-6-22-7-18 1-23-7 0-16-3-24-9-14-6-23 12-10 18-16S41 5 50 3z"/>
<circle cx="50" cy="50" r="32" fill="#a12a26"/><circle cx="50" cy="50" r="32" fill="none" stroke="#6f1616" stroke-width="1.5"/>
<path fill="#7a1a1a" d="M50 24c6 4 8 9 5 13 7-1 11 4 7 10 7 0 9 7 3 12 5 3 4 10-3 12 1 6-5 10-12 8-7 2-13-2-12-8-7-2-8-9-3-12-6-5-4-12 3-12-4-6 0-11 7-10-3-4-1-9 5-13z"/>
<path stroke="#a12a26" stroke-width="1.6" stroke-linecap="round" fill="none" d="M50 31v46M50 44l-7-5M50 44l7-5M50 56l-9-5M50 56l9-5M50 67l-7-4M50 67l7-4"/>
<path fill="#fff" opacity=".14" d="M24 36c5-12 16-19 28-19-9 4-17 11-22 22z"/>
</symbol>
<g id="ico" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
<symbol id="i-spring" viewBox="0 0 24 24"><path d="M12 21v-9M12 12c0-4-3-6-7-6 0 4 3 6 7 6zM12 14c0-3 2.5-5 6-5 0 3-2.5 5-6 5z"/></symbol>
<symbol id="i-summer" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 3v2.5M12 18.5V21M3 12h2.5M18.5 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M5.6 18.4l1.8-1.8M16.6 7.4l1.8-1.8"/></symbol>
<symbol id="i-autumn" viewBox="0 0 24 24"><path d="M12 21V6M12 6l-2-3M12 6l2-3M12 10l-4-3M12 10l4-3M12 14l-4-3M12 14l4-3M12 18l-4-3M12 18l4-3"/></symbol>
<symbol id="i-winter" viewBox="0 0 24 24"><path d="M12 3v18M4.2 7.5l15.6 9M19.8 7.5l-15.6 9M12 6l-2-2M12 6l2-2M12 18l-2 2M12 18l2 2"/></symbol>
<symbol id="i-next" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>
</g>
<filter id="wob" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency=".04" numOctaves="2" seed="4"/><feDisplacementMap in="SourceGraphic" scale="2.4"/></filter>
</defs></svg>"""


def ico(name, cls=""):
    return f'<svg class="ico {cls}" aria-hidden="true"><use href="#i-{name}"/></svg>'


def emblem(cls=""):
    return f'''<svg class="emblem {cls}" viewBox="0 0 64 76" fill="none" aria-hidden="true"><path d="M9 10h46v31c0 14-23 27-23 27S9 55 9 41V10Z" stroke="currentColor" stroke-width="1.4"/><path d="M14 15h36v26c0 10-18 21-18 21S14 51 14 41V15Z" stroke="currentColor" stroke-width=".6"/><path d="M32 53V24m0 22c-10 0-14-7-14-7 8-2 14 1 14 7Zm0-9c-8-1-11-7-11-7 7-2 11 2 11 7Zm0 5c10 0 14-7 14-7-8-2-14 1-14 7Zm0-10c8-1 11-7 11-7-7-2-11 2-11 7Zm0-8c-5-5 0-11 0-11s5 6 0 11Z" fill="currentColor"/><path d="M21 5h22M32 0v9" stroke="currentColor"/></svg>'''


def shell(파일, 머리제목, 본문, cover=False, pre=""):
    """공통 프레임. 파일은 HTML 생성기의 단일 출처에서만 갱신한다."""
    title = d.제목 if not 머리제목 else f"{머리제목} · {d.제목}"
    page = "character" if pre else 파일.removesuffix(".html")
    labels = ["THE WORLD", "YOUR DOMAIN", "THE PEOPLE", "BEGIN YOUR STORY"]
    tabs = "".join(
        f'<a href="{pre}{h}"{chr(32) + "aria-current=page" if h == 파일 else ""}><span>{e(t)}</span><small>{labels[i]}</small></a>'
        for i, (h, t) in enumerate(d.메뉴))
    dial = "".join(f'<button type="button" data-season="{k}" aria-pressed="false" aria-label="{e(t)}" title="{e(t)}">{ico(k)}</button>' for k, t, _, _ in d.계절)
    snd = ('<button class="snd" type="button" aria-pressed="true" aria-label="효과음 (M)" title="효과음 (M)">'
           '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9.5h3l4-3.5v12l-4-3.5H4z"/>'
           '<path class="w" d="M14.5 9a4 4 0 0 1 0 6M17 6.5a7.5 7.5 0 0 1 0 11"/><path class="x" d="M15 9.5l5 5m0-5l-5 5"/></svg></button>')
    top = f'''<a class="skip-link" href="#main">본문으로 건너뛰기</a>
<header class="top"><div class="wrap">
<a class="brand" href="{pre}home.html" aria-label="에른 변경 첫 화면">{emblem()}<span>THE ERN MARCH<small>변경의 신임 영주가 되었다</small></span></a>
<nav class="tabs" id="site-nav" aria-label="주 메뉴">{tabs}</nav>
<div class="tools">{snd}<button class="help-button" type="button" data-help aria-label="단축키 안내">?</button><a class="header-cta" href="{pre}start.html">이야기 시작 {ico("next")}</a></div>
<button class="menu-toggle" type="button" data-menu-toggle aria-controls="site-nav" aria-expanded="false" aria-label="메뉴 열기"><span></span><span></span></button>
</div><div class="reading-progress" data-reading-progress></div></header>'''
    foot = "".join(f'<a href="{pre}{h}">{e(t)}</a>' for h, t in d.메뉴)
    bottom = f'''<footer class="foot"><div class="wrap footer-grid"><a class="brand" href="{pre}home.html">{emblem()}<span>THE ERN MARCH<small>왕국의 끝, 당신의 시작.</small></span></a><nav aria-label="바닥글">{foot}</nav><div class="footer-season"><span class="eyebrow">THE TURN OF SEASONS</span><div class="dial" role="group" aria-label="계절">{dial}</div></div></div><div class="wrap footer-bottom"><span>정통 판타지 · 영지 경영 · 캐릭터 챗</span><span class="age-note">19+ 성인 대상 작품</span><a href="#main">맨 위로 ↑</a></div></footer>
<dialog class="shortcuts-dialog" data-shortcuts aria-labelledby="shortcuts-title"><button class="dialog-close" type="button" data-close-help aria-label="단축키 안내 닫기">×</button><p class="eyebrow">A FEW SMALL KEYS</p><h2 id="shortcuts-title">손끝으로 넘기는 기록</h2><dl class="key-list"><dt><kbd>1</kbd> — <kbd>4</kbd></dt><dd>세계 · 영지 · 인물 · 시작</dd><dt><kbd>M</kbd></dt><dd>효과음 켜기 / 끄기</dd><dt><kbd>←</kbd> <kbd>→</kbd></dt><dd>인물 상세에서 표정 넘기기</dd><dt><kbd>Q</kbd> <kbd>E</kbd></dt><dd>이전 / 다음 인물</dd><dt><kbd>?</kbd></dt><dd>단축키 안내</dd></dl><p class="small-print">입력 중에는 단축키가 작동하지 않습니다.</p></dialog>'''
    preload = f'<link rel="preload" as="image" href="{pre}images/art/ern-valley.webp">' if page in ("index", "home") else ""
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(d.소개)}"><meta property="og:title" content="{e(d.제목)}"><meta property="og:description" content="{e(d.소개)}"><meta property="og:type" content="website"><meta property="og:image" content="https://moooncang.github.io/ern/images/art/ern-valley.webp"><meta name="theme-color" content="#f5f1e8">
<script>{BOOT}</script>{preload}<link rel="icon" href="{pre}assets/icons/ern.svg" type="image/svg+xml">
<link rel="stylesheet" href="{pre}assets/css/fonts.css"><link rel="stylesheet" href="{pre}assets/css/style.css"><link rel="stylesheet" href="{pre}assets/css/experience.css"><link rel="stylesheet" href="{pre}assets/css/chapters.css">
</head><body data-page="{page}" data-default-domain="{e(d.기본_영지명)}">{SPRITE}<canvas class="air" aria-hidden="true"></canvas>{top}<main id="main">{본문}</main>{bottom}
<script src="{pre}assets/js/main.js"></script><script src="{pre}assets/js/experience.js"></script></body></html>'''


# ── 공통 조각 ────────────────────────────────────────────────
def block(b):
    kind, *v = b
    if kind == "p":
        return f"<p>{e(v[0])}</p>"
    if kind == "dl":
        return "<dl>" + "".join(f"<dt>{e(t)}</dt><dd>{e(x)}</dd>" for t, x in v[0]) + "</dl>"
    if kind == "table":
        return table(v[0], v[1])
    raise ValueError(f"모르는 블록: {kind}")


def blocks(bs):
    return "".join(block(b) for b in bs)


def table(head, rows):
    h = "".join(f'<th scope="col">{e(x)}</th>' for x in head)
    r = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="scroll"><table><thead><tr>{h}</tr></thead><tbody>{r}</tbody></table></div>'


def hd(제목, 영문, tag="h2", cls=""):
    """소제목 줄: 한글 제목 — 금선 — 영문"""
    return (f'<header class="hd {cls}" data-rv><{tag}>{e(제목)}</{tag}><i></i>'
            f'<span class="en">{e(영문)}</span></header>')


def page_head(영문, 제목, 머리말):
    return (f'<section class="head chapter-head"><div class="wrap"><p class="eyebrow chapter-kicker">THE ERN MARCH / {e(영문)}</p>{hd(제목, 영문, "h1", "big")}'
            f'<p class="lead" data-rv>{e(머리말)}</p></div></section>')


def sec(제목, 영문, 안, cls="", narrow=True, id_=""):
    return (f'<section class="sec {cls}"{f" id={chr(34)}{id_}{chr(34)}" if id_ else ""}>'
            f'<div class="wrap{" narrow" if narrow else ""}">{hd(제목, 영문)}<div data-rv>{안}</div></div></section>')


def plate(c, cls="", heading=False):
    outer, name = ("div", "h1") if heading else ("span", "b")
    return f'<{outer} class="plate {cls}"><small>{e(c["직책"])}</small><{name}>{e(c["이름"])}</{name}></{outer}>'


def crack_button():
    return f'<a class="btn" href="{e(d.크랙_주소)}">크랙에서 시작하기</a>' if d.크랙_주소 else ""


def coin(v):
    """동화 값을 금화·은화·동화로 적는다"""
    parts = [(v // 100, "금화"), (v % 100 // 10, "은화"), (v % 10, "동화")]
    return " ".join(f"{n:,}{u}" for n, u in parts if n) or "0동화"


def n(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def pth(dd, cls=""):
    return f'<path pathLength="1" d="{dd}"{f" class={chr(34)}{cls}{chr(34)}" if cls else ""}/>'


# ── 그림: 자라는 영지 ───────────────────────────────────────
def house(x, w, h, roof=None, base=290):
    r = w * .45 if roof is None else roof
    return (pth(f"M{n(x)} {base}v{n(-h)}l{n(w / 2)} {n(-r)}l{n(w / 2)} {n(r)}v{n(h)}z")
            + pth(f"M{n(x + w * .42)} {base}v{n(-h * .5)}h{n(w * .16)}v{n(h * .5)}"))


def tower(x, w, h, cap="flat", base=290):
    if cap == "spire":
        top = f"l{n(w / 2)} {n(-w * 1.5)}l{n(w / 2)} {n(w * 1.5)}"
    else:
        t = n(w / 5)
        top = f"v-6h{t}v6h{t}v-6h{t}v6h{t}v-6h{t}v6"
    return pth(f"M{n(x)} {base}v{n(-h)}{top}v{n(h)}z")


def flag(x, y):
    return pth(f"M{n(x)} {n(y)}v-18l13 4.5l-13 4.5", "flag")


def zigzag(x1, x2, y, seed):
    rnd, x, dd = random.Random(seed), x1, f"M{x1} {y}"
    while x < x2:
        w = rnd.choice([8, 10, 12, 14])
        dd += f"l{w} {-w}l{w} {w}"
        x += 2 * w
    return pth(dd)


def town():
    g = lambda s, inner, cls="": f'<g class="st {cls}" data-s="{s}">{inner}</g>'
    far = "".join(tower(x, 14, h, "spire") + flag(x + 7, 290 - h - 21) for x, h in
                  [(58, 150), (124, 176), (296, 162), (566, 184), (628, 150), (742, 170)])
    bg5 = far + zigzag(0, 800, 244, 5)
    bg4 = (tower(340, 22, 112, "spire") + tower(438, 22, 112, "spire") + house(352, 96, 72, 30)
           + '<circle pathLength="1" cx="400" cy="232" r="9"/>'
           + house(176, 70, 50, 0) + pth("M176 240a35 30 0 0 1 70 0") + pth("M211 210v-12")
           + zigzag(252, 336, 268, 2) + zigzag(662, 760, 268, 3))
    bg3 = house(470, 64, 54, 22) + flag(502, 214) + house(556, 96, 34, 14)
    s0 = (pth("M356 290l20 -34l20 34z") + pth("M400 290l26 -44l26 44z") + pth("M458 290l19 -30l19 30z")
          + pth("M426 290l0 -22")
          + pth("".join(f"M{x} 290v-12l3 -4l3 4" for x in range(336, 521, 12)))
          + pth("M430 240c-8 -10 6 -16 -2 -28s6 -14 0 -24", "smoke"))
    s1 = (house(250, 50, 30, 18)
          + pth("M308 290v-14h22v14M304 276h30M308 276v-12h22v12M306 264l13 -8l13 8")
          + house(540, 44, 22) + house(592, 40, 20)
          + pth("M648 290l5 -50h18l5 50z")
          + '<g class="spin">' + pth("M662 238l-5 -30h10zM662 238l30 -5v10zM662 238l5 30h-10zM662 238l-30 5v-10z") + "</g>")
    s2 = (house(94, 48, 34, 20) + pth("M142 290v-64l10 -18l10 18v64z")
          + '<circle pathLength="1" cx="152" cy="200" r="3.5"/>'
          + pth("M170 290v-20h34v20M166 270l6 -9h30l6 9z") + pth("M212 290v-18h30v18M208 272l6 -8h26l6 8z")
          + house(700, 50, 26, 14) + pth("M736 258v-18h8v22")
          + pth("M740 236c-6 -8 5 -12 -1 -22s5 -10 0 -18", "smoke"))
    wall = "M40 332V304" + "h12v-6h12v6" * 30 + "V332z"
    s3 = (pth(wall) + pth("M384 332v-14a16 16 0 0 1 32 0v14")
          + "".join(tower(x, 30, 50, base=332) for x in (40, 250, 520, 730)))
    s4 = tower(372, 56, 66, base=332) + pth("M384 332v-14a16 16 0 0 1 32 0v14") + flag(400, 262)
    s5 = ("".join(flag(x + 15, 276) for x in (40, 250, 520, 730))
          + house(2, 30, 14, base=332) + house(768, 28, 12, base=332))
    hills = '<path class="hill" d="M0 232Q120 182 240 216T480 206T800 190"/>'
    ground = '<path class="ground" d="M0 290H800"/>'
    return (f'<svg class="town" viewBox="0 0 800 340" role="img" aria-label="영지가 단계마다 자라는 그림">'
            f'<g filter="url(#wob)">{hills}{g(5, bg5, "far")}{g(4, bg4)}{g(3, bg3)}{ground}'
            f'{g(0, s0)}{g(1, s1)}{g(2, s2)}{g(3, s3)}{g(4, s4)}{g(5, s5)}</g></svg>')


# ── 그림: 에른 변경 약도 ────────────────────────────────────
MAP_AT = {"home": (450, 292), "seril": (676, 122), "kardun": (700, 448),
          "waste": (800, 290), "reibek": (206, 272), "haster": (232, 452)}
MAP_LABEL = {"home": (450, 340), "seril": (676, 196), "kardun": (700, 500),
             "waste": (800, 344), "reibek": (206, 322), "haster": (232, 506)}


def atlas_svg():
    rnd = random.Random(11)
    trees = ""
    for _ in range(26):
        x, y = 676 + rnd.uniform(-118, 118), 118 + rnd.uniform(-58, 50)
        trees += f"M{n(x)} {n(y)}v-6M{n(x - 6)} {n(y - 5)}l6 -15l6 15z"
    peaks = ""
    for x, y, s in [(626, 452, 1), (668, 440, 1.3), (716, 452, 1.1), (760, 444, .9), (690, 470, .8), (738, 474, .9), (646, 478, .7)]:
        peaks += (f"M{n(x - 18 * s)} {y}l{n(18 * s)} {n(-32 * s)}l{n(7 * s)} {n(10 * s)}l{n(5 * s)} {n(-6 * s)}"
                  f"l{n(14 * s)} {n(28 * s)}M{n(x - 4 * s)} {n(y - 18 * s)}l{n(-5 * s)} {n(12 * s)}")
    dots = "".join(f'<circle cx="{n(800 + rnd.uniform(-70, 64))}" cy="{n(286 + rnd.uniform(-62, 46))}" r="1.3"/>'
                   for _ in range(60))
    dunes = "M744 262q14 -10 30 0M790 318q16 -10 34 0M816 250q12 -8 26 0M760 300l8 -6l5 8l7 -5"
    castle = lambda x, y, s: (
        f"M{n(x - 22 * s)} {y}v{n(-16 * s)}h{n(44 * s)}v{n(16 * s)}z"
        f"M{n(x - 28 * s)} {y}v{n(-26 * s)}h{n(4 * s)}v{n(-4 * s)}h{n(4 * s)}v{n(4 * s)}h{n(4 * s)}v{n(26 * s)}"
        f"M{n(x + 16 * s)} {y}v{n(-26 * s)}h{n(4 * s)}v{n(-4 * s)}h{n(4 * s)}v{n(4 * s)}h{n(4 * s)}v{n(26 * s)}"
        f"M{n(x - 5 * s)} {y}v{n(-34 * s)}h{n(10 * s)}v{n(34 * s)}M{x} {n(y - 34 * s)}v{n(-12 * s)}l{n(10 * s)} {n(3 * s)}l{n(-10 * s)} {n(3 * s)}")
    keep = ("M438 300v-22h24v22zM434 278l16 -14l16 14M450 264v-14l11 3.5l-11 3.5"
            "M414 300v-10l8 -7l8 7v10zM470 300v-9l7 -6l7 6v9z")
    glyph = {
        "home": f'<path d="{keep}"/><circle class="ring" cx="450" cy="288" r="46"/>',
        "seril": f'<path d="{trees}"/>',
        "kardun": f'<path d="{peaks}"/>',
        "waste": f'<g class="stip">{dots}</g><path d="{dunes}"/>',
        "reibek": f'<path d="{castle(206, 286, .9)}"/>',
        "haster": f'<path d="{castle(232, 468, 1.25)}"/>',
    }
    route = {
        "seril": "M450 290Q560 170 676 130", "kardun": "M450 290Q590 330 690 430",
        "waste": "M450 290Q620 262 780 288", "reibek": "M450 290C380 302 300 264 216 280",
        "haster": "M450 290Q330 340 248 440",
    }
    out = ""
    for k, 이름, _, _, _ in d.지역:
        (x, y), (lx, ly) = MAP_AT[k], MAP_LABEL[k]
        label = (f'<text class="lb" x="{lx}" y="{ly}" data-domain>{e(d.기본_영지명)}</text>' if k == "home"
                 else f'<text class="lb" x="{lx}" y="{ly}">{e(이름)}</text>')
        out += (f'<g class="rg" data-r="{k}" tabindex="0" role="button" aria-label="{e(이름)}">'
                f'<g class="gl" filter="url(#wob)">{glyph[k]}</g>{label}'
                f'<circle class="pulse" cx="{x}" cy="{y}" r="10"/>'
                f'<ellipse class="hit" cx="{x}" cy="{y + 14}" rx="110" ry="74"/></g>')
    routes = "".join(f'<path class="route" data-r="{k}" pathLength="1" d="{v}"/>' for k, v in route.items())
    compass = ('<g class="compass" transform="translate(96 96)"><circle r="34"/><circle r="26"/>'
               '<path d="M0 -40l7 33l33 7l-33 7l-7 33l-7 -33l-33 -7l33 -7z"/><text y="-48">N</text></g>')
    road = ('<path class="road" d="M436 294C380 306 300 268 232 284S100 270 24 276"/>'
            '<text class="note" x="30" y="258">왕도 라우넨</text><path class="road-end" d="M40 276l-14 0m6 -6l-6 6l6 6"/>')
    return (f'<svg class="map" viewBox="0 0 900 560" role="group" aria-label="에른 변경 약도">'
            f'<rect class="frame" x="8" y="8" width="884" height="544"/><rect class="frame" x="16" y="16" width="868" height="528"/>'
            f'{compass}{road}{routes}{out}</svg>')


# ── 쪽 ───────────────────────────────────────────────────────
def writ_dialog():
    lines = "".join(f'<p class="ln">{e(x)}</p>' for x in d.칙서)
    return f'''<dialog class="ceremony" data-ceremony aria-labelledby="writ-title"><button class="dialog-close" type="button" data-close-writ aria-label="서임장 닫기">×</button><div class="writ" data-writ>{emblem()}<p class="eyebrow">{e(d.칙서_라벨)}</p><h2 id="writ-title">그대에게, 변경의 땅을.</h2><p class="writ-caption">오르텐 왕국의 이름으로 내리는 서임장</p><div class="writ-body"><div>{lines}<p class="ln sign"><label for="dn">영지의 이름</label><input id="dn" data-domain-input maxlength="12" placeholder="{e(d.기본_영지명)}" autocomplete="off" spellcheck="false" enterkeyhint="go"></p><p class="ln"><a class="btn" href="start.html" data-enter>봉토를 받는다 {ico("next")}</a></p></div></div><p class="hint">붉은 인장을 눌러 봉인을 떼십시오.</p><a class="seal" href="start.html" data-seal aria-label="봉인을 떼고 서임장 펼치기"><svg class="l" aria-hidden="true"><use href="#wax"/></svg><svg class="r" aria-hidden="true"><use href="#wax"/></svg></a></div></dialog>'''


def index():
    return home("index.html")


def home(filename="home.html"):
    hero = f'''<section class="landscape-hero" aria-labelledby="hero-title"><img class="hero-art" src="images/art/ern-valley.webp" alt="황금빛 들판과 강 너머, 산기슭에 자리한 변경의 성읍" width="1774" height="887" fetchpriority="high"><div class="hero-wash"></div><div class="hero-border" aria-hidden="true"></div><div class="wrap hero-inner"><div class="hero-copy"><p class="eyebrow hero-eyebrow"><span></span> A NEW LORD. AN UNWRITTEN STORY.</p><h1 id="hero-title">변경의<br>신임 영주가<br><em>되었다.</em></h1><p class="hero-desc">왕국 동쪽 끝, 이름 없는 땅 하나.<br>그곳에서 당신의 이야기가 시작됩니다.</p><div class="hero-actions"><a class="btn" href="start.html" data-open-writ>나의 서임장 펼치기 {ico("next")}</a><a class="text-link" href="world.html">세계 둘러보기 <span>↗</span></a></div></div></div><div class="hero-foot"><span class="eyebrow">KINGDOM OF ORTEN <i>·</i> EASTERN FRONTIER</span><a href="#prologue" class="scroll-cue"><span>이야기 속으로</span><span>↓</span></a><span class="hero-edition">정통 판타지 · 영지 경영</span></div></section>
<div class="chapter-ribbon"><div class="wrap"><span class="ribbon-title">THE ERN MARCH</span><span><b>12</b> 저마다의 삶</span><i>✦</i><span><b>6</b> 영지의 단계</span><i>✦</i><span><b>4</b> 흐르는 계절</span><a href="start.html">그리고, 당신 {ico("next")}</a></div></div>'''
    prologue = f'''<section class="prologue wrap" id="prologue"><div class="chapter-label"><span class="eyebrow">01 / THE PROLOGUE</span><span class="fine-line"></span></div><div class="prologue-grid"><div><h2>왕국의 끝에서,<br><em>당신의</em> 역사가 시작된다.</h2><p class="editorial-note">A land to cultivate. A story to make your own.</p></div><div class="prologue-copy">{"".join(f"<p>{e(x)}</p>" for x in d.홈_소개)}<a class="text-link" href="world.html">에른 변경에 관하여 <span>↗</span></a></div></div></section>
<section class="explore wrap" aria-label="에른 변경 둘러보기"><a class="explore-item" href="world.html"><div class="explore-picture explore-world"><img src="images/art/ern-valley.webp" alt="산과 들판이 펼쳐진 에른 변경" width="1774" height="887" loading="lazy"><span class="explore-number">I</span></div><div class="explore-caption"><div><span class="eyebrow">THE WORLD</span><h3>변경 너머의 세계</h3></div><span class="round-arrow">↗</span></div><p>숲의 경계에서 왕국의 질서까지.</p></a><a class="explore-item" href="domain.html"><div class="explore-picture explore-domain">{town()}<span class="explore-number">II</span></div><div class="explore-caption"><div><span class="eyebrow">YOUR DOMAIN</span><h3>손으로 일구는 영지</h3></div><span class="round-arrow">↗</span></div><p>땅을 일구고, 장부를 펴고, 내일을 짓는 일.</p></a><a class="explore-item" href="characters.html"><div class="explore-picture explore-people"><img src="images/c/b/1.jpg" alt="기사대장 카트린 볼크" width="1600" height="1103" loading="lazy"><span class="explore-number">III</span></div><div class="explore-caption"><div><span class="eyebrow">THE PEOPLE</span><h3>당신 곁의 열두 사람</h3></div><span class="round-arrow">↗</span></div><p>누구에게나, 당신과 다른 바람이 있습니다.</p></a></section>'''
    ticks = "".join(f'<li><button type="button" data-g="{i}">{e(stage[0])}</button></li>' for i, stage in enumerate(d.단계))
    stages = e(json.dumps([[x[0], x[1], x[3]] for x in d.단계], ensure_ascii=False))
    grow = f'''<section class="growth-chapter"><div class="wrap"><div class="section-top"><div><p class="eyebrow">02 / A LAND OF YOUR OWN</p><h2>작은 개척지에서,<br>하나의 도시로.</h2></div><p>움집과 목책이 선 자리에서 시작합니다.<br>영지의 다음 모습을 직접 펼쳐 보십시오.</p></div><div class="growth-paper"><div class="growth-note"><span>에른 변경 개발 기록</span><span class="eyebrow">THE DOMAIN ARCHIVE</span></div><div class="grow" data-grow data-stages="{stages}">{town()}<div class="g-info" aria-live="polite"><p class="eyebrow">SETTLEMENT</p><p class="g-name" data-g-name>{e(d.단계[0][0])}</p><p class="g-pop">인구 <b data-g-pop>50</b><span data-g-cap>까지</span></p><p class="g-fac" data-g-fac>{e(d.단계[0][3])}</p></div><div class="g-ctl"><input type="range" min="0" max="5" step="1" value="0" aria-label="영지 단계" data-g-range><ol class="g-ticks">{ticks}</ol></div><p class="g-win"><span data-domain>{e(d.기본_영지명)}</span> 영지의 기록 <span class="grow-hint">← 인장을 움직여 보세요 →</span></p></div></div><div class="section-after"><span>시설은 예시입니다. 무엇이든 사업을 벌여야 생깁니다.</span><a class="text-link" href="domain.html">영지의 살림 살펴보기 <span>↗</span></a></div></div></section>'''
    cards = "".join(f'''<a class="person-card" href="char/{c['코드']}.html"><div class="person-image"><img src="images/c/{c['코드']}/1.jpg" alt="{e(c['이름'])}" style="object-position:{d.인물_초점[c['코드']]}% 20%" width="1600" height="1103" loading="lazy"><span class="person-index">{i + 1:02d} / 12</span></div><div class="person-caption"><span class="person-role">{e(c['직책'])}</span><h3>{e(c['이름'])}</h3><span class="person-arrow">↗</span></div></a>''' for i, c in enumerate(d.인물))
    people = f'''<section class="people-chapter" data-gallery><div class="wrap"><div class="section-top"><div><p class="eyebrow">03 / PEOPLE OF THE MARCH</p><h2>같은 땅, 서로 다른 바람.</h2></div><a class="text-link" href="characters.html">열두 사람의 기록 <span>↗</span></a></div><p class="people-intro">충성과 계약, 이해와 갈등. 영주가 없는 동안에도 이들의 삶은 계속됩니다.</p></div><div class="people-track" id="people-gallery" data-gallery-track tabindex="0" role="region" aria-label="인물 갤러리">{cards}</div><div class="wrap gallery-bottom"><span class="eyebrow">EVERY PERSON HAS A STORY</span><div><button type="button" data-gallery-prev aria-label="이전 인물 카드">←</button><button type="button" data-gallery-next aria-label="다음 인물 카드">→</button></div></div></section>'''
    rows = "".join(f"<li>{e(t)}</li>" for t in reversed(d.태도))
    cols = "".join(f'<div class="est-col" data-k="{k}" style="--lv:2"><span class="pennant"><b>{e(name)}</b></span><small>{e(BY[rep]["이름"])}</small><em data-lv>{e(d.태도[2])}</em></div>' for k, name, _, _, rep in d.세력)
    edicts = "".join(f'<button type="button" class="edict" aria-pressed="false" data-e="{k}">{e(t)} <span>+</span></button>' for k, t, _, _ in d.칙령)
    ed_data = e(json.dumps({k: {"out": o, "fx": fx} for k, _, o, fx in d.칙령}, ensure_ascii=False))
    est = f'''<section class="estates-chapter wrap"><div class="section-top"><div><p class="eyebrow">04 / THE WEIGHT OF A DECISION</p><h2>모두를 위한 결정은<br>쉽지 않습니다.</h2></div><p>기사, 성당, 길드, 그리고 촌락.<br>당신의 결정이 네 세력의 마음을 움직입니다.</p></div><div class="est" data-est data-edicts="{ed_data}" data-levels="{e(json.dumps(d.태도, ensure_ascii=False))}"><div class="est-board"><ol class="est-rows" aria-hidden="true">{rows}</ol><div class="est-cols">{cols}</div></div><div class="est-ctl"><p class="eyebrow">ISSUE YOUR FIRST EDICT</p>{edicts}<p class="est-out" aria-live="polite" data-est-out>큰 결정은 대개 한쪽을 올리고 다른 쪽을 깎습니다.</p></div></div></section>'''
    seasons = f'''<section class="seasons-chapter wrap"><div class="section-top compact"><div><p class="eyebrow">THE TURNING YEAR</p><h2>땅은 계절을 기억합니다.</h2></div><p>계절을 고르면 이곳의 공기도 달라집니다.</p></div><div class="seasons">''' + "".join(f'<button type="button" class="season" data-season="{k}" aria-pressed="false"><span class="season-top">{ico(k)}<span class="en">{en}</span></span><b>{e(t)}</b><span class="s-d">{e(x)}</span><span class="season-check" aria-hidden="true">↗</span></button>' for k, t, en, x in d.계절) + '</div></section>'
    deeds = f'''<section class="beginnings wrap"><div class="section-top"><div><p class="eyebrow">05 / BEGIN YOUR STORY</p><h2>어떤 시작을 고르시겠습니까?</h2></div><span class="small-print">세 가지 출발. 그다음은 당신의 선택.</span></div><div class="deeds">''' + "".join(f'<a class="deed" href="start.html#{k}"><span class="deed-number">0{i + 1}</span><span class="en">{en}</span><h3>{e(t)}</h3><p>{e(a)}</p><span class="deed-link">이 시작을 고르기 {ico("next")}</span></a>' for i, (k, t, en, a, _, _) in enumerate(d.모드)) + '</div></section>'
    end = f'''<section class="night-chapter"><img src="images/art/ern-night.webp" alt="달빛 아래 등불이 켜진 변경의 마을" width="1774" height="887" loading="lazy"><div class="night-content">{emblem()}<p class="eyebrow">YOUR STORY IS STILL UNWRITTEN</p><h2><span data-domain-or="{e(d.홈_맺음)}">{e(d.홈_맺음)}</span></h2><p>이제, 첫 장을 써 내려갈 시간입니다.</p><a class="btn btn-light" href="start.html" data-open-writ>나의 서임장 펼치기 {ico("next")}</a>{crack_button()}</div></section>'''
    return shell(filename, "", hero + prologue + grow + people + est + seasons + deeds + end + writ_dialog())


def characters():
    def entry(c):
        info = {k: c.get(k, "") for k in ("이름", "직책", "나이", "호칭", "목표", "소개")}
        info["img"] = f'images/c/{c["코드"]}/1.jpg'
        info["focus"] = d.인물_초점[c["코드"]]
        return (f'<li data-g="{c["묶음"]}"><a class="ro" id="{c["코드"]}" href="char/{c["코드"]}.html" '
                f'data-c="{e(json.dumps(info, ensure_ascii=False))}"><b>{e(c["이름"])}</b><small>{e(c["직책"])}</small></a></li>')
    c0 = d.인물[0]
    filters = '<button type="button" role="tab" aria-selected="true" data-f="all">전체</button>' + "".join(
        f'<button type="button" role="tab" aria-selected="false" data-f="{k}">{e(t)}</button>' for k, t, _ in d.묶음)
    영문, 제목, 머리말 = d.인물_머리
    body = f"""<section class="select" data-select>
<div class="sel-stage"><img data-sel-img style="object-position:{d.인물_초점[c0["코드"]]}% 20%" src="images/c/{c0["코드"]}/1.jpg" alt="" width="1600" height="1103" fetchpriority="high">
<span class="plate big"><small data-f="직책">{e(c0["직책"])}</small><b data-f="이름">{e(c0["이름"])}</b></span></div>
<div class="sel-side">{hd(제목, 영문, "h1", "big")}<p class="lead">{e(머리말)}</p>
<div class="sel-f" role="tablist" aria-label="묶음">{filters}</div>
<ol class="roster">{"".join(entry(c) for c in d.인물)}</ol>
<div class="sel-info" aria-live="polite"><p data-f="소개">{e(c0["소개"])}</p>
<dl class="rec"><dt>나이</dt><dd data-f="나이">{e(c0["나이"])}</dd><dt>영주를 부르는 말</dt><dd data-f="호칭">{e(c0["호칭"])}</dd>
<dt>바라는 것</dt><dd data-f="목표">{e(c0["목표"])}</dd></dl>
<a class="btn" data-f-link href="char/{c0["코드"]}.html">기록 열람 {ico("next")}</a></div>
</div></section>"""
    return shell("characters.html", 제목, body)


def character(i):
    c = d.인물[i]
    prev, nxt = d.인물[i - 1], d.인물[(i + 1) % len(d.인물)]
    k = c["코드"]
    rec = [("나이", c["나이"]), ("직책", c["직책"]), ("영주를 부르는 말", c["호칭"]), ("말투", c["말투"]), ("바라는 것", c["목표"])]
    if c.get("질투"):
        rec.append(("질투하면", c["질투"]))
    faces = "".join(
        f'<button type="button" aria-pressed="{"true" if j == 0 else "false"}" data-src="../images/c/{k}/{num}.jpg" '
        f'data-alt="{e(c["이름"])} — {e(t)}">{e(t)}</button>' for j, (num, t) in enumerate(d.표정))
    num0, t0 = d.표정[0]
    body = f"""<section class="prof">
<div class="prof-hero"><img src="../images/c/{k}/1.jpg" alt="{e(c["이름"])}" width="1600" height="1103" fetchpriority="high">{plate(c, "big", heading=True)}</div>
<div class="wrap narrow">
<nav class="prof-nav" aria-label="다른 인물"><a data-prev href="{prev["코드"]}.html">{ico("next", "flip")}<span>{e(prev["이름"])}</span><kbd>Q</kbd></a>
<a href="../characters.html#{k}">명부</a><a data-next href="{nxt["코드"]}.html"><kbd>E</kbd><span>{e(nxt["이름"])}</span>{ico("next")}</a></nav>
<p class="prof-lead" data-rv>{e(c["소개"])}</p>
<dl class="rec" data-rv>{"".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in rec)}</dl>
</div>
<div class="wrap">{hd("표정", "EXPRESSIONS")}
<div class="faces" data-faces><div class="face-stage"><img data-face src="../images/c/{k}/{num0}.jpg" alt="{e(c["이름"])} — {e(t0)}" width="1280" height="533"></div>
<div class="face-tabs" role="group" aria-label="표정">{faces}</div></div>
</div></section>"""
    return shell("characters.html", c["이름"], body, pre="../")


def world():
    btns = "".join(f'<li><button type="button" data-r="{k}"><b>{e(이름)}</b><small>{e(방위)}</small></button></li>'
                   for k, 이름, 방위, _, _ in d.지역)
    infos = ""
    for k, 이름, 방위, 설명, rep in d.지역:
        name = f'<span data-domain>{e(d.기본_영지명)}</span>' if k == "home" else e(이름)
        who = (f'<a class="rep" href="char/{rep}.html">{plate(BY[rep])}{ico("next")}</a>' if rep else "")
        infos += (f'<article class="rg-info" data-r="{k}"{"" if k == "home" else " hidden"}><h2>{name}</h2>'
                  f'<p class="dir">{e(방위)}</p><p>{e(설명)}</p>{who}</article>')
    atlas = (f'<section class="atlas" data-atlas><div class="wrap"><div class="map-wrap">{atlas_svg()}</div>'
             f'<div class="atlas-side"><ol class="rg-list">{btns}</ol><div aria-live="polite">{infos}</div></div></div></section>')
    return shell("world.html", d.세계_머리[1], page_head(*d.세계_머리) + atlas
                 + "".join(sec(t, en, blocks(bs)) for en, t, bs in d.세계))


def domain():
    stages = table(["단계", "인구", "이 무렵의 시설"], [[s[0], s[2], s[3]] for s in d.단계])
    est = table(["세력", "쥔 것", "바라는 것", "대표"], [[이름, a, b, BY[rep]["이름"]] for _, 이름, a, b, rep in d.세력])
    rows = "".join(
        f'<tr data-v="{v}"><td>{e(t)}</td><td>{coin(v)}</td><td class="qty">'
        f'<button type="button" data-d="-1" aria-label="{e(t)} 빼기">−</button><output>0</output>'
        f'<button type="button" data-d="1" aria-label="{e(t)} 더하기">+</button></td></tr>' for t, v in d.시세)
    tally = (f'<div class="tally scroll" data-tally><table><thead><tr><th scope="col">품목</th><th scope="col">값</th>'
             f'<th scope="col">수량</th></tr></thead><tbody>{rows}</tbody><tfoot><tr><th scope="row" colspan="2">합계 '
             f'<button type="button" class="link" data-reset>지우기</button></th><td><output data-total>0동화</output></td></tr></tfoot></table></div>')
    seasons = "<dl>" + "".join(f"<dt>{e(t)}</dt><dd>{e(x)}</dd>" for _, t, _, x in d.계절) + f"</dl><p>{e(d.계절_글)}</p>"
    a, b = d.정보창.split("{영지명}")
    win = (f'<p>{e(d.정보창_글)}</p><div class="scroll"><pre>{e(a)}<span class="mine" data-domain>{e(d.기본_영지명)}</span>{e(b)}</pre></div>')
    return shell("domain.html", d.영지_머리[1], page_head(*d.영지_머리)
                 + sec("영지 단계", "STAGES", stages + "<p>시설은 예시입니다. 어느 것이든 사업을 벌여야 생깁니다.</p>")
                 + sec("살림", "LIVELIHOOD", blocks(d.살림))
                 + sec("네 세력", "FOUR ESTATES", est + blocks(d.세력_글))
                 + sec("사업", "WORKS", blocks(d.사업))
                 + sec("기준 시세", "PRICES", f"<p>{e(d.시세_글)} 수량을 눌러 셈해 볼 수 있습니다.</p>" + tally)
                 + sec("사계", "SEASONS", seasons)
                 + sec("정보창", "THE WINDOW", win))


def start():
    slots = "".join(
        f'<button type="button" role="tab" class="slot" data-m="{k}" aria-selected="{"true" if i == 0 else "false"}">'
        f'<svg class="mark" aria-hidden="true"><use href="#wax"/></svg><b>{e(t)}</b><span class="en">{en}</span></button>'
        for i, (k, t, en, *_) in enumerate(d.모드))
    panes = "".join(
        f'<article class="mode-pane" id="{k}" data-m="{k}" data-name="{e(t)}" role="tabpanel"{"" if i == 0 else " hidden"}>'
        f'<h2>{e(t)}</h2><p>{e(a)}</p><p>{e(b)}</p><p class="lv"><b>난이도</b>{e(lv)}</p></article>'
        for i, (k, t, _, a, b, lv) in enumerate(d.모드))
    modes = f'<section class="modes" data-modes><div class="wrap"><div class="slots" role="tablist" aria-label="시작 모드">{slots}</div>{panes}</div></section>'
    fields = "".join(f'<label><span>{e(t)}</span><input data-n="{e(t)}" placeholder="{e(ph)}" autocomplete="off"></label>'
                     for t, ph in d.노트_칸)
    note = (blocks(d.시작전) + f'<form class="note" data-note onsubmit="return false">'
            f'<label><span>영지 이름</span><input data-domain-input maxlength="12" placeholder="{e(d.기본_영지명)}" autocomplete="off" spellcheck="false"></label>'
            f'{fields}<p class="note-save-message">작성한 내용은 이 브라우저에 자동으로 보관됩니다.</p><pre data-note-out aria-live="polite"></pre>'
            f'<p><button type="button" class="btn" data-copy>유저노트 초안 복사</button> <span class="copied" role="status" data-copied></span></p></form>')
    return shell("start.html", d.시작_머리[1], page_head(*d.시작_머리) + modes
                 + sec("시작 전에", "BEFORE YOU BEGIN", note, id_="note")
                 + sec("플레이", "HOW IT PLAYS", blocks(d.플레이))
                 + sec("안내", "NOTICE", f"<p>{e(d.안내)}</p>{crack_button()}"))


def main():
    out = {"index.html": index(), "home.html": home(), "characters.html": characters(),
           "world.html": world(), "domain.html": domain(), "start.html": start()}
    out.update({f'char/{c["코드"]}.html': character(i) for i, c in enumerate(d.인물)})
    (ROOT / "char").mkdir(exist_ok=True)
    for name, html in out.items():
        (ROOT / name).write_text(html, encoding="utf-8", newline="\n")
    # 자가 점검: HTML·CSS·데이터가 부르는 로컬 파일이 전부 있어야 한다
    refs = set()
    for stylesheet in (ROOT / "assets/css").glob("*.css"):
        css = stylesheet.read_text(encoding="utf-8")
        for quoted, single_quoted, unquoted in re.findall(r'''url\(\s*(?:"([^"]*)"|'([^']*)'|([^\s)]+))\s*\)''', css):
            target = quoted or single_quoted or unquoted
            if not target.startswith(("data:", "http:", "https:", "#")):
                refs.add((stylesheet.parent / target.split("#")[0]).resolve())
    for name, html in out.items():
        base = (ROOT / name).parent
        refs |= {(base / m).resolve() for m in re.findall(r'(?:href|src)="([^"#:]+)"', html)}
    for c in d.인물:
        refs |= {ROOT / f'images/c/{c["코드"]}/{k}.jpg' for k in [1] + [k for k, _ in d.표정]}
        refs.add(ROOT / f'images/card/{c["코드"]}.jpg')
    missing = sorted(str(p) for p in refs if not p.exists())
    assert not missing, "없는 파일:\n" + "\n".join(missing)
    assert coin(1500) == "15금화" and coin(342) == "3금화 4은화 2동화" and coin(0) == "0동화"
    print(f"{len(out)}쪽 생성, 참조 {len(refs)}개 확인")


if __name__ == "__main__":
    main()
