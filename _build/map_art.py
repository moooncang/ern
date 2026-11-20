"""Compact region symbols layered under the original live map controls."""

REGIONS = {
    "home": (0, 0, 450, 292),
    "seril": (1, 0, 676, 122),
    "kardun": (2, 0, 700, 448),
    "waste": (0, 1, 800, 290),
    "reibek": (1, 1, 206, 272),
    "haster": (2, 1, 232, 452),
}
SPRITE = "images/modern/region-pen.webp"


def symbol_svg(key, *, x=0, y=0, size=128):
    col, row, _, _ = REGIONS[key]
    return (f'<svg class="region-symbol-art" x="{x}" y="{y}" width="{size}" height="{size}" '
            f'viewBox="{col * 512} {row * 512} 512 512" aria-hidden="true" '
            f'overflow="hidden" pointer-events="none">'
            f'<image href="{SPRITE}" x="0" y="0" width="1536" height="1024"/></svg>')


def illustrated_map(svg):
    """The original labels, routes and hit areas remain the interaction layer."""
    svg = svg.replace('class="map"', 'class="map map-modern"', 1)
    end = svg.index(">") + 1
    art = ['<g class="modern-map-field" aria-hidden="true" pointer-events="none">',
           '<rect class="map-field" x="0" y="0" width="900" height="560" rx="22"/>',
           '<g class="map-contours"><path d="M73 159l19-13 17-8 23-16 26-9 34-3 28 2 19 5 24 12 18 12 15 15 14 8 17 4 16-1 13-7 19-12 15-18 19-15 27-8 24-3"/>',
           '<path d="M366 439l17 6 18 2 21-1 16-5 21-11 16-7 19-10 21-4 19 1 21 4 18 8 20 11 17 5 18 2 23-2 17-5"/></g>',
           '<path class="modern-north" d="M96 110V70m-6 8 6-8 6 8"/>', '</g>']
    for key, (_, _, x, y) in REGIONS.items():
        cy = y - 24
        art.append(f'<g class="region-marker" data-r="{key}" aria-hidden="true" pointer-events="none">'
                   f'<circle class="node-halo" cx="{x}" cy="{cy}" r="57"/>'
                   f'{symbol_svg(key, x=x - 64, y=cy - 64)}</g>')
    return svg[:end] + "".join(art) + svg[end:]


def region_art(key):
    """One small symbol in each record; the previous landscape panel is gone."""
    return f'<div class="region-symbol" aria-hidden="true">{symbol_svg(key, size=76)}</div>'
