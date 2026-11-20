# Self-hosted fonts

The original serif families below were downloaded from the official Google Fonts repository and losslessly packaged as WOFF2 with fontTools. No glyphs were removed. Each family retains its SIL Open Font License below.

- `gowun-batang-regular.woff2`: [GowunBatang-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/gowunbatang/GowunBatang-Regular.ttf); source SHA-256 `466c593e7147412e748af4856d5ad14709b5a860bdf62b9c2546f2c5874e9849`.
- `gowun-batang-bold.woff2`: [GowunBatang-Bold.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/gowunbatang/GowunBatang-Bold.ttf); source SHA-256 `dbfcaa646e5831e7478524924f02906f550285a5050699b4e38c9950b3ec4b94`.
- `nanum-myeongjo-extrabold.woff2`: [NanumMyeongjo-ExtraBold.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/nanummyeongjo/NanumMyeongjo-ExtraBold.ttf); source SHA-256 `60c0077fce069ba90ae97c0a3679f6eb3712e0ca637bdd0c15b72d335ec46db7`.
- `cormorant-garamond.woff2`: [CormorantGaramond[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf); source SHA-256 `b20b7d9626dd956b2c5e558692ad328b1f19e3275e2782db4fa07670d83f35e0`.
- `cormorant-garamond-italic.woff2`: [CormorantGaramond-Italic[wght].ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf); source SHA-256 `0f48ea6abb2084537854f7174c470991a463b13036309e3b50a81511611c530d`.
- `nanum-myeongjo-regular.woff2`: [NanumMyeongjo-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/nanummyeongjo/NanumMyeongjo-Regular.ttf); source SHA-256 `7ed9e8653a8ed04285d51dc343ffea6eb3d9c73afc27383ea8929ee4ffd03205`.
- `nanum-myeongjo-bold.woff2`: [NanumMyeongjo-Bold.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/nanummyeongjo/NanumMyeongjo-Bold.ttf); source SHA-256 `bc9ed8e60d93fe6db054b8fb988481b625f2eef8cb2317ad0e9834681b8fe3f3`.

The modern interface uses [Pretendard Variable 1.3.9](pretendard/README.md), preserved as 92 upstream Unicode subsets (2,957,724 bytes). Its license, provenance, weight range, and checksums are documented in that directory. `assets/css/interface-fonts.css` declares the family with local URLs and `font-display: swap`; page styles select it separately.

The four handwritten margin notes use [ERN Margin Pen](margin-pen/README.md), a renamed, 21,148-byte subset of Nanum Pen Script under the SIL Open Font License. Its reserved font names were replaced in the derivative; original copyright and license notices are preserved. `assets/css/margin-font.css` declares only this notes font.
