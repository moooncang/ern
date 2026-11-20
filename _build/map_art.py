"""Illustrated atlas layers; all region coordinates and live controls stay intact."""

REGION_POSITIONS = {
    "home": ("0%", "13.636364%"),
    "seril": ("50%", "13.636364%"),
    "kardun": ("100%", "13.636364%"),
    "waste": ("0%", "86.363636%"),
    "reibek": ("50%", "86.363636%"),
    "haster": ("100%", "86.363636%"),
}


def illustrated_map(svg):
    """Place the illustrated survey beneath the original SVG controls/routes."""
    svg = svg.replace('class="map"', 'class="map map-illustrated"', 1)
    end = svg.index(">") + 1
    art = ('<image class="survey-art" href="images/atelier/map-survey.webp" '
           'x="0" y="0" width="900" height="560" preserveAspectRatio="none" '
           'aria-hidden="true" pointer-events="none"/>')
    return svg[:end] + art + svg[end:]


def region_art(key):
    """A decorative landscape accompanying the region's unchanged written record."""
    x, y = REGION_POSITIONS[key]
    return (f'<div class="region-illustration" aria-hidden="true" '
            f'style="--region-x:{x};--region-y:{y}"></div>')
