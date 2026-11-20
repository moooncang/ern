"""Illustrated settlement growth; the existing slider owns stage state."""

from html import escape


TOWN_IMAGES = tuple(f"images/atelier/town-{stage}.webp" for stage in range(6))


def town_art(pre=""):
    """Use the existing .st/data-s/.on hooks without changing text or controls.

    main.js marks every stage up to the current one .on. The stylesheet shows
    only the last such image, cross-fading complete architectural illustrations.
    """
    stages = "".join(
        f'<img class="st{" on" if stage == 0 else ""}" data-s="{stage}" '
        f'src="{escape(pre + path, quote=True)}" alt="" aria-hidden="true" '
        'width="1774" height="887" loading="lazy" decoding="async">'
        for stage, path in enumerate(TOWN_IMAGES)
    )
    return (
        '<div class="town town-art" role="img" '
        'aria-label="영지가 단계마다 자라는 그림">'
        f'{stages}</div>'
    )
