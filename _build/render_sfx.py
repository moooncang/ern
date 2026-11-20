"""Edit recorded foley into the site's small sound bank.

Optional authoring dependencies: numpy, scipy, ffmpeg. Ordinary HTML builds
do not run this script. Source recordings and hashes are in sfx_sources/;
attribution and adaptation details are in audio/sfx/SOURCES.md.
"""
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.signal import butter, sosfilt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).resolve().parent / "sfx_sources"
DEST = ROOT / "audio/sfx"
RATE = 44100
META = '"Oculus Audio Pack 01" by Oculus VR, LLC; CC BY 4.0'
PENCIL = '"Pencil, Writing, Close, A" by InspectorJ; CC BY 3.0'


@lru_cache(maxsize=None)
def recording(name):
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(SOURCE / name),
        "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-",
    ])
    return np.frombuffer(raw, dtype="<f4").astype(np.float64)


def cut(name, start, length, speed=1):
    samples = recording(name)[round(start * RATE):round((start + length) * RATE)].copy()
    if speed != 1:
        samples = np.interp(np.arange(0, len(samples) - 1, speed), np.arange(len(samples)), samples)
    return samples


def mix(*layers):
    # Each layer is (recording excerpt, linear gain, offset in seconds).
    size = max(len(samples) + round(offset * RATE) for samples, _, offset in layers)
    result = np.zeros(size)
    for samples, gain, offset in layers:
        begin = round(offset * RATE)
        result[begin:begin + len(samples)] += samples * gain
    return result


def master(samples, low, high, peak_db=-8, rms_db=-23, release=.018):
    samples = samples - np.mean(samples)
    samples = sosfilt(butter(2, low, fs=RATE, btype="highpass", output="sos"), samples)
    samples = sosfilt(butter(3, high, fs=RATE, btype="lowpass", output="sos"), samples)
    # Rounded boundaries avoid a digital click without smearing the transient.
    attack = min(round(.002 * RATE), len(samples) // 4)
    tail = min(round(release * RATE), len(samples) // 3)
    samples[:attack] *= np.sin(np.linspace(0, np.pi / 2, attack)) ** 2
    samples[-tail:] *= np.sin(np.linspace(np.pi / 2, 0, tail)) ** 2
    peak = max(np.max(np.abs(samples)), 1e-9)
    rms = max(np.sqrt(np.mean(samples * samples)), 1e-9)
    samples *= min(10 ** (peak_db / 20) / peak, 10 ** (rms_db / 20) / rms)
    return samples.astype("<f4")


def save(name, samples, low=140, high=7600, peak_db=-8, rms_db=-23, release=.018, pencil=False):
    samples = master(samples, low, high, peak_db, rms_db, release)
    path = DEST / (name + ".wav")
    credit = PENCIL if pencil else META
    url = "https://creativecommons.org/licenses/by/3.0/" if pencil else "https://creativecommons.org/licenses/by/4.0/"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(RATE), "-ac", "1", "-i", "-",
        "-map_metadata", "-1", "-c:a", "pcm_s16le", "-metadata", f"artist={credit}",
        "-metadata", f"copyright={url}", "-metadata", "comment=Edited for ERN: excerpts, layering, EQ, fades, level matching. See SOURCES.md.", str(path),
    ], input=samples.tobytes(), check=True)
    return {"file": path.name, "seconds": round(len(samples) / RATE, 4), "bytes": path.stat().st_size,
            "peak_dbfs": round(float(20 * np.log10(max(np.max(np.abs(samples)), 1e-9))), 2),
            "rms_dbfs": round(float(20 * np.log10(max(np.sqrt(np.mean(samples * samples)), 1e-9))), 2),
            "sha256": sha256(path.read_bytes()).hexdigest()}


def main():
    for source in json.loads((SOURCE / "sources.json").read_text()):
        assert sha256((SOURCE / source["file"]).read_bytes()).hexdigest() == source["sha256"], source["file"]
    DEST.mkdir(exist_ok=True, parents=True)
    back, confirm = "UIClick_WoodBack_OS_01.ogg", "UIClick_WoodConfirm_OS_01.ogg"
    pages, close = "PAPRHndl_BookPageTurns_OS_01.ogg", "OBJBook_BookClose_OS_01.ogg"
    tear, crumple = "PAPRRip_PaperTear_OS_01.ogg", "PAPRHndl_PaperCrumple_OS_01.ogg"
    result = [
        save("select-1", cut(back, 0, .108), low=220, high=5400, peak_db=-10, rms_db=-25, release=.013),
        save("select-2", cut(confirm, .008, .112), low=220, high=5400, peak_db=-10, rms_db=-25, release=.013),
        save("paper-turn-1", cut(pages, .285, .34), low=180, high=7800),
        save("paper-turn-2", cut(pages, .695, .63, speed=1.24), low=180, high=7800),
        save("paper-turn-3", cut(pages, 1.995, .48), low=180, high=7800),
        save("seal-press-1", mix((cut(close, .112, .27), .70, 0), (cut(confirm, .006, .11), .12, 0),
                                 (cut("WOODImpt_LargeWoodDrop_OS_01.ogg", 0, .25), .32, .005)),
             low=95, high=3500, rms_db=-22, release=.04),
        save("seal-press-2", mix((cut("WOODImpt_LargeWoodDrop_OS_01.ogg", 0, .29, speed=1.13), .7, 0),
                                 (cut(close, .118, .22), .34, .012)), low=100, high=3300, rms_db=-22, release=.045),
        save("wax-break-1", mix((cut(tear, .005, .235), .70, 0), (cut(crumple, .285, .22), .55, .018),
                                (cut(back, 0, .10), .18, 0)), low=260, high=6800, rms_db=-22, release=.025),
        save("wax-break-2", mix((cut(crumple, .245, .30), .55, 0), (cut(tear, .075, .22), .80, .01),
                                (cut(back, .006, .10), .14, 0)), low=270, high=6700, rms_db=-22, release=.03),
        save("pen-stroke-1", cut("pencil-writing.wav", 1.04, .135), low=540, high=7600, peak_db=-11, rms_db=-24, pencil=True),
        save("pen-stroke-2", cut("pencil-writing.wav", 2.22, .155), low=540, high=7600, peak_db=-11, rms_db=-24, pencil=True),
        save("pen-stroke-3", cut("pencil-writing.wav", 7.37, .148), low=540, high=7600, peak_db=-11, rms_db=-24, pencil=True),
        save("folio-shift-1", cut("OBJBook_BookOpen_OS_01.ogg", .045, .50, speed=1.10), low=200, high=6500, rms_db=-24, release=.04),
        save("folio-shift-2", cut("OBJBook_BookOpen_OS_02.ogg", .025, .59, speed=1.22), low=210, high=6500, rms_db=-24, release=.04),
    ]
    (DEST / "bank.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Rendered {len(result)} clips, {sum(r['bytes'] for r in result):,} bytes; peaks <= -8 dBFS.")


if __name__ == "__main__":
    main()
