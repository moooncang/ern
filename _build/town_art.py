"""Small fountain-pen stage studies; the existing slider owns stage state."""


def town_art(pre=""):
    """Use the existing .st/data-s/.on hooks without changing text or controls.

    main.js marks every stage up to the current one .on. The stylesheet shows
    only the last such sketch from the six-cell transparent sprite.
    """
    stages = "".join(
        f'<span class="st{" on" if stage == 0 else ""}" data-s="{stage}" '
        f'aria-hidden="true" style="--sketch-x:{stage % 3 * 50}%;--sketch-y:{stage // 3 * 100}%"></span>'
        for stage in range(6)
    )
    return (
        '<div class="town town-art" role="img" '
        'aria-label="영지가 단계마다 자라는 그림">'
        f'{stages}</div>'
    )
