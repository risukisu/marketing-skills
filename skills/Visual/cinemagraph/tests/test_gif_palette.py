"""The GIF keeps every hue in the loop, not only the ones on frame 0 and mid-loop.

A choreographed loop gives each beat its own accent. This page shows five
beats, each a flat square in its own hue, and checks that the GIF renders
every beat in its hue. Needs Pillow and Playwright (Chromium), like the renderer.

    python tests/test_gif_palette.py      (or: pytest tests/)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

RENDER = Path(__file__).resolve().parents[1] / "scripts" / "render_loop.py"
HUES = ["#3fd68c", "#e8a13d", "#7c8cf0", "#f08a6b", "#b58cf5"]  # one per beat
FRAMES, MS = 40, 80

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html, body { margin: 0; background: #0e100d; }
#sq { position: absolute; left: 50px; top: 50px; width: 100px; height: 100px; }
</style></head><body><div id="sq"></div><script>
const HUES = %s;
function setPhase(p) { document.getElementById("sq").style.background = HUES[Math.floor(p * HUES.length) %% HUES.length]; }
setPhase(0);
</script></body></html>""" % HUES


def rgb(hex_):
    return tuple(int(hex_[i : i + 2], 16) for i in (1, 3, 5))


def frame_at(gif, ms):
    """The GIF frame on screen at `ms` (identical frames may be merged, so go by durations)."""
    t = 0
    for k in range(gif.n_frames):
        gif.seek(k)
        t += gif.info["duration"]
        if t > ms:
            return gif.convert("RGB")
    raise AssertionError(f"GIF is shorter than {ms} ms")


def test_every_beat_keeps_its_hue():
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "beats.html"
        page.write_text(PAGE, encoding="utf-8")
        out = Path(tmp) / "beats.webp"
        subprocess.run(
            [sys.executable, str(RENDER), str(page), str(out), "--gif",
             "--frames", str(FRAMES), "--duration", str(MS), "--width", "200", "--height", "200"],
            check=True, capture_output=True,
        )
        with Image.open(out.with_suffix(".gif")) as gif:
            per_beat = FRAMES // len(HUES)
            wrong = []
            for b, hue in enumerate(HUES):
                got = frame_at(gif, (b * per_beat + per_beat // 2) * MS).getpixel((100, 100))
                if max(abs(g - w) for g, w in zip(got, rgb(hue))) > 12:
                    wrong.append(f"beat {b}: expected {hue}, got #{got[0]:02x}{got[1]:02x}{got[2]:02x}")
            assert not wrong, "GIF lost beat hues: " + "; ".join(wrong)


if __name__ == "__main__":
    test_every_beat_keeps_its_hue()
    print("ok: every beat keeps its hue in the GIF")
