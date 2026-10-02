# Changelog

Releases are tagged on `master`; notes live here and on the GitHub release.

## v1.1.5 — 2026-10-02

**`/cinemagraph` encodes flat art lossless.** `render_loop.py` wrote lossy WebP only, and on a flat diagram loop (white ground, thin connectors, small text; 1320 × 680, three beats of 2.8 s, 84 frames at 100 ms) the default output missed the skill's own 1 MB hero budget. The renderer now always merges identical consecutive frames (the 84 rendered frames were stored as 74, with 100/200/500 ms durations and the same total time) and, unless `--lossless` or `--quality` is given, encodes both ways, prints both sizes and keeps the smaller file, preferring lossless when it is within about 10% because it is pixel-exact. On that loop: lossy q82 1.13 MB (the old default), lossy q75 0.93 MB, lossy q82 with merged frames 0.49 MB, lossless 0.59 MB, lossless with merged frames 0.43 MB. The weight advice for flat art is now lossless first, then fewer frames, then a smaller canvas; lowering quality is no longer the first move.

**Fix: the choreographed reset is timed in frames, so beats no longer snap.** The rule said everything fades out "over the last 5% of the beat". With `F` frames per beat the last rendered frame sits at `q = (F−1)/F`, so at `F = 28` a 0.95–1.0 fade lasts 1.6 frames and is still about 68% lit on the beat's last frame: every beat snapped back to rest, and `--check` reported a wrap step 21.9× the typical one. `SKILL.md` and the motion vocabulary now say the reset spans at least 3 frames and ends by `(F−1)/F` (at `F = 28`: `q` 0.84–0.96), and that a fade-in shorter than one frame renders as a cut, which is acceptable for a light piece.

**`--check` catches snaps anywhere in the loop.** It compared only the last frame with frame 0, so a snap at an inner beat boundary went unflagged; this one was caught only because the wrap is also a beat boundary. It now reports the largest step anywhere in the loop with its frame index, flags a lone step more than 3× the median step and above 0.05 as a snap (a step inside a fade spread over three or more frames is not one) with a hint that a reset must finish by the beat's last frame, and decodes the written WebP to confirm the stored frame count, the total duration and, for lossless, pixel equality with the rendered frames. Two new tests: `tests/test_webp_encoding.py` (the kept file is no larger than the lossy one, a lossless file decodes pixel-exact, the duration is frames × duration) and `tests/test_max_step.py` (a too-short reset is flagged, one that ends by the last frame passes). When rebuilding a merged WebP's timeline with Pillow, read `im.info["timestamp"]` after `load()` for each frame; `im.info["duration"]` is None on frame 0 before that, so a duration sum runs off by one and reports false mismatches.

## v1.1.4 — 2026-09-30

**`/writing-assistant` finds work voices in your workspace.** A work voice (company blog, employer content) is now a markdown file in the workspace it belongs to, marked `pack: voice` in its front-matter, with a `voice` name, an optional `company`, and an optional `extends` pointing at a broader voice it builds on (for example a workspace baseline under per-company voices). The skill no longer reads a routing file inside its own folder. With several voices it picks the one for the company the piece is about and asks when that is unclear. Blank sections fall back to the voice it extends, then to a plain professional register, and never to the personal voice. The personal voice is unchanged. Work voices in the old location (`references/<client>-voice.local.md`) still work during the move, but only from a directory whose path contains the client's name; move them into your workspace with the new front-matter.

## v1.1.3 — 2026-09-30

**Reporting skills keep company packs in your workspace, not in the library.** `/pipeline-analysis`, `/marketing-monthly`, and `/campaign-report` no longer store or list context packs inside their own folders. They search the directory you launch from for markdown files whose front-matter says `pack: reporting` (with `company` and optional `aliases`), take company and period as arguments in any order (`/marketing-monthly September Acme`, `/pipeline-analysis Q3 Acme`), and always confirm both in one question. Without arguments they list the companies they found and propose a period. New packs are created in the workspace, with `pipeline-analysis`'s three engine files in a `reporting/` folder beside the pack. `/marketing-monthly` now proposes the last full month instead of the running month. Why: every workspace on a machine could see, and load, every other workspace's pack, and a pack file sitting in the library's working tree was one misnamed file away from a public commit. Packs in the old location (`references/<client>-context.local.md`) still work during the move, but only from a directory whose path contains the client's name; move them into your workspace and add the front-matter from `context-pack.TEMPLATE.md`.

**`/linkedin-ads` and `/content-strategy` follow the same rule.** Both already read company context from the launch directory first. Their optional machine-local packs (`references/<client>-context.local.md`) are now legacy: offered only when the client's name appears in the launch directory's path, with an offer to move them into the workspace. Neither skill saves company context in its own folder.

**`/cinemagraph`: GIF guidance for choreographed loops.** The skill no longer says a long choreographed GIF is usually too heavy. With flat art and one beat moving at a time, the GIF stores only the part of each frame that changed and merges identical frames, so 13 s loops at 1080 × 1080 came to 0.6–1.5 MB. Gradients, photos, and whole-canvas motion still call for the WebP or the CSS-animated SVG. The skill now also says to check the destination’s GIF limits before rendering.

## v1.1.2 — 2026-09-29

**Fix: `/cinemagraph` GIFs keep every beat’s colour.** `render_loop.py --gif` built the GIF’s 256-colour palette from two frames, the first and the middle one. A colour that appeared on neither frame was swapped for the nearest one that did. In a choreographed loop, where each beat has its own accent, that meant whole beats rendered in the wrong hue: in a five-beat test loop, amber came out green, and coral and violet came out blue. The palette is now sampled from frames spread evenly across the loop (as many as fit in about 40 megapixels). A new test, `tests/test_gif_palette.py`, renders a five-beat loop with one hue per beat and fails if any beat changes colour in the GIF. WebP output was never affected. If you made a GIF of a multi-colour loop with an earlier version, render it again.

**`/cinemagraph` gets a second intensity.** Next to *ambient* (one to three quiet layers, noticed on the second look), *choreographed* acts the image's own content out one beat at a time, like a product demo loop: each beat lights its part of the image, stages a staggered build, holds the result and resets, so dozens of pieces move per loop but only one beat plays at once. Intake now asks for the intensity next to the mode, and a report that the last loop went unnoticed maps to choreographed. New output: a CSS-animated SVG for vector art, which plays in an `<img>` and in GitHub READMEs at a few tens of KB whatever the loop length.

## v1.1.1 — 2026-09-15

**Visual category completed.** `/beautify-github-readme` and `/frontend-design-anti-slop` move from Marketing Ops into `skills/Visual/`, next to `/cinemagraph`. No skill content changed; the Presence block in the README is dissolved into the Visual section. Existing junctions or symlinks made by an earlier `install.ps1` / `install.sh` run point at the old paths: re-run the installer once after pulling.

## v1.1.0 — 2026-09-15

**New category: Visual** (`skills/Visual/`). Skills that produce or transform visual assets rather than text or analysis.

**New skill: `/cinemagraph`.** Turns a static image (hero, chart, diagram, screenshot) into a subtle seamless loop, delivered as an animated WebP with a static PNG fallback, or a GIF for READMEs. Two modes, confirmed at intake:

- **Light** keeps the image visually identical and moves only what is already in it: dots march, a marker pulses, a hatch drifts, a highlight flows along a connector.
- **Heavy** may add new moving elements (a scan line, a drawn path, particles, a counter) while keeping about 95% of the original untouched.

Three techniques (overlay, region loop, redraw), a motion vocabulary with phase formulas, a phase-stepping renderer (`render_loop.py`) whose `--check` verifies the loop seam, the moving region and the file weight, and an image probe that reports palette and a type guess. Two worked examples and three eval prompts ship with it.

## v1.0.0 — 2026-09-09

Public release baseline: 48 skills in three categories (Writing, SEO, Marketing Ops). History before this tag was squashed.
