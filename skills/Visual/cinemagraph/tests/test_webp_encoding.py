"""The WebP the renderer writes is small, exact when lossless, and keeps the loop's timing.

Renders a small flat loop (400x240, three beats, one accent, 30 frames at 100 ms) once and
checks the encoder on it. Needs Pillow and Playwright (Chromium), like the renderer.

    python tests/test_webp_encoding.py      (or: pytest tests/)
"""
import argparse
import functools
import io
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

import render_loop  # noqa: E402
from flat_page import H, W, page_html  # noqa: E402

FRAMES, MS = 30, 100


@functools.lru_cache(maxsize=None)
def rendered():
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "flat.html"
        page.write_text(page_html(), encoding="utf-8")
        a = argparse.Namespace(page=page, frames=FRAMES, width=W, height=H, scale=1.0, alpha=False)
        frames, _wrap = render_loop.render_frames(a)
    return frames


def decoded_timeline(data):
    """[(start_ms, end_ms, RGB image)] for every stored frame, rebuilt from timestamps.

    `im.info` describes the frame last loaded, not the one just sought, so each frame is
    loaded before its timestamp is read; `info["duration"]` is None on frame 0 until then.
    """
    im = Image.open(io.BytesIO(data))
    starts, pics = [], []
    for k in range(im.n_frames):
        im.seek(k)
        im.load()
        starts.append(im.info["timestamp"])
        pics.append(im.convert("RGB"))
    im.seek(im.n_frames - 1)
    im.load()
    total = starts[-1] + im.info["duration"]
    ends = starts[1:] + [total]
    return list(zip(starts, ends, pics))


def test_chosen_encoding_is_no_larger_than_lossy():
    frames = rendered()
    lossy = render_loop.encode_webp(frames, MS, lossless=False, quality=82)
    chosen, label, _sizes = render_loop.choose_webp(frames, MS, quality=82)
    assert label in ("lossless", "lossy")
    assert len(chosen) <= len(lossy), f"kept {label} at {len(chosen)} B, lossy is {len(lossy)} B"


def test_lossless_decodes_pixel_exact_by_timestamp():
    frames = rendered()
    data = render_loop.encode_webp(frames, MS, lossless=True, quality=None)
    timeline = decoded_timeline(data)
    assert len(timeline) <= FRAMES  # identical consecutive frames may be merged
    wrong = []
    for i, fr in enumerate(frames):
        t = i * MS
        shown = next(pic for s, e, pic in timeline if s <= t < e)
        if ImageChops.difference(shown, fr.convert("RGB")).getbbox() is not None:
            wrong.append(i)
    assert not wrong, f"lossless WebP differs from the rendered frames at {wrong}"


def test_total_duration_is_frames_times_duration():
    frames = rendered()
    data = render_loop.encode_webp(frames, MS, lossless=True, quality=None)
    timeline = decoded_timeline(data)
    assert timeline[-1][1] == FRAMES * MS
    assert all(e > s for s, e, _ in timeline)


if __name__ == "__main__":
    test_chosen_encoding_is_no_larger_than_lossy()
    test_lossless_decodes_pixel_exact_by_timestamp()
    test_total_duration_is_frames_times_duration()
    print("ok: webp encoding is small, exact and keeps the loop's timing")
