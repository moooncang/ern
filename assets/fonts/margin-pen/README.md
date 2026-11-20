# ERN Margin Pen

영주가 남긴 짧은 여백 메모 네 줄에만 쓰는 손글씨 글꼴이다. 원본 **Nanum Pen Script**의 글자 모양과 간격을 유지하고 필요한 문자만 WOFF2로 묶었다. 본문 글꼴을 대체하지 않는다.

- 원본: [Google Fonts / NanumPenScript-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/nanumpenscript/NanumPenScript-Regular.ttf), 내부 버전 `1.10`.
- 원저작권: © 2010 NHN Corporation. Font designed by Sandoll Communications Inc.
- 라이선스: [SIL Open Font License 1.1](OFL.txt). 원본의 `Nanum`, `NanumPen` 등은 Reserved Font Name이므로 수정된 부분 집합의 내부 가족명·전체명·PostScript명을 **ERN Margin Pen**으로 변경했다. 원저작권과 OFL 고지는 그대로 보존했다.
- 수정 범위: 이름 변경, 문자 부분 집합, WOFF2 압축. 윤곽선·굵기·폭·간격은 수정하지 않았다.
- CSS 가족명: `ERN Margin Pen`, 보통체 `400`. 실제 글자 몸체가 작으므로 화면에서는 약 `24–25px`을 권장한다.
- 파일: `ern-margin-pen.woff2`, **21,148바이트**, 126 Unicode 문자. `U+0020–U+007E`의 출력 가능한 ASCII와 아래 네 문장의 한글을 포함한다.

지원하는 메모:

1. 우물과 곳간부터 확인.
2. 세금을 올리면 촌락이 반발.
3. 가을 공납 몫은 따로.
4. 서쪽 통행세 확인.

새 한글 메모를 추가하면 원본에서 해당 글자를 포함해 부분 집합을 다시 생성해야 한다. 현재 없는 글자는 CSS의 대체 글꼴로 표시된다. `assets/css/margin-font.css`는 이 부분 집합의 `@font-face`와 정확한 `unicode-range`만 선언하며 외부 서버를 요청하지 않는다.

가공에는 fontTools `subset`과 Brotli를 사용했다. 원본의 모든 name 레코드와 언어를 보존하되 가족명을 나타내는 name ID `1, 2, 3, 4, 6, 16, 17, 18, 21, 22`를 새 이름과 `Regular`로 바꿨다. 모든 지원 문자가 출력 글꼴의 cmap에 포함되는지 확인했으며 Chromium에서 네 문장의 렌더링을 확인했다.

SHA-256:

```text
6f0d1ab29c7894010dc88831fb7a0a51edb79136e450344183de5b1a8b52bd43  NanumPenScript-Regular.ttf
30e70896b75fd857f3545504441f1d09f8f5e672751c35def7b65ae57d4fc027  ern-margin-pen.woff2
```
