#!/usr/bin/env python3
"""Describe a source image before deciding how to animate it.

Prints size, aspect, alpha presence, a dominant-color palette (hex), the accent
colors (saturated, non-background), a flatness score, and a rough type guess.
Use the palette when redrawing so colors match the source.

Usage: python probe_image.py image.png [--colors 8]
"""
import argparse
import warnings
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops

warnings.simplefilter("ignore", DeprecationWarning)


def pixels(im):
    return list(im.getdata())


def hexes(q, n):
    pal = q.getpalette()[: n * 3]
    counts = Counter(pixels(q))
    total = sum(counts.values())
    for idx, c in counts.most_common(n):
        r, g, b = pal[idx * 3: idx * 3 + 3]
        yield f"#{r:02x}{g:02x}{b:02x}", 100 * c / total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("--colors", type=int, default=8)
    a = ap.parse_args()

    im = Image.open(a.image)
    w, h = im.size
    has_alpha = im.mode in ("RGBA", "LA") or "transparency" in im.info
    print(f"{a.image.name}: {w}x{h}, aspect {w / h:.3f}, mode {im.mode}, alpha {has_alpha}")

    sw = min(400, w)
    small = im.convert("RGB").resize((sw, max(1, int(sw * h / w))))
    q = small.quantize(colors=a.colors, method=Image.Quantize.MEDIANCUT)
    print("dominant colors (incl. background):")
    for hx, share in hexes(q, a.colors):
        print(f"  {hx}  {share:5.1f}%")

    # accent colors: saturated pixels only, so the background does not swamp the palette
    px = pixels(small)
    sat = [(r, g, b) for r, g, b in px if max(r, g, b) - min(r, g, b) > 60]
    if sat:
        acc = Image.new("RGB", (len(sat), 1))
        acc.putdata(sat)
        qa = acc.quantize(colors=min(6, len(set(sat))), method=Image.Quantize.MEDIANCUT)
        print(f"accent colors ({100 * len(sat) / len(px):.0f}% of pixels are saturated):")
        for hx, share in hexes(qa, 6):
            print(f"  {hx}  {share:5.1f}% of accents")
    else:
        print("accent colors: none (image is near-monochrome)")

    # flatness: share of pixels whose right-hand neighbour is almost identical.
    # Charts, diagrams and UI are mostly flat (also across smooth gradients); photos are not.
    shifted = ImageChops.offset(small, -1, 0)
    diff = ImageChops.difference(small, shifted).convert("L")
    flat = sum(1 for v in pixels(diff) if v < 6) / (small.width * small.height)
    edges = sum(1 for v in pixels(diff) if v > 60) / (small.width * small.height)
    print(f"flatness {100 * flat:.0f}% (share of near-identical neighbours), hard edges {100 * edges:.1f}%")

    if flat > 0.80 and edges > 0.005:
        guess = "chart / diagram / UI: flat regions with crisp edges. Overlay or region loop first; redraw is feasible."
    elif flat > 0.80:
        guess = "very flat image (illustration, gradient art). Overlay or region loop; redraw feasible."
    else:
        guess = "photo or rich render: prefer overlay or region loop; a redraw is not realistic."
    print("type guess:", guess)


if __name__ == "__main__":
    main()
