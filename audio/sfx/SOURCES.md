# ERN material sound effects

The site uses 14 short edits of recorded material sounds. They replace the
previous oscillator/white-noise effects. No dialogue or music is included.

## Oculus Audio Pack 01

"Oculus Audio Pack 01" by Oculus VR, LLC
(https://developers.meta.com/vr/downloads/package/oculus-audio-pack-1/),
licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Files renamed to the UCS naming convention; OGG previews transcoded from the original WAVs.

Copyright © 2015 Oculus VR, LLC. The license text is included in
[CC-BY-4.0.txt](CC-BY-4.0.txt).

Source archive: [Meta Open Sound, Oculus Audio Pack](https://github.com/facebookincubator/Meta-open-sound/tree/514c926efecdb3c7812bf00eedf8e5c8d61dd681/corpora/oculus-audio-pack).

ERN adaptations: short excerpts, mono conversion, modest playback-rate changes,
layering, high/low-pass filtering, short fades and level matching. The wax and
seal sounds are designed composites of paper and wood recordings; they are
not recordings of an actual wax seal.

| Site files | Source recordings |
| --- | --- |
| `select-1/2.wav` | `UIClick_WoodBack_OS_01`, `UIClick_WoodConfirm_OS_01` |
| `paper-turn-1/2/3.wav` | `PAPRHndl_BookPageTurns_OS_01` |
| `seal-press-1/2.wav` | `OBJBook_BookClose_OS_01`, `WOODImpt_LargeWoodDrop_OS_01`, `UIClick_WoodConfirm_OS_01` |
| `wax-break-1/2.wav` | `PAPRRip_PaperTear_OS_01`, `PAPRHndl_PaperCrumple_OS_01`, `UIClick_WoodBack_OS_01` |
| `folio-shift-1/2.wav` | `OBJBook_BookOpen_OS_01`, `OBJBook_BookOpen_OS_02` |

## Pencil, Writing, Close, A

"[Pencil, Writing, Close, A](https://freesound.org/people/InspectorJ/sounds/398271/)"
by [InspectorJ](https://freesound.org/people/InspectorJ/), licensed under
[CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).
The license text is included in [CC-BY-3.0.txt](CC-BY-3.0.txt).

Source copy distributed by [Rnote](https://github.com/flxzt/rnote/tree/main/crates/rnote-engine/data/sounds),
with its original sound attribution preserved in `_build/sfx_sources/RNOTE-LICENSES.md`.

`pen-stroke-1/2/3.wav` use three separate short excerpts from that close pencil
recording. ERN adaptations: mono conversion, filtering, fades and level matching
for the site's quill animation. The three excerpts are 135–155 ms, not a loop.

## Rebuilding and verification

`_build/sfx_sources/` contains the unmodified source files and SHA256 provenance.
`python3 _build/render_sfx.py` reproduces the edits using NumPy, SciPy and FFmpeg.
An ordinary site build needs only Python's standard library and uses the
already-rendered WAV files. `bank.json` records duration, peak, RMS, size and hash.
Each exported WAV also embeds its creator, license URL and adaptation note.
