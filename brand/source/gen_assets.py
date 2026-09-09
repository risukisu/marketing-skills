"""Generate the README asset set in the os-schematic style.

Outputs (into ../../assets/readme/ by default):
  section-shelf/home/provenance/drift/elsewhere.svg                               (1200x140)
  how-it-works.svg                                                                (1200x400)

Pure SVG, system font stacks, no scripts. Pixel numerals are drawn as rects from the same
5x7 bitmap font as the hero wordmark, so the motif carries through.
"""
from pathlib import Path
import sys

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "assets" / "readme"

BG, PANEL, LINE = "#0e100d", "#151813", "#262b23"
INK, MUT, MUT2, DIM = "#e9ebe3", "#899084", "#b4bab0", "#5b6156"
ACC, AMB, BLU = "#3fd68c", "#e8a13d", "#7c8cf0"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Courier New', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif"

GLYPHS = {
    "0": ["01110","10001","10011","10101","11001","10001","01110"],
    "1": ["00100","01100","00100","00100","00100","00100","01110"],
    "2": ["01110","10001","00001","00010","00100","01000","11111"],
    "3": ["11110","00001","00001","01110","00001","00001","11110"],
    "4": ["00010","00110","01010","10010","11111","00010","00010"],
    "5": ["11111","10000","10000","11110","00001","00001","11110"],
}

def pixels(text, x0, y0, px=5, gap=1, color=ACC):
    out, x = [], 0
    for ch in text:
        g = GLYPHS[ch]; w = len(g[0])
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == "1":
                    out.append(f'<rect x="{x0 + (x + c) * px + gap/2:.1f}" y="{y0 + r * px + gap/2:.1f}" '
                               f'width="{px - gap}" height="{px - gap}" rx="1" fill="{color}"/>')
        x += w + 1
    return "\n".join(out), x * px

def dotgrid(w, h, step=36):
    return (f'<defs><pattern id="dots" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
            f'<circle cx="1.4" cy="1.4" r="1.4" fill="#1d211b"/></pattern></defs>'
            f'<rect width="{w}" height="{h}" rx="18" fill="url(#dots)" opacity=".55"/>')

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def section(name, num, eyebrow, title, subtitle, color):
    W, H = 1200, 140
    px_num, num_w = pixels(num, 48, 40, px=6, color=color)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">',
        f'<title id="t">Section {num}: {esc(title)}</title>',
        f'<desc id="d">{esc(subtitle)}</desc>',
        f'<rect width="{W}" height="{H}" rx="18" fill="{BG}"/>',
        dotgrid(W, H),
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="17" fill="none" stroke="{LINE}"/>',
        f'<rect x="0" y="0" width="220" height="4" rx="2" fill="{color}" opacity=".9"/>',
        px_num,
        f'<text x="{48 + num_w + 22}" y="52" font-family="{MONO}" font-size="18" letter-spacing="2.4" fill="{DIM}">{esc(eyebrow)}</text>',
        f'<text x="{48 + num_w + 22}" y="98" font-family="{SANS}" font-size="40" font-weight="800" letter-spacing="-0.8" fill="{INK}">{esc(title)}</text>',
        f'<text x="{W-48}" y="86" text-anchor="end" font-family="{MONO}" font-size="20" fill="{MUT}">{esc(subtitle)}</text>',
        # cursor echo: three trailing cells
        f'<rect x="{W-48-14}" y="104" width="10" height="10" rx="1.5" fill="{color}" opacity=".9"/>',
        f'<rect x="{W-48-30}" y="104" width="10" height="10" rx="1.5" fill="{color}" opacity=".45"/>',
        f'<rect x="{W-48-46}" y="104" width="10" height="10" rx="1.5" fill="{color}" opacity=".2"/>',
        '</svg>',
    ]
    (OUT / f"section-{name}.svg").write_text("\n".join(parts), encoding="utf-8")

def how_it_works():
    W, H = 1200, 400
    stages = [
        ("1", "you say", ACC, ['"the blog brings', 'no leads"', "plain words or", "a slash command"]),
        ("2", "it asks", AMB, ["a couple of", "questions, one", "at a time", "never assumes"]),
        ("3", "your files", BLU, ["scans the folder,", "lists what it", "found, reads only", "with your yes"]),
        ("4", "your data", ACC, ["GA4 and Search", "Console when", "connected, else", "it asks you"]),
        ("5", "the work", AMB, ["a strategy, audit,", "brief or draft,", "saved as a file", "you can edit"]),
    ]
    n = len(stages); margin, gap = 40, 34
    cw = (W - 2 * margin - (n - 1) * gap) / n
    top, ch = 96, 236
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">',
        '<title id="t">How a skill runs</title>',
        '<desc id="d">Five stages: you say what you need, the skill asks a couple of questions, scans your folder and reads files only with your yes, pulls live data when connected, and saves the work as a file. Unknown numbers are labeled, never invented.</desc>',
        f'<rect width="{W}" height="{H}" rx="18" fill="{BG}"/>',
        dotgrid(W, H),
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="17" fill="none" stroke="{LINE}"/>',
        f'<text x="{margin}" y="50" font-family="{MONO}" font-size="18" letter-spacing="2.4" fill="{DIM}">HOW A SKILL RUNS</text>',
        f'<text x="{W-margin}" y="50" text-anchor="end" font-family="{MONO}" font-size="18" fill="{MUT}">same shape, every skill</text>',
    ]
    for i, (num, title, color, lines) in enumerate(stages):
        x = margin + i * (cw + gap)
        parts.append(f'<rect x="{x:.1f}" y="{top}" width="{cw:.1f}" height="{ch}" rx="14" fill="{PANEL}" stroke="{LINE}"/>')
        parts.append(f'<rect x="{x:.1f}" y="{top}" width="{cw:.1f}" height="4" rx="2" fill="{color}" opacity=".9"/>')
        pxs, _ = pixels(num, x + 18, top + 24, px=5, color=color)
        parts.append(pxs)
        parts.append(f'<text x="{x + 60:.1f}" y="{top + 54}" font-family="{SANS}" font-size="24" font-weight="800" fill="{INK}">{esc(title)}</text>')
        for k, ln in enumerate(lines):
            parts.append(f'<text x="{x + 18:.1f}" y="{top + 96 + k * 28}" font-family="{MONO}" font-size="18" fill="{MUT2}">{esc(ln)}</text>')
        if i < n - 1:
            ax = x + cw + 4; bx = x + cw + gap - 4; ay = top + ch / 2
            parts.append(f'<path d="M {ax:.1f} {ay:.1f} L {bx:.1f} {ay:.1f}" stroke="{DIM}" stroke-width="1.6" stroke-dasharray="4 5"/>')
            parts.append(f'<path d="M {bx-7:.1f} {ay-5:.1f} L {bx:.1f} {ay:.1f} L {bx-7:.1f} {ay+5:.1f}" fill="none" stroke="{DIM}" stroke-width="1.6"/>')
    parts.append(f'<text x="{W/2}" y="{H-32}" text-anchor="middle" font-family="{MONO}" font-size="18" fill="{MUT}">a number the skill cannot get is written as <tspan fill="{ACC}" font-weight="700">unknown</tspan>, never invented</text>')
    parts.append('</svg>')
    (OUT / "how-it-works.svg").write_text("\n".join(parts), encoding="utf-8")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    section("shelf", "01", "THE SHELF", "the shelf", "one folder per skill, the folder name is the command", ACC)
    section("home", "02", "TAKE IT HOME", "take it home", "clone, run the installer, start asking", AMB)
    section("provenance", "03", "WHERE IT COMES FROM", "where it comes from", "provenance and licenses, per skill", BLU)
    section("drift", "04", "ZERO DRIFT", "zero drift", "install once, pull to update, nothing to copy around", ACC)
    section("elsewhere", "05", "ELSEWHERE", "elsewhere", "the rest of what risu builds and writes", AMB)
    how_it_works()
    print("wrote", sorted(p.name for p in OUT.glob("*.svg")))
