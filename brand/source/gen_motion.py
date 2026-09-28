"""Generate the two animated README panels: the "you say -> it runs" readout
beside an art panel that acts each pair out, in the command's own colour.

Outputs (into ../../assets/readme/ by default):
  motion-keys.svg  (1200x400)  the keys light as the command types; Enter flashes when it runs
  motion-work.svg  (1200x400)  a small wireframe of what each skill hands back, building itself

Pure SVG + CSS animation (no scripts), system font stacks, one 13 s loop: five pairs,
2.6 s each. Ported from the marketing-skills tile options on abialas.pl
(/dev/skills-tile/, src/components/dev/SkillsArtTile.astro), where the readout and the
art share the same loop. Reduced motion shows the first pair, finished.
"""
from pathlib import Path
import math
import sys

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "assets" / "readme"

BG, PANEL, LINE = "#0e100d", "#151813", "#262b23"
INK, MUT, MUT2, DIM = "#e9ebe3", "#899084", "#b4bab0", "#5b6156"
ACC, AMB, BLU = "#3fd68c", "#e8a13d", "#7c8cf0"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Courier New', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif"

# [you say, it runs, hue] — the hero's own phrases; every command in its own colour
PAIRS = [
    ("“audit the whole site”", "/seo-audit", ACC),
    ("“this page isn’t converting”", "/cro", AMB),
    ("“sounds like AI wrote it”", "/copy-deslop", BLU),
    ("“the blog brings no leads”", "/content-strategy", "#f08a6b"),
    ("“what would Ogilvy say?”", "/marketing-council", "#b58cf5"),
]
HOLD = 2.6
LOOP = HOLD * len(PAIRS)

W, H = 1200, 400
CH = 15.6  # mono advance at 26px; textLength pins it so every font lines up
RX = 170  # readout text column
SAY_Y, RUN_Y = 262, 318
ART_X, ART_Y, ART_S = 703, 82, 1.38  # the 300x210 art space, scaled into the right panel


def f(n):
    return f"{n:.1f}"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def lcg(seed):
    """The tile's seeded LCG, in IEEE doubles like its JavaScript original."""
    s = float(seed)

    def rnd():
        nonlocal s
        s = (s * 1103515245.0 + 12345.0) % 2147483648.0
        return s / 2147483648.0

    return rnd


def cover_w(run):
    return len(run) * CH + 6 + 13 + 4  # text, gap, cursor, margin


# ── CSS ────────────────────────────────────────────────────────────
CSS = f"""
:root {{ --hold: {HOLD}s; --loop: {LOOP}s; }}
/* one pair owns 20% of the loop: the phrase fades in, the command types in 14 steps */
.say {{ opacity: 0; animation: say var(--loop) ease-out infinite; animation-delay: calc(var(--i) * var(--hold)); }}
.run {{ opacity: 0; animation: run var(--loop) ease-out infinite; animation-delay: calc(var(--i) * var(--hold)); }}
.cover {{ fill: {BG}; transform-box: fill-box; transform-origin: 100% 50%; animation: cover var(--loop) linear infinite; animation-delay: calc(var(--i) * var(--hold)); }}
.cur {{ animation: blink 1s steps(2, end) infinite; }}
@keyframes say {{ 0% {{ opacity: 0; }} 2% {{ opacity: 1; }} 18.6% {{ opacity: 1; }} 20% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
@keyframes run {{ 0%, 2.9% {{ opacity: 0; }} 3% {{ opacity: 1; }} 18.6% {{ opacity: 1; }} 20% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
@keyframes cover {{ 0% {{ transform: scaleX(1); }} 3% {{ transform: scaleX(1); animation-timing-function: steps(14, end); }} 8% {{ transform: scaleX(0); }} 100% {{ transform: scaleX(0); }} }}
@keyframes blink {{ to {{ opacity: 0; }} }}

/* the art: a skill's piece shows only while its pair is on */
.art__on {{ opacity: 0; animation: on var(--loop) ease-out infinite backwards; animation-delay: calc(var(--i) * var(--hold)); }}
@keyframes on {{ 0% {{ opacity: 0; }} 2% {{ opacity: 1; }} 18.6% {{ opacity: 1; }} 20% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
/* build steps inside a window: each piece arrives --d after its pair */
.b {{ opacity: 0; animation: in var(--loop) ease-out infinite; animation-delay: calc(var(--i) * var(--hold) + var(--d, 0s)); }}
@keyframes in {{ 0% {{ opacity: 0; }} 1.2% {{ opacity: 1; }} 19% {{ opacity: 1; }} 20% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}

.w__frame {{ fill: none; stroke: #4a5146; stroke-width: 0.9; }}
.w__bg {{ fill: {BG}; }}
.w__panel {{ fill: {PANEL}; }}
.w__dim {{ fill: #4a5146; }}
.w__ink2 {{ fill: #454b41; }}
.w__txt {{ fill: #343a31; }}
.w__block {{ fill: #1e221b; stroke: #353b32; stroke-width: 0.8; }}
.w__card {{ fill: #181b15; stroke: #353b32; stroke-width: 0.8; }}
.w__hue {{ fill: var(--c); }}
.w__ink {{ fill: #9aa194; }}
.w__ring {{ fill: none; stroke: var(--c); stroke-width: 0.8; }}
.w__lead {{ fill: none; stroke: var(--c); stroke-width: 0.8; stroke-dasharray: 2 3; }}
.w__spoke {{ fill: none; stroke: #353b32; stroke-width: 0.9; }}
.w__flow {{ fill: none; stroke: var(--c); stroke-width: 1.2; stroke-dasharray: 7 12;
  animation-name: in, flow; animation-duration: var(--loop), 1.6s; animation-timing-function: ease-out, linear;
  animation-iteration-count: infinite; animation-delay: calc(var(--i) * var(--hold) + var(--d, 0s)), 0s; }}
@keyframes flow {{ to {{ stroke-dashoffset: -19; }} }}
.w__dot {{ fill: #454c42; }}
.w__erase {{ fill: {BG}; }}
.w__new {{ fill: #9aa194; }}
.w__cta {{ fill: {BG}; }}
.w__ripple {{ fill: none; stroke: var(--c); stroke-width: 0.9; transform-box: fill-box; transform-origin: center; animation-name: ripple; }}
@keyframes ripple {{ 0% {{ opacity: 0.9; transform: scale(1); }} 4% {{ opacity: 0; transform: scale(1.5); }} 100% {{ opacity: 0; transform: scale(1.5); }} }}
.w__scan {{ fill: var(--c); opacity: 0; animation: scan var(--loop) linear infinite; animation-delay: calc(var(--i) * var(--hold) + var(--d, 0s)); }}
@keyframes scan {{ 0% {{ opacity: 1; transform: translateY(0); }} 11% {{ opacity: 1; transform: translateY(155px); }} 11.5% {{ opacity: 0; transform: translateY(155px); }} 100% {{ opacity: 0; transform: translateY(155px); }} }}
.w__cursor {{ fill: {INK}; stroke: {BG}; stroke-width: 0.8; opacity: 0; animation: point var(--loop) ease-in-out infinite; animation-delay: calc(var(--i) * var(--hold) + var(--d, 0s)); }}
@keyframes point {{ 0% {{ opacity: 1; transform: translate(196px, 172px); }} 6.5% {{ opacity: 1; transform: translate(100px, 101px); }}
  7.2% {{ transform: translate(100px, 102.5px); }} 8% {{ transform: translate(100px, 101px); }}
  18% {{ opacity: 1; transform: translate(100px, 101px); }} 19% {{ opacity: 0; transform: translate(100px, 101px); }} 100% {{ opacity: 0; transform: translate(100px, 101px); }} }}
.w__verdict {{ fill: var(--c); transform-box: fill-box; transform-origin: left center; animation-name: draw; }}
@keyframes draw {{ 0% {{ opacity: 1; transform: scaleX(0); }} 4% {{ opacity: 1; transform: scaleX(1); }} 19% {{ opacity: 1; transform: scaleX(1); }} 20% {{ opacity: 0; transform: scaleX(1); }} 100% {{ opacity: 0; transform: scaleX(1); }} }}

.k__key {{ fill: {PANEL}; stroke: {LINE}; stroke-width: 0.9; }}
.k__lbl {{ fill: #7d8478; font-family: {MONO}; font-size: 11px; text-anchor: middle; }}
.k__trail {{ fill: var(--c); opacity: 0; animation: trail var(--loop) linear infinite; animation-delay: calc(var(--i) * var(--hold) + var(--d, 0s)); }}
@keyframes trail {{ 0% {{ opacity: 0; }} 0.2% {{ opacity: 0.3; }} 11.6% {{ opacity: 0.3; }} 12.6% {{ opacity: 0; }} 100% {{ opacity: 0; }} }}
.k__flash {{ opacity: 0; animation: key var(--loop) linear infinite; animation-delay: calc(var(--i) * var(--hold) + var(--d, 0s)); }}
.k__flash rect {{ fill: var(--c); }}
.k__on {{ fill: {BG}; font-weight: 600; }}
@keyframes key {{ 0% {{ opacity: 1; transform: translateY(1px); }} 1.6% {{ opacity: 0; transform: translateY(0); }} 100% {{ opacity: 0; transform: translateY(0); }} }}

@media (prefers-reduced-motion: reduce) {{
  .say, .run, .cover, .cur, .art__on, .b, .w__scan, .w__cursor, .k__flash, .k__trail {{ animation: none; }}
  [style^="--i:0"].say, [style^="--i:0"].run, [style^="--i:0"].art__on, [style^="--i:0"].art__on .b {{ opacity: 1; }}
  .cover {{ transform: scaleX(0); }}
  .w__erase, .w__ripple {{ opacity: 0; }}
}}
"""


# ── the readout ────────────────────────────────────────────────────
def readout():
    out = [
        f'<text x="40" y="{SAY_Y}" font-family="{MONO}" font-size="20" fill="{DIM}">you say</text>',
        f'<text x="40" y="{RUN_Y}" font-family="{MONO}" font-size="20" fill="{DIM}">it runs</text>',
    ]
    for i, (say, run, c) in enumerate(PAIRS):
        out.append(f'<text class="say" style="--i:{i}" x="{RX}" y="{SAY_Y}" font-family="{MONO}" font-size="26" fill="{INK}">{esc(say)}</text>')
    for i, (say, run, c) in enumerate(PAIRS):
        x0 = RX + 2 * CH
        cw = cover_w(run)
        out.append(
            f'<g class="run" style="--i:{i}">'
            f'<text x="{RX}" y="{RUN_Y}" font-family="{MONO}" font-size="26" fill="{BLU}">›</text>'
            f'<text x="{f(x0)}" y="{RUN_Y}" font-family="{MONO}" font-size="26" font-weight="700" fill="{c}" '
            f'textLength="{f(len(run) * CH)}" lengthAdjust="spacing">{esc(run)}</text>'
            f'<rect class="cur" x="{f(x0 + len(run) * CH + 6)}" y="{RUN_Y - 21}" width="13" height="25" fill="{c}"/>'
            f'<rect class="cover" x="{f(x0 - 2)}" y="{RUN_Y - 25}" width="{f(cw)}" height="33"/>'
            f"</g>"
        )
    return out


# ── art: keys ──────────────────────────────────────────────────────
def keys_art():
    K, P = 22, 26
    rows, offs = ["qwertyuiop-", "asdfghjkl", "zxcvbnm/"], [9, 16, 29]
    at, parts = {}, []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            at[ch] = (offs[r] + c * P, 55 + r * P, K)
    enter = (16 + 9 * P, 55 + P, 44)
    space = (90, 55 + 3 * P, 120)
    for ch, (x, y, w) in list(at.items()) + [("⏎", enter), ("", space)]:
        parts.append(f'<rect class="k__key" x="{x}" y="{y}" width="{w}" height="{K}"/>')
        if ch:
            parts.append(f'<text class="k__lbl" x="{f(x + w / 2)}" y="{f(y + K / 2 + 3.8)}">{esc(ch)}</text>')
    trails, flashes = [], []
    for i, (_, run, c) in enumerate(PAIRS):
        cw = cover_w(run)
        hits = []
        for j, ch in enumerate(run):
            if ch not in at:
                continue
            step = math.ceil(14 * ((j + 1) * CH + 2) / cw)
            hits.append((at[ch], ch, LOOP * (0.03 + step * 0.05 / 14)))
        hits.append((enter, "⏎", LOOP * 0.088))
        for (x, y, w), ch, d in hits:
            st = f'--i:{i}; --d:{d:.3f}s; --c:{c}'
            trails.append(f'<rect class="k__trail" style="{st}" x="{x}" y="{y}" width="{w}" height="{K}"/>')
            flashes.append(
                f'<g class="k__flash" style="{st}"><rect x="{x}" y="{y}" width="{w}" height="{K}"/>'
                f'<text class="k__lbl k__on" x="{f(x + w / 2)}" y="{f(y + K / 2 + 3.8)}">{esc(ch)}</text></g>'
            )
    return parts + trails + flashes


# ── art: the work ──────────────────────────────────────────────────
def R(x, y, w, h, cls, d=None):
    st = f' style="--d:{d}s"' if d is not None else ""
    return f'<rect class="{cls}" x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"{st}/>'


def Pth(dd, cls, d=None):
    st = f' style="--d:{d}s"' if d is not None else ""
    return f'<path class="{cls}" d="{dd}"{st}/>'


def work_art():
    hue = [c for _, _, c in PAIRS]
    g = []

    # /seo-audit — a page scanned, issues flagged, checklist ticked
    v = [R(36, 20, 150, 170, "w__frame"), Pth("M36,32 H186", "w__frame")]
    v += [R(x, 24.5, 3.5, 3.5, "w__dim") for x in (41, 47, 53)]
    v += [R(46, 42, 90, 7, "w__ink2")]
    v += [R(x, y, w, 3, "w__txt") for x, y, w in ((46, 56, 120), (46, 64, 110), (46, 72, 96))]
    v += [R(46, 84, 60, 40, "w__block")]
    v += [R(x, y, w, 3, "w__txt") for x, y, w in ((114, 86, 58), (114, 94, 50), (114, 102, 56), (114, 110, 40))]
    v += [R(x, y, w, 3, "w__txt") for x, y, w in ((46, 134, 124), (46, 142, 118), (46, 150, 100), (46, 158, 84), (46, 166, 110))]
    v += [R(36, 33, 150, 1.2, "w__scan", 0.1)]
    for k, (x, y, d) in enumerate(((166, 58, 0.35), (104, 104, 0.8), (154, 150, 1.25))):
        v += [
            R(x - 3, y - 3, 6, 6, "b w__hue", d),
            R(x - 7, y - 7, 14, 14, "b w__ring", d),
            Pth(f"M{x + 7},{y} H198", "b w__lead", round(d + 0.08, 2)),
            R(200, y - 4, 8, 8, "w__frame"),
            R(214, y - 1.5, (62, 50, 56)[k], 3, "w__txt"),
            R(201.5, y - 2.5, 5, 5, "b w__hue", round(d + 0.15, 2)),
        ]
    g.append(v)

    # /cro — a landing page; the cursor finds the button, it fills
    v = [R(56, 20, 160, 170, "w__frame"), Pth("M56,34 H216", "w__frame"), R(62, 24, 7, 7, "w__dim")]
    v += [R(x, 26, w, 3, "w__txt") for x, w in ((168, 12), (184, 12), (200, 10))]
    v += [R(66, 46, 92, 8, "w__ink2"), R(66, 58, 70, 8, "w__ink2")]
    v += [R(66, 74, 96, 3, "w__txt"), R(66, 81, 80, 3, "w__txt")]
    v += [R(66, 92, 52, 16, "w__frame"), R(66, 92, 52, 16, "b w__hue", 1.05), R(76, 99, 32, 2.5, "w__cta"), R(66, 92, 52, 16, "b w__ripple", 1.05)]
    v += [R(158, 46, 48, 62, "w__block")]
    for x in (66, 112, 158):
        v += [R(x, 124, 40, 30, "w__card"), R(x, 160, 34, 3, "w__txt"), R(x, 167, 26, 3, "w__txt")]
    v += [Pth("M0,0 L0,13 L3.6,9.6 L6.2,15.4 L8.6,14.3 L6,8.6 L11,8.6 Z", "w__cursor", 0.15)]
    g.append(v)

    # /copy-deslop — copy with its AI tells struck and rewritten
    v = [R(58, 22, 184, 166, "w__frame"), R(70, 36, 96, 7, "w__ink2")]
    for r in range(10):
        rnd = lcg(40 + r)
        y, x = 56 + r * 12, 70
        while x < 226:
            w = min(226 - x, 18 + math.floor(rnd() * 34 + 0.5))
            if w > 6:
                v.append(R(x, y, w, 3.5, "w__txt"))
            x += w + 5
    for x, y, w, d in ((93, 68, 44, 0.3), (70, 104, 52, 0.6), (150, 140, 40, 0.9)):
        v += [
            R(x - 1, y + 5, w + 2, 1.4, "b w__hue", d),
            R(x - 1, y + 1.2, w + 2, 1.1, "b w__hue", round(d + 0.3, 2)),
            R(x - 2, y - 2, w + 4, 9, "b w__erase", round(d + 0.75, 2)),
            R(x, y, math.floor(w * 0.6 + 0.5), 3.5, "b w__new", round(d + 0.85, 2)),
            R(248, y - 1, 5, 5, "b w__hue", d),
        ]
    g.append(v)

    # /content-strategy — a hub, its spokes and the posts around it
    v = []
    for k in range(6):
        a = math.radians(k * 60 - 90)
        x, y, d = 150 + 62 * math.cos(a), 105 + 62 * math.sin(a), round(0.2 + k * 0.14, 2)
        tx = x + (10 if math.cos(a) >= -0.1 else -34)
        v += [
            Pth(f"M150,105 L{f(x)},{f(y)}", "w__spoke"),
            Pth(f"M150,105 L{f(x)},{f(y)}", "b w__flow", d),
            R(x - 6, y - 6, 12, 12, "w__frame w__bg"),
            R(x - 4, y - 4, 8, 8, "b w__hue", round(d + 0.2, 2)),
            R(tx, y - 4, 24, 2.5, "b w__txt", round(d + 0.3, 2)),
            R(tx, y + 1.5, 16, 2.5, "b w__txt", round(d + 0.3, 2)),
        ]
    for k in range(18):
        a = math.radians(k * 20 - 80)
        x, y = 150 + 92 * math.cos(a) * 1.25, 105 + 92 * math.sin(a) * 0.95
        v.append(R(x - 2, y - 2, 4, 4, "b w__dot", round(1.1 + k * 0.035, 3)))
    v += [R(140, 95, 20, 20, "w__frame w__bg"), R(143, 98, 14, 14, "b w__hue", 0.05)]
    g.append(v)

    # /marketing-council — seats round a table, each speaks, a verdict
    v = [R(92, 80, 116, 50, "w__frame w__panel")]
    for k, (x, y, up) in enumerate(((109, 60, 1), (150, 60, 1), (191, 60, 1), (129, 150, 0), (171, 150, 0))):
        d = round(0.2 + k * 0.2, 2)
        ty = y - 16 if up else y + 12
        v += [
            R(x - 7, y - 7, 14, 14, "w__frame w__bg"),
            R(x - 4, y - 4, 8, 8, "b w__ink", d),
            Pth(f"M{x},{y + 8} V80" if up else f"M{x},{y - 8} V130", "b w__lead", d),
            R(x - 2.5, ty, 5, 5, "b w__hue", round(d + 0.08, 2)),
            R(x + 4, ty, 5, 5, "b w__hue", round(d + 0.16, 2)),
        ]
    v += [R(110, 102, 80, 4, "w__txt"), R(110, 102, 80, 4, "b w__verdict", 1.35), R(196, 100.5, 7, 7, "b w__hue", 1.75)]
    g.append(v)

    return [f'<g class="art__on" style="--i:{i}; --c:{hue[i]}">' + "".join(v) + "</g>" for i, v in enumerate(g)]


# ── the panel ──────────────────────────────────────────────────────
def panel(name, title, desc, headline, subtitle, art):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">',
        f'<title id="t">{esc(title)}</title>',
        f'<desc id="d">{esc(desc)}</desc>',
        f"<style>{CSS}</style>",
        f'<rect width="{W}" height="{H}" rx="18" fill="{BG}"/>',
        f'<defs><pattern id="dots" width="36" height="36" patternUnits="userSpaceOnUse"><circle cx="1.4" cy="1.4" r="1.4" fill="#1d211b"/></pattern></defs>',
        f'<rect width="{W}" height="{H}" rx="18" fill="url(#dots)" opacity=".55"/>',
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="17" fill="none" stroke="{LINE}"/>',
        f'<text x="40" y="50" font-family="{MONO}" font-size="18" letter-spacing="2.4" fill="{DIM}">YOU SAY → IT RUNS</text>',
        f'<text x="{W - 40}" y="50" text-anchor="end" font-family="{MONO}" font-size="18" fill="{MUT}">{esc(subtitle)}</text>',
        f'<rect x="40" y="130" width="12" height="12" fill="{ACC}"/>',
        f'<text x="66" y="144" font-family="{SANS}" font-size="40" font-weight="800" letter-spacing="-0.8" fill="{INK}">{esc(headline)}</text>',
        f'<path d="M40,206 H600" stroke="{LINE}"/>',
        f'<path d="M640,86 V354" stroke="{LINE}"/>',
    ]
    parts += readout()
    parts.append(f'<g transform="translate({ART_X} {ART_Y}) scale({ART_S})">' + "".join(art) + "</g>")
    parts.append("</svg>")
    (OUT / f"motion-{name}.svg").write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    panel(
        "keys",
        "Type it, it runs",
        "Five phrases a marketer says, each with the command that answers it: audit the whole site runs /seo-audit, "
        "this page isn't converting runs /cro, sounds like AI wrote it runs /copy-deslop, the blog brings no leads "
        "runs /content-strategy, what would Ogilvy say runs /marketing-council. A keyboard lights each key as the "
        "command types, in the command's colour, and Enter flashes when it runs.",
        "Type it. It runs.",
        "every command, typed",
        keys_art(),
    )
    panel(
        "work",
        "What each skill hands back",
        "The same five phrases and commands, each beside a small wireframe of what the skill hands back, building "
        "itself: /seo-audit scans a page and flags three problems, /cro finds the button and presses it, "
        "/copy-deslop strikes out AI-sounding phrases and rewrites them, /content-strategy grows a content hub, "
        "/marketing-council seats five voices that speak and reach a verdict.",
        "It does the work.",
        "what each skill hands back",
        work_art(),
    )
