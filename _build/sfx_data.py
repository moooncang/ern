"""Short material sounds. The legacy names match the existing interaction calls."""


def clips(stem, count):
    return [f"audio/sfx/{stem}-{number}.wav" for number in range(1, count + 1)]


EFFECTS = {
    "tick": {"files": clips("select", 2), "gain": .40, "minGap": 90},
    "page": {"files": clips("paper-turn", 3), "gain": .65, "minGap": 120},
    "stamp": {"files": clips("seal-press", 2), "gain": .70, "minGap": 160},
    "crack": {"files": clips("wax-break", 2), "gain": .80, "minGap": 240},
    "quill": {"files": clips("pen-stroke", 3), "gain": .38, "minGap": 220},
    "chime": {"files": clips("folio-shift", 2), "gain": .60, "minGap": 180},
}
