"""Annotated ink studies; image handwriting is also described for screen readers."""

from html import escape


STUDIES = (
    ("개척지", ("기둥은 깊게", "이음새 재확인", "목책 간격 좁게", "빗물 길을 낼 것")),
    ("촌락", ("우물 깊이 확인", "밧줄 마모 점검", "손잡이 축 보강", "곳간은 습기 주의")),
    ("마을", ("장터 동선 확인", "화덕 곁은 비워 둘 것", "풀무 연결부 점검", "기둥 이음 보강")),
    ("성읍", ("문짝 무게 분산", "쇠사슬 마모 확인", "권양 축 점검", "수비 동선 확보")),
    ("도시", ("지붕 하중 분산", "들보 이음 확인", "통로 폭 유지", "공사 순서 재검토")),
    ("대도시", ("성문 위치 확인", "모서리 기둥 보강", "빈 공간은 남길 것", "동선 다시 그릴 것")),
)


def town_art(pre=""):
    """Use the existing .st/data-s/.on hooks without changing text or controls.

    main.js marks every stage up to the current one .on. The stylesheet shows
    only the last study, including its four painted handwriting clusters.
    """
    stages = "".join(
        f'<span class="st{" on" if stage == 0 else ""}" data-s="{stage}" '
        f'data-caption="{escape(name + " 구조도. " + ". ".join(notes) + ".", quote=True)}" '
        f'aria-hidden="true" style="--sketch-x:{stage % 3 * 50}%;--sketch-y:{stage // 3 * 100}%"></span>'
        for stage, (name, notes) in enumerate(STUDIES)
    )
    return (
        '<div class="town town-art" role="img" '
        'aria-label="영지가 단계마다 자라는 그림">'
        f'{stages}</div>'
    )
