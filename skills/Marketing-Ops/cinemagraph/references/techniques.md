# Techniques: overlay, region loop, redraw

Pick the cheapest technique that reaches the fidelity the mode demands. Light mode requires that a paused frame is indistinguishable from the original; heavy mode requires that about 95% of the original survives untouched.

## Overlay

Place the untouched raster as the base layer and draw the moving parts on top in an SVG that shares its coordinate space.

**When it works:** the motion sits over a plain or uniform area (a pulse ring around a marker on a white ground, a cursor at the end of a line, a glow behind a node, marching dots along an existing dotted line where you paint *over* the dots with an identical dot pattern).

**How:**
1. Load the raster at its native pixel size; set the canvas to the same size (or an integer multiple).
2. Read anchor coordinates off the raster. Zoom in and note the pixel positions of the elements you will overlay. Do not estimate.
3. Sample the colors you will draw with from the raster itself (`probe_image.py`, or read the pixel).
4. For an existing repeating element (dots, dashes) you want to animate, first cover the original run with a rectangle in the *background* color sampled from around it, then draw your own dashed line at the same geometry and animate its `stroke-dashoffset`. The cover only works over a flat area; over a gradient use a region loop instead.

**Pitfalls:** antialiasing differences between the raster's dots and your vector dots show as a slight weight change. Match stroke width to the pixel measurement, not the nominal design value. Over JPEG sources, sample the cover color from several pixels and average.

## Region loop

Cut a rectangular (or masked) region that contains a repeating texture and translate a copy of it under a mask by one texture period per loop.

**When it works:** hatches, grids, dashed borders, wave strips, conveyor-like rows, ticker text, dotted leader lines on non-flat backgrounds.

**How:**
1. Measure the period of the texture in pixels (distance between repeats). It must divide evenly or the seam shows.
2. In the SVG, define a `<clipPath>` equal to the region. Inside it place an `<image>` of the raster twice (or a `<pattern>` built from the cut region), offset by one period.
3. `setPhase(p)` translates the group by `p × period` along the texture's direction. At `p = 1` the copy lands exactly where the original was: seamless.
4. Where the region border is not a clean edge, feather it with a gradient mask of 4–8 px so the moving texture blends into the still one.

**Pitfalls:** any element inside the region that is *not* part of the texture (a label sitting on the hatch) will move too. Either mask it out and redraw it on top, or shrink the region. Perspective textures do not have a constant period; skip them.

## Redraw

Rebuild the image as HTML/SVG with the same geometry, typography and palette, then animate the vector layers directly.

**When it is the only option:** the motion passes behind or through static content; the raster is too small for the target width; the design has soft shadows or gradients that a cover would break; or heavy mode needs new elements woven into the existing ones. Also the right call when the user has the source file: import it and skip the measuring.

**How, from a raster only:**
1. Measure. For a chart: axes origin, extents, tick positions, the pixel coordinates of every labelled point, curve inflection points. For a diagram: box corners, connector endpoints, arrowheads. Write them down as a table before drawing.
2. Sample colors from the raster (`probe_image.py --colors 12`, and read specific pixels for strokes and fills). Note opacities for fills over white by comparing to the background.
3. Identify fonts. Serif headline plus humanist sans body is common in brand systems; check the brand's design tokens if you have them, otherwise match x-height and weight visually from Google Fonts candidates.
4. Draw in SVG using a viewBox equal to the source pixel size, so measured coordinates transfer directly. Generate curves from a formula that fits the measured points rather than hand-tracing; it is faster and smoother.
5. Compare side by side at equal size. Fix geometry, then type, then color. Stop when a reviewer cannot tell which is which.
6. Only now add motion.

**Pitfalls:** it is tempting to "improve" the design while redrawing. Do not, unless the user asked. Light mode means identical. Keep a copy of the original next to the source HTML so future edits can re-check fidelity.

## Alpha or opaque

Render opaque by default. Give the host element (`<img>`, CSS background, card) the radius, border and shadow. Reasons: lossy WebP and GIF palette reduction both produce visible fringes on transparent rounded corners and soft shadows; a gradient behind the image makes those fringes obvious; and opaque frames compress smaller.

Use alpha only for genuinely floating cut-outs (an icon, a product shot) and test it against the real background at the real size before delivering.
