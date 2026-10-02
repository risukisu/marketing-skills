---
name: cinemagraph
description: Turn a static image (chart, diagram, hero graphic, illustration, screenshot, poster, UI tile) into a seamless loop, delivered as an animated WebP plus a static PNG fallback, or as a CSS-animated SVG for vector art. Two modes (light moves only what is already there; heavy adds elements and keeps ~95% of the original) and two intensities (ambient, a few quiet layers; choreographed, the image acts out its own content beat by beat). Use this whenever a user wants an image "animated", "slightly moving", "alive", "motioned", "a cinemagraph", "an idle loop", "a subtle GIF/WebP", "a demo loop", "like my README hero", or says the last animation was too subtle or nobody noticed it move, even if they do not name a file format. Also use when a static hero feels flat. Do not use for motion-graphics explainers with scene changes or cuts, video editing, or when the user wants the image redesigned rather than animated.
compatibility: Python 3 with Pillow and Playwright (Chromium) for rendering. Works on any OS. No API keys.
---

# Cinemagraph

A cinemagraph is a still image that moves in a seamless loop while its layout stays put. The eye reads it as the image itself, alive. This skill produces that effect from a static source image, for landing-page heroes, README banners, product tiles, slide covers, social cards, and charts.

The craft is control, at one of two intensities, chosen at intake:

- **Ambient** is restraint. One to three quiet layers; a good result is one the viewer notices only on the second look.
- **Choreographed** is staging. The image acts out its own content one beat at a time: a list item lights, its part of the image does its job, the result holds, the next beat starts. Dozens of pieces move per loop, but only inside the beat on stage, so the eye always knows where to look. It is the intensity of a product demo loop, without scene changes: the layout never moves.

Each section below says which of its rules belong to which intensity.

## 1. Intake — ask once, then work

Ask one compact question before touching anything, even when the request looks fully specified. The user's answer tells you how far they want the image to change, which is the single decision that shapes everything downstream.

> Which mode, and how much motion?
> **Light** — the image stays visually identical; I only move what is already in it (dots march, a marker pulses, a hatch drifts, a cursor blinks).
> **Heavy** — I may add new moving elements (a scanning line, particles, a drawn-in path, a badge that counts) while keeping about 95% of the image as it is.
> **Ambient** — one to three quiet layers, noticed on the second look.
> **Choreographed** — the image acts out its own content one beat at a time, like a product demo loop: many moving pieces, one focal beat at a time.
> Output defaults to animated WebP plus a static PNG. Say if you need GIF (email, old tools), MP4, or a CSS-animated SVG (vector art, README banners, long loops at a few tens of KB).

If the user has already stated the mode, intensity and output in their request, confirm in one line and proceed. Do not skip the confirmation: "subtle" means different things to different people, and the combinations cost very different amounts of work.

Map what users say to the intensity. "Subtle", "slightly", "don't redesign", "an idle loop": **ambient**. "Alive", "a demo loop", "more going on", "the last one was too subtle", "nobody noticed it moved": **choreographed**. When they report that an ambient loop went unnoticed, that is the request for choreographed, not proof that the ambient loop worked.

Mode and intensity are independent. Light + choreographed lights up, in sequence, elements that already exist (every node of a diagram, every row of a list); heavy + choreographed adds the pieces each beat needs.

Also find out, from the request or by looking at the file:

- **Do they have the source?** A Figma export, SVG, or HTML makes light mode a ten-minute job. A flat raster (PNG/JPG) means you either overlay motion on top of pixels or redraw the image as vectors. Ask for the source if it plausibly exists.
- **Where will it be embedded?** Hero column, README, slide. This sets the render width and whether alpha matters.

## 2. Read the image before deciding anything

Open the file. Run `scripts/probe_image.py <file>` to get dimensions, aspect ratio, dominant palette, and a guess at whether it is a chart, diagram, UI screenshot, photo, or illustration. Then look at it yourself and write down, in one or two lines each:

- What the image is *about* — the one idea it exists to communicate.
- Which elements already imply motion or state: dotted lines, arrows, cursors, progress markers, loading rings, hatched areas, gradients, wave shapes, nodes in a graph, blinking LEDs, timelines.
- Which elements must stay perfectly still: text, axes, logos, faces, data points. Anything that carries information is off-limits for movement in light mode.
- For choreographed: what the image lists, steps through or pairs up (stages of a funnel, rows of a readout, quotes beside the stages they belong to). Those become the beats, and the parts of the image each one points at become the beat's focal region.

Motion should reinforce the idea, not decorate it. In a chart that says "QA joined late, effort doubled", the moving parts were the "no further work needed" dotted line, the pulse on the decision point, and a slow drift in the wasted-effort hatch. Nothing about the data moved. That is the litmus test for light mode.

## 3. Pick the technique

Three techniques, in order of preference. Choose the cheapest one that reaches the fidelity the mode demands. Details, formulas and pitfalls for each are in `references/techniques.md`.

| Technique | When | Fidelity | Cost |
|---|---|---|---|
| **Overlay** | The moving parts can sit *on top* of the raster without covering anything that changes (a pulse ring around a dot, a glow, a cursor, marching dots drawn over a plain area). | Pixel-perfect: the raster is untouched. | Low. |
| **Region loop** | A repeating texture inside a bounded area should cycle (dots, dashes, hatch, wave). Cut the region, translate it periodically under a mask, blend the edges. | Very high: same pixels, shifted. | Low–medium. |
| **Redraw** | Motion would have to pass *behind* or *through* static content, the raster is too low-res for the target size, or the user has the source anyway. Rebuild the image as HTML/SVG with the same geometry, type and palette, then animate the vector layers. | As high as your redraw. Must pass a side-by-side against the original. | High. |

Light mode may use any of the three as long as the result is visually indistinguishable from the original when paused. Heavy mode usually needs a redraw, because new elements have to interact with the existing ones. A choreographed loop almost always needs one too: every piece needs a resting look and an active look you control.

For the redraw, work from measurements, not impressions: read pixel coordinates off the original for every axis, tick, box and label; sample colors with the probe script; match the fonts (most brand systems have them on Google Fonts). Put the original and your redraw side by side at the same size before animating anything. Fix geometry first, type second, color third.

## 4. Choose the motions

Every motion must be periodic so the loop closes: the state at phase 1.0 must equal the state at phase 0.0. At both intensities text, layout and the canvas itself stay still. `references/motion-vocabulary.md` lists each motion with its phase formula, what it communicates, and when it is wrong.

### Ambient

Two or three moving layers is the ceiling. One is often enough. The motions that read as subtle almost everywhere:

- **March** — dots or dashes travel along their own path by exactly one period per loop.
- **Pulse** — a ring expands and fades from a point; two rings offset by half a phase make it continuous.
- **Drift** — a hatch, grid or texture translates by one period per loop inside its mask.
- **Blink** — a cursor or LED switches on and off on a duty cycle.
- **Breathe** — a glow's opacity or a node's radius follows a sine, ±10% at most.
- **Flow** — a gradient stop or a highlight slides along a line or edge.

Heavy mode adds motions that introduce new content: a **scan** line sweeping a region, a **draw** that traces a path and resets, **particles** rising through an area, a **counter** that ticks up and wraps. Each must still loop cleanly and must not obscure text or data for more than a moment.

Avoid: anything that moves the whole canvas, moves text, changes layout, bounces, or rotates. Avoid idle bobbing on elements that are supposed to be at rest. Avoid two motions at the same frequency next to each other; they read as a glitch.

### Choreographed

A choreographed loop is a sequence of beats, and every beat is built the same way:

1. **Beats.** One per item the image lists or step it shows, 3–6 of them. Each holds 2–3 s, and the loop is beats × hold (5 beats at 2.6 s make a 13 s loop).
2. **Focal region and cast.** Each beat owns one region of the image and the 5–30 pieces that act it out there: the stage's box and connector, the markers, the ticks, the matching quote. Outside that region nothing moves during the beat, except one optional ambient layer.
3. **Staging.** Trigger (0–0.3 s: the label or item that names the beat lights), action (0.3–1.5 s: the pieces arrive in a stagger 0.07–0.4 s apart, so a scan sweeps, markers pop, ticks fill, keys light), result (held until the reset), reset (everything the beat lit fades back to rest over at least 3 frames, finished by the beat's last rendered frame). Time the reset in frames, not in a percentage of the beat: with `F` frames per beat the last frame sits at `q = (F−1)/F` and `q = 1` is never rendered, so the reset ends at or before `(F−1)/F` and starts at least `3/F` earlier. At `F = 28` that is a reset over `q` 0.84–0.96. A reset over "the last 5%" (0.95–1.0) lasts 1.6 frames and is still about two-thirds lit on the last frame, so every beat snaps back to rest.
4. **Resting and active looks.** Every piece has a dim resting look that is always on screen, so the whole layout reads in any frame, and a bright active look in the beat's accent.
5. **Accent per beat.** When the beats are categories (five commands, four stages), each gets its own hue, used for everything that beat lights. Otherwise one accent for all.
6. **Trace.** What the action touched stays at 20–30% opacity until the beat ends, so the result is readable after the action is over.
7. **Sync.** Text that names the beats (a list, a readout, captions) lights in the same window as its beat. The text never moves: it changes colour or weight, or cycles through one fixed slot.

For scale: a four-stage funnel at this intensity lights each stage box in turn, thins a cohort of dots stage by stage with every drop-off marked, stamps a result on each stage, and lights the matching quote beside it. That is 40–60 moving pieces per loop, never more than one stage's worth at once.

## 5. Build the phase-parametric page

Start from `assets/template.html`. It is a fixed-size HTML page with a `setPhase(p)` function; every animated property is a pure function of `p` in [0, 1). The renderer steps `p` and screenshots, so the loop is seamless by construction and the frame count is a free choice.

Rules that keep the output clean:

- Fixed canvas size in CSS pixels; render at 1× and let the browser downscale. Retina crispness comes from choosing a canvas about 2× the embed width, not from device scale factor.
- Render **opaque** by default. Put radius, border and shadow in the *host* CSS (the `<img>` or background element), not in the image. Baked alpha corners and shadows produce visible artefacts once the WebP is lossy-compressed and once the page behind has a gradient.
- Use alpha only when the user explicitly needs a floating cut-out, and then test it against the real background.
- Load fonts from Google Fonts or local files and wait for `document.fonts.ready` before the first frame.
- Everything that does not move must be pixel-identical across frames. Do not put randomness, `Date.now()`, or CSS transitions in the page; they break the loop and inflate the file.

A choreographed loop runs on the same phase, split into beats. With `N` beats, `beat = floor(p × N)` and `q = p × N − beat` is the position inside the beat (0 to 1). Piece `k` of beat `i` has a start `d_k` (a fraction of the beat): it is on when `beat == i` and `q ≥ d_k`. Time the fades in frames: with `F = frames / N` frames per beat, one frame is `1/F` of `q`, the renderer samples `q = 0, 1/F, …, (F−1)/F`, and `q = 1` is never rendered. A fade-in over 0.02–0.05 of `q` is less than one frame at `F = 28` (`1/28 = 0.036`), so it renders as a cut; that is acceptable for a light piece (a label, a key, a tick), while anything the eye tracks fades in over 2–3 frames. The reset spans at least 3 frames and ends by the last rendered frame: `end ≤ (F−1)/F`, `start ≤ end − 3/F`. At `F = 28` that is `q` 0.84–0.96 (the last frame, at `q = 0.964`, is at rest); a reset over 0.95–1.0 is still about 68% lit on that frame and snaps. Keep the cast of every beat in one data array (piece, region, start, accent) and generate the page from it; hand-placed timings drift out of sync the first time a beat is added.

For a vector redraw that ships as a **CSS-animated SVG**, write the same timeline as CSS instead of `setPhase`: one `@keyframes` set whose visible window is the first `1/N` of the loop, `animation-duration` = the loop, and `animation-delay` = `i × hold + d_k` per piece (custom properties on each element keep it to one rule per piece type). No script, so it plays inside an `<img>` tag and in GitHub READMEs. Use system font stacks or outlined text, since an SVG in an `<img>` loads no web fonts.

## 6. Render

```
python scripts/render_loop.py page.html out.webp --frames 40 --duration 80 --width 1300 --height 820
```

Defaults: 40 frames at 80 ms (3.2 s loop), opaque, plus `out.png` (frame 0) written next to it. The WebP always merges identical consecutive frames (a hold costs nothing: 84 rendered frames of a flat diagram loop were stored as 74, with 100/200/500 ms durations and the same total time). With neither `--lossless` nor `--quality` the renderer encodes both lossless and lossy q82, prints both sizes and keeps the smaller, preferring lossless when it is within about 10% because it is pixel-exact. Flat art (white ground, thin lines, text) comes out lossless and far smaller: that 84-frame loop at 1320×680 was 1.13 MB lossy and 0.43 MB lossless. `--lossless` or `--quality N` force one. Other flags: `--alpha` for a transparent canvas, `--gif` to also emit a GIF with one adaptive palette sampled from frames across the whole loop, so every beat's accent keeps its colour (add `--dither` if the source has smooth gradients and the 256-color version shows banding; it costs file size and adds faint frame noise, so look at both), `--scale` for device scale factor, `--check` to run the QA below and print the numbers.

Choose the loop length from the slowest motion. A pulse or drift wants 3–4 s; a blink can live inside that; a scan or draw in heavy mode may need 5–6 s. Longer loops cost frames; keep the frame period at 60–100 ms and add frames, not speed.

A choreographed loop is beats × hold, usually 8–15 s: 80–150 frames at 100 ms. A flat-art WebP stays under 0.5 MB at hero width (lossless, holds merged); soft gradients and photos run 1–2 MB. A GIF works too when the art is flat and only one beat moves at a time: the GIF stores only the part of each frame that changed and merges identical frames, so five-beat, 13 s loops at 1080 × 1080 on a flat dark ground came to 0.6–1.5 MB with 139–188 frames. Soft gradients, photos, or motion spread across the whole canvas every frame make a GIF that long too heavy; then offer the WebP or, for vector art, the CSS-animated SVG, which stays at a few tens of KB whatever the length. Check the destination's limits before rendering: LinkedIn is commonly cited at 5 MB and 250 frames for a GIF. Frames for review come from the browser either way (`--frames` stepping `setPhase`, or, for the SVG, pausing `document.getAnimations()` at a chosen `currentTime`).

## 7. Verify before handing over

Run `render_loop.py --check` or do these by hand. `--check` also decodes the written WebP and confirms the stored frame count and total duration, and for a lossless file, pixel equality with the rendered frames.

1. **Seam and snaps.** The step from the last frame back to frame 0 must look like any other step. Continuous motions (march, drift) make it pixel-identical; a sawtooth motion (a pulse that fades out and restarts) makes it a normal-sized step. `--check` compares the wrap step to the median step and flags anything more than twice as large, which means some property is not periodic in `p`. It also reports the largest step anywhere in the loop with its frame index, and flags a snap: a step more than 3× the median step and above 0.05 that stands alone rather than inside a fade spread over three or more frames. A snap at frame `F−1 → F` is a choreographed reset that did not finish by the beat's last rendered frame (§5); the wrap seam catches it only when the wrap is also a beat boundary.
2. **Stillness.** Diff frame 0 against frame N/2 and confirm the changed region is only where you intended. A changed pixel in a text label means a font hinting or subpixel issue; snap that element to integer coordinates.
3. **Fidelity (light mode).** Frame 0 side by side with the original at the same size. A reviewer who did not build it should not be able to say which is which.
4. **GIF palette.** A GIF has 256 colors per frame. Flat designs survive that untouched; soft gradients and photos band. Inspect a mid-loop GIF frame at full size, and prefer a smaller canvas or `--dither` over accepting visible steps.
5. **Weight.** Under about 1 MB for a hero, under 2 MB for anything; WebP usually lands at a third of the GIF. For flat art, try lossless with merged frames first (the default picks it when it is the smaller; `--lossless` forces it), then fewer frames, then a smaller canvas. Lowering `--quality` is not the fix for flat art: on a flat diagram loop q75 saved 18% and lossless 62%. For gradients and photos, reduce frames before quality, then canvas.
6. **In place.** Drop the WebP into the real embed (or a mock of it at the real width) and watch it. Ambient: look for ten seconds, and if the motion is the first thing you see, cut a layer or halve its amplitude. Choreographed: watch one full loop, then build a contact sheet (each beat frozen at its trigger, mid-action and result, in one grid) and check four things. Each frame has one focal region. Each beat's result is readable before it resets. The resting layout reads in every frame. Text sits still in all of them.

## 8. Deliver

Hand over three files with the same basename: the animated WebP (or GIF, or the CSS-animated SVG), the static PNG fallback, and the source (HTML, or the generator that writes the SVG). Say in one line what moves and what stays still, and how to regenerate (`render_loop.py` with the same flags). If it goes into a CMS, mention that radius and shadow belong on the host element.

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

## Worked example 3 (choreographed)

A dark product tile: a wordmark, a tagline, and a readout that cycles five "you say → it runs" pairs (a phrase a marketer types, then the command that answers it), with an art panel beside it. The first version put a constellation in the panel with a dashed current flowing through it and a blinking cursor. The owner called it too subtle. Heavy + choreographed.

- Five beats, one per pair, 2.6 s each, 13 s loop. The readout's pair is the trigger for its beat; every command has its own hue, and everything its beat lights uses it.
- Keyboard version: 30 dim keys at rest. As the command types in 14 steps, each of its keys lights in the command's hue at the moment its character appears (pieces ~50 ms apart), Enter flashes as the command lands, and the typed keys stay at 30% until the beat ends (trace). About 60 key lights per loop.
- Wireframe version: each beat draws what that skill hands back, as a 10–25-piece build. For `/seo-audit`, a page frame, a scan line sweeping it, three issues flagged with rings and leader lines, and a checklist ticking one box per issue, with pieces arriving 0.1–1.75 s into the beat. Other beats: a cursor finds a button and it fills; phrases get struck and rewritten; a hub grows spokes; five seats speak, then a verdict draws.
- Delivered as CSS-animated SVG: 27–32 KB for the 13 s loop, playing in a GitHub README `<img>`, plus the same markup inline on the live site. Checked with a contact sheet of every beat at +0.35 s, +0.9 s and +2.1 s.

## Bundled resources

- `scripts/probe_image.py` — size, palette, type guess for the source image.
- `scripts/render_loop.py` — phase-stepping renderer: HTML → WebP/GIF/PNG, with `--check`.
- `tests/test_gif_palette.py` — renders a five-beat loop, one hue per beat, and checks that the GIF shows every beat in its hue. Run it after changing the GIF path.
- `tests/test_webp_encoding.py` — renders a small flat loop (`tests/flat_page.py`) and checks that the kept WebP is no larger than the lossy one, that a lossless file decodes pixel-exact against the rendered frames (timeline rebuilt from frame timestamps), and that the total duration is frames × duration.
- `tests/test_max_step.py` — the same flat loop with a reset that runs past the beat's last frame is flagged as a snap; with the reset finished by that frame it passes.
- `assets/template.html` — starting page with `setPhase(p)` wiring and the fixed-canvas boilerplate.
- `references/techniques.md` — overlay, region loop and redraw: how, formulas, pitfalls.
- `references/motion-vocabulary.md` — the motion catalogue with phase formulas and when each is wrong.
