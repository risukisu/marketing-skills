#!/usr/bin/env python3
"""Render a phase-parametric HTML page into a seamless animated WebP (and optionally GIF).

The page must expose a global `setPhase(p)` taking p in [0, 1). Every animated
property should be a pure function of p so that setPhase(1.0) == setPhase(0.0).

Usage:
  python render_loop.py page.html out.webp [--frames 40] [--duration 80]
                        [--width 1300] [--height 820] [--scale 1]
                        [--alpha] [--gif] [--dither] [--lossless | --quality 82] [--check]

Writes out.webp, out.png (frame 0) and, with --gif, out.gif.

WebP encoding: identical consecutive frames are always merged (minimize_size, kmax = frame
count), so a choreographed loop's holds cost nothing. With neither --lossless nor --quality
the renderer encodes both ways and keeps the smaller file, preferring lossless when it is
within about 10%, because it is exact. For flat art (white ground, thin lines, text) lossless
is usually the smaller one by a wide margin.
"""
import argparse
import io
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops

PALETTE_PIXELS = 40_000_000  # frames sampled for the GIF palette, in pixels (~120 MB as RGB)
DEFAULT_QUALITY = 82         # lossy quality when the encoder is left to choose
LOSSLESS_MARGIN = 0.10       # keep lossless when it is within this much of the lossy size
STEP_RATIO = 3.0             # a step this many times the median step ...
STEP_FLOOR = 0.05            # ... and larger than this (mean abs pixel diff, 0..255) is large
FADE_FRAMES = 3              # a large step inside a run of this many similar steps is a fade, not a snap


def parse():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", type=Path, help="HTML file exposing setPhase(p)")
    ap.add_argument("out", type=Path, help="output .webp path (basename reused for .png/.gif)")
    ap.add_argument("--frames", type=int, default=40)
    ap.add_argument("--duration", type=int, default=80, help="ms per frame")
    ap.add_argument("--width", type=int, default=1300)
    ap.add_argument("--height", type=int, default=820)
    ap.add_argument("--scale", type=float, default=1.0, help="device scale factor")
    ap.add_argument("--alpha", action="store_true", help="transparent canvas (omit page background)")
    ap.add_argument("--gif", action="store_true", help="also write a GIF with a shared palette")
    ap.add_argument("--dither", action="store_true", help="Floyd-Steinberg dither in the GIF (smoother gradients, larger file, slight frame noise)")
    enc = ap.add_mutually_exclusive_group()
    enc.add_argument("--quality", type=int, default=None,
                     help=f"lossy WebP at this quality (default: encode lossless and lossy q{DEFAULT_QUALITY}, keep the smaller)")
    enc.add_argument("--lossless", action="store_true", help="lossless WebP (pixel-exact; usually smallest for flat art)")
    ap.add_argument("--check", action="store_true", help="run seam/step/stillness/weight checks and print them")
    return ap.parse_args()


def render_frames(a):
    from playwright.sync_api import sync_playwright

    frames = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": a.width, "height": a.height}, device_scale_factor=a.scale)
        page.goto(a.page.resolve().as_uri())
        page.evaluate("document.fonts ? document.fonts.ready : Promise.resolve()")
        page.wait_for_timeout(400)
        for i in range(a.frames):
            page.evaluate(f"setPhase({i}/{a.frames})")
            png = page.screenshot(omit_background=a.alpha)
            frames.append(Image.open(io.BytesIO(png)).convert("RGBA" if a.alpha else "RGB"))
        # one extra frame at phase 1.0 for the seam check
        page.evaluate("setPhase(1.0)")
        wrap = Image.open(io.BytesIO(page.screenshot(omit_background=a.alpha))).convert(frames[0].mode)
        browser.close()
    return frames, wrap


def encode_webp(frames, duration, lossless, quality):
    """Animated WebP bytes. Identical consecutive frames are merged into one longer frame."""
    buf = io.BytesIO()
    kw = {"lossless": True} if lossless else {"quality": quality}
    frames[0].save(buf, "WEBP", save_all=True, append_images=frames[1:], duration=duration, loop=0,
                   method=6, minimize_size=True, kmax=len(frames), **kw)
    return buf.getvalue()


def choose_webp(frames, duration, quality=DEFAULT_QUALITY):
    """Encode lossy and lossless; return (bytes, label, sizes). Lossless wins when it is
    within LOSSLESS_MARGIN of the lossy size, because it is exact."""
    lossy = encode_webp(frames, duration, lossless=False, quality=quality)
    exact = encode_webp(frames, duration, lossless=True, quality=None)
    sizes = {"lossy": len(lossy), "lossless": len(exact)}
    if len(exact) <= len(lossy) * (1 + LOSSLESS_MARGIN):
        return exact, "lossless", sizes
    return lossy, "lossy", sizes


def _mb(n):
    return f"{n / 1e6:.2f} MB"


def save(a, frames):
    """Write the WebP (and PNG, and GIF with --gif). Returns (written paths, 'lossless'|'lossy')."""
    out = a.out.with_suffix(".webp")
    if a.lossless:
        data, label = encode_webp(frames, a.duration, lossless=True, quality=None), "lossless"
        print(f"webp: lossless {_mb(len(data))} (exact)")
    elif a.quality is not None:
        data, label = encode_webp(frames, a.duration, lossless=False, quality=a.quality), "lossy"
        print(f"webp: lossy q{a.quality} {_mb(len(data))}")
    else:
        data, label, sizes = choose_webp(frames, a.duration)
        print(f"webp: lossy q{DEFAULT_QUALITY} {_mb(sizes['lossy'])}, lossless {_mb(sizes['lossless'])}"
              f" -> kept {label}" + (" (exact)" if label == "lossless" else ""))
    out.write_bytes(data)
    frames[0].save(a.out.with_suffix(".png"))
    written = [out, a.out.with_suffix(".png")]
    if a.gif:
        # One palette for the whole loop, built from frames spread evenly across it, so a
        # hue that shows in only one beat (a choreographed loop's accents) keeps its colour.
        w, h = frames[0].size
        step = max(1, math.ceil(len(frames) / max(1, PALETTE_PIXELS // (w * h))))
        sample = frames[::step]
        strip = Image.new("RGB", (w, h * len(sample)))
        for k, fr in enumerate(sample):
            strip.paste(fr.convert("RGB"), (0, k * h))
        pal = strip.quantize(colors=256)
        dither = Image.Dither.FLOYDSTEINBERG if a.dither else Image.Dither.NONE
        q = [f.convert("RGB").quantize(palette=pal, dither=dither) for f in frames]
        gif = a.out.with_suffix(".gif")
        q[0].save(gif, save_all=True, append_images=q[1:], duration=a.duration, loop=0, optimize=True)
        written.append(gif)
    return written, label


def _step(a, b):
    """Mean absolute pixel difference between two frames (0..255)."""
    d = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).convert("L")
    hist = d.histogram()
    n = sum(hist)
    return sum(i * c for i, c in enumerate(hist)) / n if n else 0.0


def step_report(frames):
    """Every step around the loop: step i is frame i -> frame i+1, the last one is the wrap
    (last frame -> frame 0).

    A step is *large* when it is more than STEP_RATIO times the median step and above
    STEP_FLOOR. A large step is a *snap* unless it is part of a fade: a neighbouring step at
    least half its size, inside a run of at least FADE_FRAMES consecutive large steps. In a
    choreographed loop the median step is the hold, so a reset spread over three frames is
    large too; only the lone jump is the defect, usually a reset that had not finished on
    the beat's last frame."""
    n = len(frames)
    steps = [_step(frames[i], frames[(i + 1) % n]) for i in range(n)]
    median = sorted(steps)[n // 2] if steps else 0.0
    max_index = max(range(n), key=steps.__getitem__) if steps else 0
    max_step = steps[max_index] if steps else 0.0
    large = [s > STEP_RATIO * median and s > STEP_FLOOR for s in steps]

    def run_length(i):
        if all(large):
            return n
        left = right = 0
        while large[(i - left - 1) % n]:
            left += 1
        while large[(i + right + 1) % n]:
            right += 1
        return left + 1 + right

    snaps = []
    for i, s in enumerate(steps):
        if not large[i]:
            continue
        neighbour = max(steps[(i - 1) % n], steps[(i + 1) % n])
        in_fade = neighbour >= s / 2 and run_length(i) >= FADE_FRAMES
        if not in_fade:
            snaps.append(i)
    return {"steps": steps, "median": median, "max_step": max_step, "max_index": max_index,
            "snaps": snaps, "flagged": bool(snaps)}


def verify_webp(path, frames, duration, lossless):
    """Decode the written WebP and compare it with the rendered frames.

    Returns (frames stored, total ms, problems). The timeline is rebuilt from each frame's
    `info["timestamp"]` (its start), read after `load()`: `im.info` still describes the
    previously loaded frame right after `seek()`, and `info["duration"]` is None on frame 0
    until it is loaded, so summing durations runs off by one and reports false mismatches.
    """
    mode = frames[0].mode
    starts, pics = [], []
    with Image.open(path) as im:
        stored = im.n_frames
        for k in range(stored):
            im.seek(k)
            im.load()
            starts.append(im.info["timestamp"])
            if lossless:
                pics.append(im.convert(mode))
        total = starts[-1] + im.info["duration"]
    problems = []
    expected = len(frames) * duration
    if total != expected:
        problems.append(f"total duration {total} ms, expected {expected} ms")
    if lossless:
        ends = starts[1:] + [total]
        bad = []
        for i, fr in enumerate(frames):
            t = i * duration
            k = next((k for k, (s, e) in enumerate(zip(starts, ends)) if s <= t < e), None)
            if k is None or ImageChops.difference(pics[k], fr).getbbox() is not None:
                bad.append(i)
        if bad:
            problems.append(f"{len(bad)} rendered frames differ from the decoded WebP (first: frame {bad[0]})")
    return stored, total, problems


def check(frames, wrap, written, a, encoding):
    n = len(frames)
    rep = step_report(frames)
    median, steps = rep["median"], rep["steps"]

    # Seam: the wrap step (last frame -> frame 0) should look like any other step.
    # Continuous motions (march, drift) make it identical; sawtooth motions (a pulse that
    # fades out and restarts) make it a normal-sized step. A step much larger than the
    # typical one means some property is not periodic in p.
    wrap_step = steps[-1]
    exact = ImageChops.difference(frames[0], wrap).getbbox() is None
    if exact:
        verdict = "OK (phase 1.0 renders identical to phase 0)"
    elif median == 0 or wrap_step <= 2.0 * median + 0.05:
        verdict = f"OK (wrap step {wrap_step:.3f} vs median step {median:.3f})"
    else:
        verdict = f"SUSPECT: wrap step {wrap_step:.3f} is {wrap_step / max(median, 1e-6):.1f}x the median step {median:.3f}"
    print("seam:", verdict)

    # Largest step anywhere in the loop, and any snap. The seam check misses a snap at an
    # inner beat boundary (frame F-1 -> F); this one does not.
    def where(i):
        return f"frame {i}->{(i + 1) % n}" + (" (wrap)" if i == n - 1 else "")

    print(f"largest step: {rep['max_step']:.3f} at {where(rep['max_index'])} (median step {median:.3f})")
    if rep["flagged"]:
        shown = ", ".join(f"{where(i)} ({steps[i]:.3f}, {steps[i] / max(median, 1e-6):.0f}x the median)"
                          for i in rep["snaps"][:5])
        more = f" and {len(rep['snaps']) - 5} more" if len(rep["snaps"]) > 5 else ""
        print(f"snaps: SUSPECT at {shown}{more}. A lone step this size is a cut. A choreographed reset must"
              " spread over at least 3 frames and finish before the beat's last frame: with F frames per"
              " beat, end <= (F-1)/F.")
    else:
        print("snaps: none (every large step is part of a fade over 3+ frames)")

    mid = ImageChops.difference(frames[0], frames[n // 2]).getbbox()
    print(f"moving region (frame0 vs mid): {mid if mid else 'nothing moves!'}")

    webp = next((w for w in written if w.suffix == ".webp"), None)
    if webp is not None:
        stored, total, problems = verify_webp(webp, frames, a.duration, encoding == "lossless")
        pixels = "exact" if encoding == "lossless" and not any("differ" in p for p in problems) else \
                 ("DIFFER" if encoding == "lossless" else "not compared (lossy)")
        status = "OK" if not problems else "SUSPECT: " + "; ".join(problems)
        print(f"webp decoded: {stored} frames stored for {n} rendered, {total} ms, pixels {pixels}: {status}")

    for w in written:
        mb = w.stat().st_size / 1e6
        flag = "" if mb <= 1.0 else ("  (heavy for a hero)" if mb <= 2.0 else "  (too heavy)")
        print(f"{w.name}: {mb:.2f} MB{flag}")


def main():
    a = parse()
    frames, wrap = render_frames(a)
    written, encoding = save(a, frames)
    print(f"{len(frames)} frames @ {a.duration} ms = {len(frames) * a.duration / 1000:.1f} s loop, "
          f"{frames[0].width}x{frames[0].height}, mode {frames[0].mode}")
    if a.check:
        check(frames, wrap, written, a, encoding)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    sys.exit(main())
