"""Fine engraved details for the existing town and atlas illustrations.

These overlays add surface marks only. Coordinates follow build.py's existing
silhouettes; they do not define new buildings, regions, terrain, or labels.
"""

from math import cos, pi, sin
import random


def _n(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _path(commands):
    # Match the existing town's normalized stroke-drawing animation.
    return f'<path pathLength="1" fill="none" d="{commands}"/>'


def _window(x, y, width=5, height=8):
    """Small arched opening, wholly inside an existing wall."""
    return _path(
        f"M{_n(x)} {_n(y + height)}V{_n(y + 2)}"
        f"q{_n(width / 2)} -4 {_n(width)} 0V{_n(y + height)}z"
        f"M{_n(x + width / 2)} {_n(y)}v{_n(height)}"
    )


def town_details():
    """Return six decorative stage groups for the 800×340 town SVG.

    Append after the existing silhouettes, inside the existing wob filter group.
    Existing .st/data-s behavior controls when each detail appears. The drawing
    CSS must set .town .engraving path { fill: none; stroke-width: .65; } so the
    original generic .town path fill rule cannot turn hatching into solid forms.
    """
    stage = [[] for _ in range(6)]

    # Thatched roofs on the three existing shelters. All marks stay above the
    # fence and inside each triangular roof; the entrance remains untouched.
    stage[0].append(_path(
        "M369 274l6 -10M373 280l9 -15M379 283l7 -12"
        "M412 274l10 -17M417 280l8 -14M432 267l9 15"
        "M469 279l7 -12M475 282l6 -11M481 284l5 -8"
    ))
    stage[0].append(_path(
        "M339 283v5M351 281v7M363 283v5M387 282v6"
        "M459 282v6M483 282v6M507 281v7M519 283v5"
    ))

    # The farmhouse, well, granaries, and mill already belong to stage one.
    stage[1].append(_path(
        "M256 257l17 -11M266 258l14 -9M279 258l8 -5"
        "M254 263h42M254 278h11M286 278h10"
        "M310 280h18M310 285h18M316 278v3M323 282v3"
        "M545 265l15 -13M555 265l12 -10M570 265l6 -5"
        "M598 266l12 -12M608 267l10 -10M620 267l5 -4"
        "M652 273h20M651 282h8M665 282h9"
    ))
    stage[1].extend((_window(256, 267), _window(286, 267),
                     _window(547, 273), _window(571, 273),
                     _window(599, 275, 4, 6), _window(622, 275, 4, 6),
                     _window(659, 252, 6, 10)))

    # Church and stalls: restrained roof hatching and narrow openings.
    stage[2].append(_path(
        "M101 253l15 -13M111 253l11 -10M125 253l7 -6"
        "M98 259h40M145 227h14M145 251h14M145 275h14"
        "M170 267h31M176 263v4M184 263v4M193 263v4"
        "M213 269h27M218 266v3M225 266v3M233 266v3"
        "M706 261l17 -8M716 261l11 -5M729 261l7 -3"
        "M704 267h42M738 244h4M738 250h4"
    ))
    stage[2].extend((_window(101, 265, 5, 10), _window(129, 265, 5, 10),
                     _window(149, 233, 6, 11), _window(149, 258, 6, 10),
                     _window(706, 272), _window(737, 272)))

    # Existing barracks and hall; wall masonry avoids the central gate.
    stage[3].append(_path(
        "M478 232l22 -14M490 232l17 -10M506 232l11 -7"
        "M475 239h54M475 260h18M513 260h16"
        "M579 249l21 -4M591 250l16 -3M613 248l16 -2"
    ))
    stage[3].extend(_window(x, 246, 6, 10) for x in (479, 489, 510, 520))
    # The wall lies behind its four existing towers and the stage-four gatehouse.
    for left, right in ((73, 247), (283, 369), (431, 517), (553, 727)):
        stage[3].append(_path(f"M{left} 314H{right}M{left} 324H{right}"))
        stage[3].append(_path("".join(
            f"M{x} 306v8M{x + 9} 315v9" for x in range(left + 6, right - 12, 24)
        )))
    for x in (40, 250, 520, 730):
        stage[3].extend((_window(x + 12, 287, 6, 10),
                         _path(f"M{x + 4} 311h22M{x + 4} 323h22"
                               f"M{x + 10} 312v10M{x + 20} 324v5")))

    # Cathedral roof/twin towers, domed hall, and existing central gatehouse.
    # Roof marks stop above the foreground shelters rather than crossing them.
    stage[4].append(_path(
        "M369 210l27 -17M382 211l22 -14M398 212l14 -10"
        "M415 213l9 -6M343 181h16M441 181h16"
        "M343 205h16M441 205h16M343 226h8M450 226h7"
        "M181 238h60M185 232q26 -30 52 0M211 216v19"
        "M376 278h48M376 299h48M376 313h6M418 313h6"
        "M377 325h5M418 325h5"
    ))
    stage[4].extend((_window(347, 186, 7, 12), _window(445, 186, 7, 12),
                     _window(182, 245, 7, 9), _window(194, 245, 7, 9),
                     _window(222, 245, 7, 9), _window(234, 245, 7, 9),
                     _window(380, 283, 7, 11), _window(396, 283, 7, 11),
                     _window(412, 283, 7, 11)))

    # Windows high on the already-defined distant spires and the two tiny
    # foreground houses. No new skyline or city silhouette is introduced.
    for x, height in ((58, 150), (124, 176), (296, 162),
                      (566, 184), (628, 150), (742, 170)):
        y = 290 - height
        stage[5].extend((_window(x + 5, y + 8, 4, 10),
                         _window(x + 5, y + 28, 4, 10),
                         _path(f"M{x + 3} {y + 23}h8")))
    stage[5].append(_path(
        "M6 316l9 -8M14 316l5 -5M6 321h5v6H6z"
        "M772 318l8 -7M780 318l5 -4M772 323h5v5h-5z"
    ))
    return "".join(
        f'<g class="st engraving" data-s="{i}" aria-hidden="true" '
        f'pointer-events="none">{"".join(details)}</g>'
        for i, details in enumerate(stage)
    )


def atlas_details():
    """Return decorative marks for the existing 900×560 atlas SVG.

    Append before </svg>. Compass/frame ornament and hatching remain inside the
    current motifs. No labels, geography, interactive regions, or paths move.
    """
    details = []

    # Etched corner turns repeat the existing rectangular document frame.
    corner = _path("M0 26V0h26M5 21V5h16M0 13h5M13 0v5M0 0l5 5")
    for x, y, sx, sy in ((24, 24, 1, 1), (876, 24, -1, 1),
                         (24, 536, 1, -1), (876, 536, -1, -1)):
        details.append(f'<g transform="translate({x} {y}) scale({sx} {sy})">{corner}</g>')

    # Small graduation cuts fit between the compass's existing r=26 and r=34
    # rings; the north label and four-point star are left as originally drawn.
    ticks = []
    for i in range(32):
        angle = i * pi / 16
        inner = 28 if i % 4 == 0 else 30
        ticks.append(
            f"M{_n(inner * cos(angle))} {_n(inner * sin(angle))}"
            f"L{_n(33 * cos(angle))} {_n(33 * sin(angle))}"
        )
    details.append('<g transform="translate(96 96)">' + _path("".join(ticks)) +
                   _path("M0 -28V-9M28 0H9M0 28V9M-28 0H-9") + '</g>')

    # Mirror only the already-existing mountain coordinates and sizes. Each
    # short hatch lies within a mountain's left face, clear of nearby labels.
    for x, y, scale in ((626, 452, 1), (668, 440, 1.3), (716, 452, 1.1),
                         (760, 444, .9), (690, 470, .8), (738, 474, .9),
                         (646, 478, .7)):
        details.append(
            f'<g transform="translate({x} {y}) scale({scale})">' +
            _path("M-12 -4l8 -14M-7 -3l7 -13M-2 -3l4 -9") + '</g>'
        )

    # Use the same deterministic placement as the forest's original glyph.
    # These are strokes inside its 26 existing triangular tree crowns.
    rng = random.Random(11)
    for _ in range(26):
        x = 676 + rng.uniform(-118, 118)
        y = 118 + rng.uniform(-58, 50)
        details.append(_path(f"M{_n(x - 2.5)} {_n(y - 7)}"
                             f"l2 -6M{_n(x + .5)} {_n(y - 7)}l1.2 -3"))

    return ('<g class="engraving atlas-engraving" aria-hidden="true" '
            'pointer-events="none" fill="none">' + "".join(details) + '</g>')
