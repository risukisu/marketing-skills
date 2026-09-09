# Hero archive

Every animated hero built for this repo, kept because a later idea sometimes wants an earlier one
back. Each version is a GIF plus the HTML that produced it. Open a `.html` in a browser to see the
static composition; run it through `render.py` (or `render2.py`, which takes frame count and speed
as arguments) to rebuild the GIF.

The **live** hero is `../hero.gif`, built from `v6d-flat.html`. Its maintained source lives at
[`brand/source/hero.html`](../../../brand/source/hero.html).

| Version | Canvas | What it tried | Why it moved aside |
|---|---|---|---|
| `v1-schematic` | 864×1080 | First OS schematic: light panels, constellation, flowing wires | Light ground fought every other risu surface |
| `v2-schematic` | 864×780 | Dark warm ground, three panels, "One marketer's OS." | Panels described the repo (skill counts, provenance, ledger) rather than the value |
| `v3-schematic` | 864×780 | Same frame, copy rewritten as "you say → it runs" | Type too small to read at GitHub width |
| `v4-pixel-wordmark` | 1200×1140 | Scaled up, headline became a pixel wordmark reading "AI MARKETER'S OS" | Rounded cards, colored top bars and pill chips all read as template |
| `v5a-antislop` | 1200×900 | Built to the `/frontend-design-anti-slop` rules: a real session transcript beside a numbered index | Product-first, but lost the schematic character |
| `v5b-router` | 1200×1100 | The tagline becomes a live prompt; a pulse travels the wire into the panel that answers | Clever, but the motion outran the message |
| `v5c-boot` | 1200×800 | The OS boots: a POST log reporting each category, then a prompt | Fun, further from the rest of the system |
| `v6d-flat` | 1200×1170 | v3's composition, flattened: hairline columns, square markers, icon connector strip | **Live.** Shipped as `hero.gif` |
| `v6e-bento` | 1200×930 | The same content as a twelve-column bento grid of tiles | Tiles reintroduced the rounded-card look v6d removed |

## Rebuilding one

```powershell
cd assets\readme\archive
python render.py v3-schematic.html out.gif out.png 864 780
python render2.py v5c-boot.html out.gif out.png 1200 800 72 90 0.98
```

`render.py` takes `SRC OUT PREVIEW W H`. `render2.py` adds `FRAMES DUR_MS PREVIEW_PHASE`. Both drive
a headless Chromium through the page's `setPhase(p)` hook, where `p` runs 0 to 1 across the loop, so
every frame is deterministic and the loop closes seamlessly. They need `playwright` and `pillow`.

`risu-favicon.png` is the pixel squirrel from [risu.pl](https://risu.pl), referenced by the later
versions.
