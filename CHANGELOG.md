# Changelog

Releases are tagged on `master`; notes live here and on the GitHub release.

## v1.1.0 — 2026-09-15

**New category: Visual** (`skills/Visual/`). Skills that produce or transform visual assets rather than text or analysis.

**New skill: `/cinemagraph`.** Turns a static image (hero, chart, diagram, screenshot) into a subtle seamless loop, delivered as an animated WebP with a static PNG fallback, or a GIF for READMEs. Two modes, confirmed at intake:

- **Light** keeps the image visually identical and moves only what is already in it: dots march, a marker pulses, a hatch drifts, a highlight flows along a connector.
- **Heavy** may add new moving elements (a scan line, a drawn path, particles, a counter) while keeping about 95% of the original untouched.

Three techniques (overlay, region loop, redraw), a motion vocabulary with phase formulas, a phase-stepping renderer (`render_loop.py`) whose `--check` verifies the loop seam, the moving region and the file weight, and an image probe that reports palette and a type guess. Two worked examples and three eval prompts ship with it.

## v1.0.0 — 2026-09-09

Public release baseline: 48 skills in three categories (Writing, SEO, Marketing Ops). History before this tag was squashed.
