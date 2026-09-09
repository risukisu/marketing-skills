# marketing-skills — visual system

> **Status: CANONICAL** (os-schematic, adopted 2026-09-06). Everything the README shows is
> generated from this folder. The earlier constellation kit (violet, v1, 2026-07-24) and the
> ascii-bloom exploration were retired the same day; both remain in git history.

**Direction: the schematic.** The library is a workbench, so the imagery is a workbench readout on a
warm dark ground: hairline rules instead of cards, square markers instead of pills, a live cursor,
a constellation of skills with dashed current flowing through it. Nothing floats and nothing glows.
The aesthetic is the content, so the graphics say what a marketer types and what runs.

## Palette

| Token | Hex | Role |
|---|---|---|
| Ground | `#0e100d` | every surface starts here, warm near-black |
| Panel | `#151813` | the few filled areas (terminal blocks) |
| Line | `#262b23` | structural rules |
| Line-2 | `#20241d` | row dividers |
| Ink | `#e9ebe3` | headings, values |
| Muted | `#b4bab0` / `#899084` | body, labels |
| Dim | `#5b6156` | metadata, prompts, dot grid |
| Green | `#3fd68c` | category 01, the cursor, "good" values |
| Amber | `#e8a13d` | category 02, the payoff phrase |
| Blue | `#7c8cf0` | category 03, shell prompts |

Three category hues, used only to mark a category. No fourth accent, no gradients, no shadows.

## Motif

A **square**. It marks a category head, a connector, a cursor, a pixel in the wordmark. The dot grid
behind everything is the same square at 1.4px, and the pixel squirrel from
[risu.pl](https://risu.pl) that signs each asset is built from them too. Repeat it lightly; never as
wallpaper.

## Type

System monospace (`Consolas`/`ui-monospace`) for everything except category and headline type, which
is the system sans at weight 800 with tight tracking. Essential text sits at 17px or more on a
1200-unit canvas, so it survives GitHub's 900px column.

## Sources

| File | Builds |
|---|---|
| `source/hero.html` | the animated hero (`assets/readme/hero.gif`, 1200×1170) |
| `source/og-image.html` | the social preview (`assets/readme/og-image.png`, 1200×630) |
| `source/gen_assets.py` | the five section headers and `how-it-works.svg`, straight into `assets/readme/` |
| `source/render.py` | drives headless Chromium over a page's `setPhase(p)` hook to make a seamless GIF |
| `source/risu-favicon.png` | the pixel squirrel, 70px, drawn at 30px |

Rebuild:

```powershell
python brand\source\gen_assets.py
cd brand\source
python render.py hero.html ..\..\assets\readme\hero.gif ..\..\assets\readme\hero.png 1200 1170
```

The social preview is a plain screenshot of `og-image.html` at 1200×630, and GitHub has no API for
it: upload it by hand under repo Settings → Social preview.

Superseded heroes, with the reasoning for each, live in
[`assets/readme/archive/`](../assets/readme/archive/).

## Rules

- **Never bake a count into a graphic.** The number of skills changes; a picture that says "44
  skills" is wrong the next week. Say what the thing does instead.
- **Copy describes the work a marketer gets**, never repo mechanics, provenance, or where a skill
  came from. That belongs in `INVENTORY.md`.
- **Quote the marketer.** Every category row is a phrase someone would actually type, then the
  command that answers it.
- **No rounded cards, no pill chips, no colored top bars, no drop shadows.** They were tried in v2
  through v5 and they read as template. Hairlines and squares carry the structure.
