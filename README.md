# 변경의 신임 영주가 되었다 — 소개 사이트

크랙 캐릭터 챗 작품 「변경의 신임 영주가 되었다」의 소개 사이트다. 새벽의 변경 풍경에서 시작해 약도, 장부, 열두 사람의 기록을 넘겨 보는 정적 사이트다.

- 사이트: https://moooncang.github.io/ern/
- 기획서: [PLAN.md](PLAN.md) — 콘셉트, 쪽별 설계, 글 원칙, 미완성 콘텐츠

## 구조

```text
index.html / home.html       같은 첫 화면: 변경 풍경과 선택형 서임장
world.html                   세계와 상호작용 약도
domain.html                  영지와 시세 계산
characters.html              인물 명부
char/a.html ~ l.html         인물 상세 12쪽
start.html                   시작 모드와 저장되는 유저노트 초안
_build/data.py               작품 설정, 글, 수치, 기존 그림 경로
_build/build.py              공통 프레임과 페이지 생성
assets/css/fonts.css         자체 호스팅 글꼴 선언
assets/css/style.css         기본 모양과 기존 상호작용 표현
assets/css/experience.css    첫 화면과 공통 프레임
assets/css/chapters.css      세계·영지·인물·시작의 상세 화면
assets/js/main.js            계절·이름·효과음·영지·지도·인물 등 핵심 동작
assets/js/experience.js      메뉴·대화상자·갤러리·읽기 진행·노트 저장
assets/fonts/                WOFF2 글꼴과 OFL 라이선스
assets/icons/ern.svg         사이트 문장 아이콘
images/art/                  새로 제작한 새벽·밤의 변경 풍경
images/card/, c/, fig/       기존 인물 그림
```

`index.html`과 `home.html`은 같은 첫 화면을 제공하며 기존 18개 HTML 경로를 유지한다. 서임장을 열지 않아도 각 쪽을 둘러볼 수 있다.

## 고치는 법

생성된 HTML은 직접 고치지 않는다. 글과 수치는 `_build/data.py`, 페이지 구조와 새 비주얼의 배치는 `_build/build.py`에서 고친다. 변경 뒤 저장소 루트에서 18쪽을 다시 생성한다.

```sh
python3 _build/build.py
```

빌더는 Python 3 표준 라이브러리만 사용한다. 페이지 생성 뒤 로컬 참조 파일과 화폐 표기를 검사하고, 문제가 있으면 실패한다. CSS와 JavaScript 파일은 직접 수정하면 되며, 해당 파일의 내용만 바꿀 때는 HTML을 다시 생성할 필요가 없다. npm이나 별도의 앱 서버, 데이터베이스는 필요 없다.

## 로컬 실행

저장소 루트에서 실행한다.

```sh
python3 -m http.server 8766 --bind 0.0.0.0
```

브라우저에서 `http://127.0.0.1:8766/`를 연다. 생성한 HTML과 필요한 파일이 모두 저장소 안에 있어 외부 글꼴 요청 없이 실행된다.

## 브라우저 검증

위 서버를 실행한 상태에서 별도 터미널로 검사한다.

```sh
python3 tests/browser_smoke.py --base-url http://127.0.0.1:8766
```

검사에는 Python `playwright` 패키지와 Chromium이 필요하다. 시스템 Chromium을 자동으로 찾으며, 다른 실행 파일을 쓰려면 `--chromium /path/to/chromium`을 지정한다. 시스템 브라우저가 없으면 Playwright에 설치된 브라우저를 사용한다. 이 도구들은 브라우저 검증용이며 일반 빌드와 사이트 실행에는 필요 없다.

검사 대상은 데스크톱·모바일의 페이지 표시와 탐색, 서임장, 계절·효과음, 인물·지도·시세·노트 상호작용이다. 공개 사이트 배포나 외부 공유 플랫폼의 미리보기는 이 검사 범위에 포함되지 않는다.

## 에셋과 라이선스

- `images/art/ern-valley.webp`와 `ern-night.webp`는 이 사이트를 위해 이미지 생성 도구로 제작한 풍경이다. 각각 1774×887이며 두 파일 합계는 약 0.6MB다. 분위기를 위한 삽화이며, 설정상의 지리 정보는 세계 쪽의 약도를 따른다.
- 기존 인물 그림은 보존했다. 새 풍경은 기존 인물의 설정이나 외형을 바꾸지 않는다.
- Gowun Batang, Nanum Myeongjo, Cormorant Garamond는 WOFF2로 자체 호스팅한다. 원본 출처와 체크섬은 [글꼴 안내](assets/fonts/README.md), 각 가족의 SIL Open Font License는 같은 폴더에 있다.
- 공유 이미지 메타데이터에는 새벽 풍경을 지정했다. 공유 플랫폼별 표시 결과는 해당 플랫폼에서 별도로 확인한다.

## 사용과 배포

화면 위의 `?` 또는 키보드 `?`로 단축키 안내를 연다. 영지 이름, 계절, 효과음 설정, 유저노트 입력과 시작 모드는 방문자의 브라우저에 저장된다. 서버나 계정에 동기화되지는 않는다.

`main`에 반영하면 기존 GitHub Pages 설정을 통해 배포된다. 로컬 변경과 테스트만으로 공개 사이트가 갱신되지는 않는다. 크랙 작품 주소는 아직 비어 있으며, `_build/data.py`의 `크랙_주소`에 실제 주소를 넣으면 작품 링크가 나타난다.
