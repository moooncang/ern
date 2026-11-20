# Pretendard Variable 1.3.9

현대적인 한글 인터페이스용 자체 호스팅 글꼴이다. 원저작자는 Kil Hyung-jin이며 SIL Open Font License 1.1로 배포된다. 전체 저작권 고지와 라이선스는 [OFL.txt](OFL.txt)에 보존했다.

- 공식 배포: [orioncactus/pretendard v1.3.9](https://github.com/orioncactus/pretendard/tree/v1.3.9/packages/pretendard/dist/web/variable/woff2-dynamic-subset)
- 로컬 출처: `moooncang/II`의 커밋 `8b125bbc3bcda2cfcc72b5113b67f1953763b3ce`, `assets/fonts/pretendard/`. WOFF2 바이너리는 수정하지 않았다.
- 92개 Unicode 부분 집합, 합계 **2,957,724바이트**. 브라우저는 표시하는 글자에 필요한 부분 집합만 내려받는다. 한국어 사용자 입력도 지원하도록 원본의 모든 부분 집합을 보존했다.
- CSS 가족명: `Pretendard Variable`. 보통체 가변 굵기 `45–920`, `font-display: swap`. 원본 CSS의 선언 범위를 그대로 사용하며 글꼴 내부 `wght` 축은 `45–930`, 기본값은 `400`이다. `400`, `500`, `600`, `700`, `800`, `900`을 사용할 수 있다.
- 선언은 `../../css/interface-fonts.css`에만 있다. 선택자나 화면 스타일은 포함하지 않으며 외부 글꼴 서버에 요청하지 않는다.
- 각 파일의 SHA-256은 [SHA256SUMS](SHA256SUMS)에 있다. 부분 집합 91은 공식 v1.3.9 배포 파일과 해시가 동일함을 확인했다. CSS의 `@font-face` 선언은 URL을 로컬 경로로 바꾼 것 외에 공식 v1.3.9 선언과 동일하다.
- 가변 굵기 `400`, `600`, `800`, `900`을 Chromium에서 불러오는 검사를 통과했다. 제목·인물명·숫자 표본에는 8개 부분 집합, 210,196바이트가 필요했다. 이 값은 실제 페이지 전체의 전송량과 다를 수 있다. 본문에 사용된 한글은 모두 포함하며, `−`, `⌛`, `└` 같은 일부 기호는 지정한 시스템 대체 글꼴이 표시한다.

기존 명조 글꼴은 별도 `fonts.css`에서 선언한다. 새 화면의 글꼴 선택과 대체 글꼴 지정은 인터페이스 스타일시트가 담당한다.
