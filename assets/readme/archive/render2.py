"""Render an HTML stage with a setPhase(p) hook into a looping GIF + first-frame PNG.

usage: render2.py SRC.html OUT.gif PREVIEW.png W H [FRAMES] [DUR_MS] [PREVIEW_PHASE]
Sandbox-only variant of render.py with frame count and frame duration as arguments.
"""
import io, sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
SRC, OUT, PREVIEW = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = int(sys.argv[4]), int(sys.argv[5])
FRAMES = int(sys.argv[6]) if len(sys.argv) > 6 else 36
DUR_MS = int(sys.argv[7]) if len(sys.argv) > 7 else 70
PREVIEW_PHASE = float(sys.argv[8]) if len(sys.argv) > 8 else 0.0

def main():
    imgs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(HERE.joinpath(SRC).as_uri())
        page.wait_for_timeout(400)
        for i in range(FRAMES):
            page.evaluate(f"setPhase({i}/{FRAMES})")
            imgs.append(Image.open(io.BytesIO(page.screenshot())).convert("RGB"))
        page.evaluate(f"setPhase({PREVIEW_PHASE})")
        preview = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
        b.close()
    preview.save(HERE / PREVIEW)
    strip = Image.new("RGB", (W, H * 2))
    strip.paste(imgs[0], (0, 0)); strip.paste(imgs[FRAMES * 3 // 4], (0, H))
    pal = strip.quantize(colors=256)
    q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in imgs]
    q[0].save(HERE / OUT, save_all=True, append_images=q[1:], duration=DUR_MS, loop=0, optimize=True)
    print(f"OK {FRAMES} frames @ {DUR_MS}ms = {FRAMES*DUR_MS/1000:.1f}s, {(HERE/OUT).stat().st_size/1e6:.2f} MB")

if __name__ == "__main__":
    main()
