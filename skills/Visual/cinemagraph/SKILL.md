---
name: cinemagraph
description: Turn a static image (chart, diagram, hero graphic, illustration, screenshot, poster) into a subtle seamless loop, delivered as an animated WebP plus a static PNG fallback. Two modes — light keeps the image visually identical and moves only what is already there; heavy adds new moving elements while retaining ~95% of the original. Use this whenever a user wants an image "animated", "slightly moving", "alive", "motioned", "a cinemagraph", "an idle loop", "a subtle GIF/WebP", "like my README hero", or asks to make a hero, chart, or diagram move without redesigning it — even if they do not name a file format. Also use when someone has a static hero on a landing page and wants it to feel less flat. Do not use for full motion-graphics explainers, video editing, or when the user wants the image redesigned rather than animated.
compatibility: Python 3 with Pillow and Playwright (Chromium) for rendering. Works on any OS. No API keys.
---

# Cinemagraph

A cinemagraph is a still image in which one or two things move in a seamless loop while everything else stays frozen. The eye reads it as a photograph that happens to be alive. This skill produces that effect from a static source image, for landing-page heroes, README banners, slide covers, social cards, and charts.

The craft is restraint. A good result is one the viewer notices only on the second look. If they see "an animation" before they see the image, it is too much.

## 1. Intake — ask once, then work

Ask one compact question before touching anything, even when the request looks fully specified. The user's answer tells you how far they want the image to change, which is the single decision that shapes everything downstream.

> Which mode do you want?
> **Light** — the image stays visually identical; I only move what is already in it (dots march, a marker pulses, a hatch drifts, a cursor blinks).
> **Heavy** — I may add new moving elements (a scanning line, particles, a drawn-in path, a badge that counts) while keeping about 95% of the image as it is.
> Output defaults to animated WebP plus a static PNG. Say if you need GIF (GitHub READMEs, email) or MP4 instead.

If the user has already stated the mode and output in their request, confirm in one line and proceed. Do not skip the confirmation: "subtle" means different things to different people, and the two modes cost very different amounts of work.

Also find out, from the request or by looking at the file:

- **Do they have the source?** A Figma export, SVG, or HTML makes light mode a ten-minute job. A flat raster (PNG/JPG) means you either overlay motion on top of pixels or redraw the image as vectors. Ask for the source if it plausibly exists.
- **Where will it be embedded?** Hero column, README, slide. This sets the render width and whether alpha matters.

## 2. Read the image before deciding anything

Open the file. Run `scripts/probe_image.py <file>` to get dimensions, aspect ratio, dominant palette, and a guess at whether it is a chart, diagram, UI screenshot, photo, or illustration. Then look at it yourself and write down, in one or two lines each:

- What the image is *about* — the one idea it exists to communicate.
- Which elements already imply motion or state: dotted lines, arrows, cursors, progress markers, loading rings, hatched areas, gradients, wave shapes, nodes in a graph, blinking LEDs, timelines.
- Which elements must stay perfectly still: text, axes, logos, faces, data points. Anything that carries information is off-limits for movement in light mode.

Motion should reinforce the idea, not decorate it. In a chart that says "QA joined late, effort doubled", the moving parts were the "no further work needed" dotted line, the pulse on the decision point, and a slow drift in the wasted-effort hatch. Nothing about the data moved. That is the litmus test for light mode.

## 3. Pick the technique

Three techniques, in order of preference. Choose the cheapest one that reaches the fidelity the mode demands. Details, formulas and pitfalls for each are in `references/techniques.md`.

| Technique | When | Fidelity | Cost |
|---|---|---|---|
| **Overlay** | The moving parts can sit *on top* of the raster without covering anything that changes (a pulse ring around a dot, a glow, a cursor, marching dots drawn over a plain area). | Pixel-perfect: the raster is untouched. | Low. |
| **Region loop** | A repeating texture inside a bounded area should cycle (dots, dashes, hatch, wave). Cut the region, translate it periodically under a mask, blend the edges. | Very high: same pixels, shifted. | Low–medium. |
| **Redraw** | Motion would have to pass *behind* or *through* static content, the raster is too low-res for the target size, or the user has the source anyway. Rebuild the image as HTML/SVG with the same geometry, type and palette, then animate the vector layers. | As high as your redraw. Must pass a side-by-side against the original. | High. |

Light mode may use any of the three as long as the result is visually indistinguishable from the original when paused. Heavy mode usually needs a redraw, because new elements have to interact with the existing ones.

For the redraw, work from measurements, not impressions: read pixel coordinates off the original for every axis, tick, box and label; sample colors with the probe script; match the fonts (most brand systems have them on Google Fonts). Put the original and your redraw side by side at the same size before animating anything. Fix geometry first, type second, color third.

## 4. Choose the motions

Two or three moving layers is the ceiling. One is often enough. Every motion must be periodic so the loop closes: the state at phase 1.0 must equal the state at phase 0.0.

Pick from `references/motion-vocabulary.md`, which lists each motion with its phase formula, what it communicates, and when it is wrong. The ones that read as subtle almost everywhere:

- **March** — dots or dashes travel along their own path by exactly one period per loop.
- **Pulse** — a ring expands and fades from a point; two rings offset by half a phase make it continuous.
- **Drift** — a hatch, grid or texture translates by one period per loop inside its mask.
- **Blink** — a cursor or LED switches on and off on a duty cycle.
- **Breathe** — a glow's opacity or a node's radius follows a sine, ±10% at most.
- **Flow** — a gradient stop or a highlight slides along a line or edge.

Heavy mode adds motions that introduce new content: a **scan** line sweeping a region, a **draw** that traces a path and resets, **particles** rising through an area, a **counter** that ticks up and wraps. Each must still loop cleanly and must not obscure text or data for more than a moment.

Avoid: anything that moves the whole canvas, moves text, changes layout, bounces, or rotates. Avoid idle bobbing on elements that are supposed to be at rest. Avoid two motions at the same frequency next to each other; they read as a glitch.

## 5. Build the phase-parametric page

Start from `assets/template.html`. It is a fixed-size HTML page with a `setPhase(p)` function; every animated property is a pure function of `p` in [0, 1). The renderer steps `p` and screenshots, so the loop is seamless by construction and the frame count is a free choice.

Rules that keep the output clean:

- Fixed canvas size in CSS pixels; render at 1× and let the browser downscale. Retina crispness comes from choosing a canvas about 2× the embed width, not from device scale factor.
- Render **opaque** by default. Put radius, border and shadow in the *host* CSS (the `<img>` or background element), not in the image. Baked alpha corners and shadows produce visible artefacts once the WebP is lossy-compressed and once the page behind has a gradient.
- Use alpha only when the user explicitly needs a floating cut-out, and then test it against the real background.
- Load fonts from Google Fonts or local files and wait for `document.fonts.ready` before the first frame.
- Everything that does not move must be pixel-identical across frames. Do not put randomness, `Date.now()`, or CSS transitions in the page; they break the loop and inflate the file.

## 6. Render

```
python scripts/render_loop.py page.html out.webp --frames 40 --duration 80 --width 1300 --height 820
```

Defaults: 40 frames at 80 ms (3.2 s loop), opaque, WebP quality 82, plus `out.png` (frame 0) written next to it. Flags: `--alpha` for a transparent canvas, `--gif` to also emit a GIF with a shared adaptive palette (add `--dither` if the source has smooth gradients and the 256-color version shows banding; it costs file size and adds faint frame noise, so look at both), `--scale` for device scale factor, `--check` to run the QA below and print the numbers.

Choose the loop length from the slowest motion. A pulse or drift wants 3–4 s; a blink can live inside that; a scan or draw in heavy mode may need 5–6 s. Longer loops cost frames; keep the frame period at 60–100 ms and add frames, not speed.

## 7. Verify before handing over

Run `render_loop.py --check` or do these by hand:

1. **Seam.** The step from the last frame back to frame 0 must look like any other step. Continuous motions (march, drift) make it pixel-identical; a sawtooth motion (a pulse that fades out and restarts) makes it a normal-sized step. `--check` compares the wrap step to the median step and flags anything more than twice as large, which means some property is not periodic in `p`.
2. **Stillness.** Diff frame 0 against frame N/2 and confirm the changed region is only where you intended. A changed pixel in a text label means a font hinting or subpixel issue; snap that element to integer coordinates.
3. **Fidelity (light mode).** Frame 0 side by side with the original at the same size. A reviewer who did not build it should not be able to say which is which.
4. **GIF palette.** A GIF has 256 colors per frame. Flat designs survive that untouched; soft gradients and photos band. Inspect a mid-loop GIF frame at full size, and prefer a smaller canvas or `--dither` over accepting visible steps.
5. **Weight.** Under about 1 MB for a hero, under 2 MB for anything; WebP usually lands at a third of the GIF. If heavy, reduce frames before reducing quality, then reduce canvas size.
6. **In place.** Drop the WebP into the real embed (or a mock of it at the real width) and look at it for ten seconds. If the motion is the first thing you see, cut a layer or halve its amplitude.

## 8. Deliver

Hand over three files with the same basename: the animated WebP (or GIF), the static PNG fallback, and the source HTML. Say in one line what moves and what stays still, and how to regenerate (`render_loop.py` with the same flags). If it goes into a CMS, mention that radius and shadow belong on the host element.

## Worked example

A 1920×1080 PNG line chart: "The cheapest week of your validation is week zero", two curves, a validated-at-week-16 marker, a dotted "no further work" line, a hatched "wasted effort" area. User wanted light mode for a landing-page hero, modelled on a README banner where nodes pulse and dashes drift.

- Source was a raster only, and the motion (dots marching *under* the red curve, hatch drifting *behind* the label) had to pass behind static content, so the technique was a redraw. Geometry read off the pixels, colors sampled, Caladea and Titillium Web loaded from Google Fonts.
- Three motions, all periodic: march on the dotted line (`dashoffset = -p × period`), two pulse rings offset by half a phase on the marker, drift on the hatch pattern (`translate(p × period, 0)`). Curves, fills, axes, labels: still.
- 40 frames at 80 ms, 1300×820 opaque, 0.67 MB WebP. First attempt with an alpha canvas and baked shadow showed corner artefacts on a gradient background; re-rendered opaque with radius and shadow in CSS.

## Worked example 2 (overlay)

A 1920×1080 PNG cycle diagram for a GitHub README: four boxes, numbered badges, thin light connectors with arrowheads on a dark gradient background. Light mode, GIF output.

- The image is *about* a loop, and the only elements that imply motion are the connectors. Text, boxes, badges, background: still.
- Technique: overlay. The connectors are 2 px lines; their rows, columns and corner radius were read off the pixels (`min(r,g,b) > 200` scan along the candidate rows). The raster sits underneath untouched; four SVG paths trace the connector centrelines on top.
- One motion: flow. A 56 px highlight dash (3 px core plus a 9 px faint glow) travels each path from tail to arrowhead once per loop via `stroke-dashoffset = DASH − p × (L + DASH)`, fading in over the first 14% of `p` and out over the last 14% so it never pops.
- 36 frames at 90 ms, 1200×675 (README content width), GIF 0.45 MB with a shared 256-color palette; the dark gradient survived without dither. Seam check: wrap step smaller than the median step.

## Bundled resources

- `scripts/probe_image.py` — size, palette, type guess for the source image.
- `scripts/render_loop.py` — phase-stepping renderer: HTML → WebP/GIF/PNG, with `--check`.
- `assets/template.html` — starting page with `setPhase(p)` wiring and the fixed-canvas boilerplate.
- `references/techniques.md` — overlay, region loop and redraw: how, formulas, pitfalls.
- `references/motion-vocabulary.md` — the motion catalogue with phase formulas and when each is wrong.
