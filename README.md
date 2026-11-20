# 변경의 신임 영주가 되었다 — 소개 사이트

크랙 캐릭터 챗 작품 「변경의 신임 영주가 되었다」의 소개 사이트다.

- 사이트: https://moooncang.github.io/ern/
- 기획서: [PLAN.md](PLAN.md) — 컨셉, 쪽별 설계, 글 원칙, 아직 비어 있는 것

## 폴더

```
index.html              입장(서임장)
home.html               첫 화면
world.html              세계
domain.html             영지
characters.html         인물 고르는 화면
char/a.html ~ l.html    인물 상세 12쪽
start.html              시작
assets/css/style.css    모양
assets/js/main.js       동작
images/                 변환한 그림(JPG)
_build/data.py          글과 경로 전부
_build/build.py         쪽을 찍어 내는 스크립트
```

## 고치는 법

HTML은 직접 고치지 않는다. 메뉴와 바닥글이 쪽마다 겹치므로 스크립트가 18쪽을 한 번에 다시 찍는다.

1. 글, 수치, 그림 경로는 `_build/data.py`에서 고친다
2. 사이트 폴더에서 다시 찍는다

```
python _build/build.py
```

3. `main`에 푸시하면 GitHub Pages에 반영된다

`build.py`는 파이썬 기본 기능만 쓴다. 다 찍은 뒤 쪽과 CSS가 가리키는 파일이 실제로 있는지 검사하고, 없으면 멈춘다.

모양은 `assets/css/style.css`, 동작은 `assets/js/main.js`에서 고친다. 이 둘은 다시 찍지 않아도 된다.

## 미리 보기

```
python -m http.server 8765
```

브라우저에서 `http://localhost:8765/`를 연다.

## 원래 기획을 유지한 디자인 보강

문구와 쪽 구성, 인물 구도는 `PLAN.md`를 기준으로 유지한다. `assets/css/materials.css`는 기본 재질, `craft.css`는 내부 화면의 마감·정렬·반응형 배치, `entry.css`는 봉투와 서임장의 표현을 담당한다.

- `images/ui/wax-seal.webp`: 기존 참나무잎 문양으로 제작한 투명 밀랍 에셋. 봉투 봉인과 명부·문서의 인장에 사용한다.
- `images/ui/envelope.webp`, `letter-sheet.webp`: 접힌 덮개·금박·종이 두께를 표현한 봉투와 서임장 이미지. 봉인을 떼면 덮개가 열리고 서임장이 나타난다.
- `images/ui/leather-plate.webp`, `banner-cloth.webp`: 인물·영지 명패와 세력 깃발에 사용하는 가죽·직물 이미지.
- `images/ui/parchment.webp`: 기존 양피지 색 위에 약하게 적용하는 종이결.
- `_build/engraving.py`: 기존 지도·영지 SVG에 더하는 세부 판화선. 설정·지역·성장 단계는 바꾸지 않는다.
- `assets/css/fonts.css`, `assets/fonts/`: 원래 세 글꼴과 두께를 그대로 자체 호스팅한다. OFL 라이선스와 출처는 해당 폴더에 있다.

입장 화면은 320px 모바일부터 가로 화면까지 중앙에 정렬하며, 열린 서임장이 화면보다 길면 세로로 스크롤된다. 키보드로 봉인을 열 수 있고, 이름 입력 중 Enter를 누르면 확인 버튼으로 이동한다. 동작 줄이기 설정도 따른다.

원문·기획 보존 검사는 `python3 tests/preserve_plan.py`로 실행한다. 미리 보기 서버와 Playwright·Chromium을 준비하면 `python3 tests/original_smoke.py --base-url http://127.0.0.1:8766/`으로 18쪽의 기능과 입장 화면의 정렬·키보드 동작을 확인할 수 있다.
