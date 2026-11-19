"""data.py를 읽어 사이트 루트에 HTML을 찍는다.  실행: python _build/build.py"""
import re
from html import escape as e
from pathlib import Path

import data as d

ROOT = Path(__file__).resolve().parent.parent
FONTS = ("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600"
         "&family=Gowun+Batang:wght@400;700&family=Nanum+Myeongjo:wght@400;700;800&display=swap")
WAX = """<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="wax" viewBox="0 0 100 100">
<path fill="#8f2020" d="M50 3c9-2 15 5 23 7s17 2 20 11-2 15 0 23 6 16 2 24-13 8-18 15-8 14-17 15-14-6-22-7-18 1-23-7 0-16-3-24-9-14-6-23 12-10 18-16S41 5 50 3z"/>
<circle cx="50" cy="50" r="32" fill="#a12a26"/><circle cx="50" cy="50" r="32" fill="none" stroke="#6f1616" stroke-width="1.5"/>
<path fill="#7a1a1a" d="M50 24c6 4 8 9 5 13 7-1 11 4 7 10 7 0 9 7 3 12 5 3 4 10-3 12 1 6-5 10-12 8-7 2-13-2-12-8-7-2-8-9-3-12-6-5-4-12 3-12-4-6 0-11 7-10-3-4-1-9 5-13z"/>
<path stroke="#a12a26" stroke-width="1.6" stroke-linecap="round" fill="none" d="M50 31v46M50 44l-7-5M50 44l7-5M50 56l-9-5M50 56l9-5M50 67l-7-4M50 67l7-4"/>
</symbol></svg>"""


def shell(파일, 머리제목, 본문, cover=False):
    title = d.제목 if not 머리제목 else f"{머리제목} · {d.제목}"
    tabs = "".join(
        '<a href="{}"{}><kbd>{}</kbd>{}</a>'.format(h, ' aria-current="page"' if h == 파일 else "", i, e(t))
        for i, (h, t) in enumerate(d.메뉴, 1))
    foot = "".join(f'<a href="{h}">{e(t)}</a>' for h, t in d.메뉴)
    top = "" if cover else (
        f'<header class="top"><div class="wrap"><a class="brand" href="home.html">{e(d.제목)}</a>'
        f'<nav class="tabs" aria-label="주 메뉴">{tabs}</nav></div></header>')
    bottom = "" if cover else (
        f'<footer class="foot"><div class="wrap"><p class="label">{e(d.영문)}</p>'
        f'<nav aria-label="바닥글">{foot}</nav></div></footer>')
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(d.소개)}">
<meta property="og:title" content="{e(d.제목)}">
<meta property="og:description" content="{e(d.소개)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#f6ecd6">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body{' class="cover"' if cover else ''}>
{top}
<main>
{본문}
</main>
{bottom}
<script src="assets/js/main.js"></script>
</body>
</html>
"""


def block(b):
    kind, *v = b
    if kind == "p":
        return f"<p>{e(v[0])}</p>"
    if kind == "dl":
        return "<dl>" + "".join(f"<dt>{e(t)}</dt><dd>{e(x)}</dd>" for t, x in v[0]) + "</dl>"
    if kind == "table":
        head = "".join(f'<th scope="col">{e(h)}</th>' for h in v[0])
        rows = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in v[1])
        return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    if kind == "pre":
        return f'<div class="scroll"><pre>{e(v[0])}</pre></div>'
    raise ValueError(f"모르는 블록: {kind}")


def head(label, 제목, 머리말, 추가=""):
    return (f'<section class="head"><div class="wrap"><p class="label">{e(label)}</p>'
            f'<h1>{e(제목)}</h1><p class="lead">{e(머리말)}</p>{추가}</div></section>')


def section(label, 제목, 안, 좁게=True):
    return (f'<section class="sec"><div class="wrap{" narrow" if 좁게 else ""}">'
            f'<p class="label">{e(label)}</p><h2>{e(제목)}</h2>{안}</div></section>')


def card(코드, 이름, 직책):
    return (f'<img src="images/card/{코드}.jpg" alt="{e(이름)}, {e(직책)}" '
            f'width="960" height="662" loading="lazy" decoding="async">')


def crack_button():
    return f'<p><a class="btn" href="{e(d.크랙_주소)}">크랙에서 시작하기</a></p>' if d.크랙_주소 else ""


def index():
    lines = "".join(f"<p>{e(x)}</p>" for x in d.칙서)
    return shell("index.html", "", f"""{WAX}
<div class="writ">
  <p class="label">{e(d.칙서_라벨)}</p>
  <h1>{e(d.제목)}</h1>
  <div class="writ-body"><div>{lines}<p>영지의 이름 <span class="blank"></span></p></div></div>
  <p class="hint"><span class="a">인장을 눌러 봉인을 뗍니다</span><span class="b">한 번 더 누르면 들어갑니다</span></p>
  <a class="seal" href="home.html" data-seal aria-label="봉인을 떼고 들어가기"><svg class="l"><use href="#wax"/></svg><svg class="r"><use href="#wax"/></svg></a>
</div>""", cover=True)


def home():
    everyone = [c for _, _, people in d.인물 for c in people]
    strip = "".join(f'<a href="characters.html">{card(*c)}</a>' for c in everyone)
    tiles = "".join(
        f'<a class="tile" href="{h}"><p class="label">{e(lb)}</p><h3>{e(t)}</h3><p>{e(x)}</p></a>'
        for h, lb, t, x in d.홈_문서)
    return shell("home.html", "", (
        head(d.영문, d.제목, d.장르, f'<p><span class="adult">19+</span></p>{crack_button()}')
        + section("THE WRIT", "칙서", "".join(f"<p>{e(x)}</p>" for x in d.홈_소개))
        + f'<section class="sec"><div class="wrap"><p class="label">HOUSEHOLD</p><h2>사람들</h2></div>'
          f'<div class="strip" tabindex="0" role="region" aria-label="인물 카드">{strip}</div></section>'
        + section("THE PAPERS", "문서 묶음", f'<div class="tiles">{tiles}</div>', 좁게=False)
        + f'<section class="sec end"><div class="wrap"><p class="closing">{e(d.홈_맺음)}</p>{crack_button()}</div></section>'))


def characters():
    groups = "".join(
        section(lb, 이름, '<div class="cards">' + "".join(card(*c) for c in people) + "</div>", 좁게=False)
        for 이름, lb, people in d.인물)
    return shell("characters.html", d.인물_머리[1], head(*d.인물_머리) + groups)


def text_page(파일):
    label, 제목, 머리말, secs = d.페이지[파일]
    body = head(label, 제목, 머리말) + "".join(
        section(lb, t, "".join(block(b) for b in blocks)) for lb, t, blocks in secs)
    return shell(파일, 제목, body)


def main():
    out = {"index.html": index(), "home.html": home(), "characters.html": characters()}
    out.update({f: text_page(f) for f in d.페이지})
    for name, html in out.items():
        (ROOT / name).write_text(html, encoding="utf-8", newline="\n")
    # 자가 점검: 메뉴가 가리키는 페이지와 HTML·CSS가 부르는 로컬 파일이 전부 있어야 한다
    css = (ROOT / "assets/css/style.css").read_text(encoding="utf-8")
    refs = {(ROOT / "assets/css" / m).resolve() for m in re.findall(r"url\(([^)]+)\)", css)}
    for html in out.values():
        refs |= {ROOT / m for m in re.findall(r'(?:href|src)="([^"#:]+)"', html)}
    missing = sorted(str(p) for p in refs if not p.exists())
    assert not missing, "없는 파일:\n" + "\n".join(missing)
    print(f"{len(out)}쪽 생성, 참조 {len(refs)}개 확인")


if __name__ == "__main__":
    main()
