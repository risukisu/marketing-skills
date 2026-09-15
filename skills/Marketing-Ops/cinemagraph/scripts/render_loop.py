#!/usr/bin/env python3
"""Render a phase-parametric HTML page into a seamless animated WebP (and optionally GIF).

The page must expose a global `setPhase(p)` taking p in [0, 1). Every animated
property should be a pure function of p so that setPhase(1.0) == setPhase(0.0).

Usage:
  python render_loop.py page.html out.webp [--frames 40] [--duration 80]
                        [--width 1300] [--height 820] [--scale 1]
                        [--alpha] [--gif] [--dither] [--quality 82] [--check]

Writes out.webp, out.png (frame 0) and, with --gif, out.gif.
"""
import argparse
import io
import sys
from pathlib import Path

from PIL import Image, ImageChops


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
    ap.add_argument("--quality", type=int, default=82, help="WebP quality")
    ap.add_argument("--check", action="store_true", help="run seam/stillness/weight checks and print them")
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


def save(a, frames):
    out = a.out.with_suffix(".webp")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=a.duration, loop=0,
                   quality=a.quality, method=6)
    frames[0].save(a.out.with_suffix(".png"))
    written = [out, a.out.with_suffix(".png")]
    if a.gif:
        strip = Image.new("RGB", (frames[0].width, frames[0].height * 2))
        strip.paste(frames[0].convert("RGB"), (0, 0))
        strip.paste(frames[len(frames) // 2].convert("RGB"), (0, frames[0].height))
        pal = strip.quantize(colors=256)
        dither = Image.Dither.FLOYDSTEINBERG if a.dither else Image.Dither.NONE
        q = [f.convert("RGB").quantize(palette=pal, dither=dither) for f in frames]
        gif = a.out.with_suffix(".gif")
        q[0].save(gif, save_all=True, append_images=q[1:], duration=a.duration, loop=0, optimize=True)
        written.append(gif)
    return written


def _step(a, b):
    """Mean absolute pixel difference between two frames (0..255)."""
    d = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).convert("L")
    hist = d.histogram()
    n = sum(hist)
    return sum(i * c for i, c in enumerate(hist)) / n if n else 0.0


def check(frames, wrap, written):
    # Seam: the wrap step (last frame -> frame 0) should look like any other step.
    # Continuous motions (march, drift) make it identical; sawtooth motions (a pulse that
    # fades out and restarts) make it a normal-sized step. A step much larger than the
    # typical one means some property is not periodic in p.
    steps = [_step(frames[i], frames[i + 1]) for i in range(len(frames) - 1)]
    typical = sorted(steps)[len(steps) // 2] if steps else 0.0
    wrap_step = _step(frames[-1], frames[0])
    exact = ImageChops.difference(frames[0], wrap).getbbox() is None
    if exact:
        verdict = "OK (phase 1.0 renders identical to phase 0)"
    elif typical == 0 or wrap_step <= 2.0 * typical + 0.05:
        verdict = f"OK (wrap step {wrap_step:.3f} vs typical step {typical:.3f})"
    else:
        verdict = f"SUSPECT: wrap step {wrap_step:.3f} is {wrap_step / max(typical, 1e-6):.1f}x the typical step {typical:.3f}"
    print("seam:", verdict)
    mid = ImageChops.difference(frames[0], frames[len(frames) // 2]).getbbox()
    print(f"moving region (frame0 vs mid): {mid if mid else 'nothing moves!'}")
    for w in written:
        mb = w.stat().st_size / 1e6
        flag = "" if mb <= 1.0 else ("  (heavy for a hero)" if mb <= 2.0 else "  (too heavy)")
        print(f"{w.name}: {mb:.2f} MB{flag}")


def main():
    a = parse()
    frames, wrap = render_frames(a)
    written = save(a, frames)
    print(f"{len(frames)} frames @ {a.duration} ms = {len(frames) * a.duration / 1000:.1f} s loop, "
          f"{frames[0].width}x{frames[0].height}, mode {frames[0].mode}")
    if a.check:
        check(frames, wrap, written)
    for w in written:
        print("wrote", w)


if __name__ == "__main__":
    sys.exit(main())
