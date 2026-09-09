"""Render source.html -> marketing-os.gif (36 frames @ 70ms, seamless loop)."""
import io, os, sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
FRAMES = 36
DUR_MS = 70
SRC = sys.argv[1] if len(sys.argv) > 1 else "source.html"
OUT = sys.argv[2] if len(sys.argv) > 2 else "marketing-os.gif"
PREVIEW = sys.argv[3] if len(sys.argv) > 3 else "preview.png"
W = int(sys.argv[4]) if len(sys.argv) > 4 else 864
H = int(sys.argv[5]) if len(sys.argv) > 5 else 1080

def main():
    imgs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto(HERE.joinpath(SRC).as_uri())
        page.wait_for_timeout(300)
        for i in range(FRAMES):
            page.evaluate(f"setPhase({i}/{FRAMES})")
            imgs.append(Image.open(io.BytesIO(page.screenshot())).convert("RGB"))
        b.close()

    imgs[0].save(HERE / PREVIEW)
    # shared adaptive palette from a composite of first + mid frame
    strip = Image.new("RGB", (W, H * 2))
    strip.paste(imgs[0], (0, 0)); strip.paste(imgs[FRAMES // 2], (0, H))
    pal = strip.quantize(colors=256)
    q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in imgs]
    q[0].save(HERE / OUT, save_all=True, append_images=q[1:],
              duration=DUR_MS, loop=0, optimize=True)
    size = (HERE / OUT).stat().st_size
    print(f"OK {FRAMES} frames, {size/1e6:.2f} MB")

if __name__ == "__main__":
    main()
