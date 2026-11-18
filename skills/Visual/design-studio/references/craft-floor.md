# Craft floor

The minimum every mock and every build meets, whatever the direction. These numbers are defaults, not a style. A direction may move a style value when its card says why; the accessibility numbers (contrast, sizes, targets, reduced motion) hold regardless. Numbers marked *house default* are this skill's own choices, not a cited standard.

## Type

- Body text is at least 16 px on screens. Documents use 10 to 12 pt and slides at least 24 pt (*house defaults*).
- Body measure is 60 to 75 characters, with 65 as the target.
- Body leading is 1.5 to 1.7. Display leading is 1.0 to 1.2 (*house default*).
- At least one size step between heading and body is 1.25× or more. A flat scale reads as unfinished.
- Display tops out around 6rem. Tracking never goes below −0.04em, and body tracking stays at or under 0.05em.
- Use `text-wrap: balance` on headings and `text-wrap: pretty` on body text.
- Use `font-variant-numeric: tabular-nums` wherever numbers sit in columns or change in place.
- Load only the weights you use. Check that the faces cover the content's scripts by rendering the hardest diacritics and looking at the screenshot; a name check or `document.fonts.check()` is not proof.
- Keep all-caps runs short (under about 80 characters). Never justify text on the web.

## Colour

- Build roles, not swatches: canvas, raised surface, primary text, secondary text, accent or action, focus, border, and status colours (success, warning, error, info).
- Write colours in `oklch()`. Use hue `none` for true greys, and derive variants with `color-mix(in oklch, …)` rather than adding new literals.
- Contrast is at least 4.5:1 for body text and at least 3:1 for large text, controls, icons and focus indicators. Colour is never the only cue.
- Tint the neutrals toward the palette. Compose dark mode rather than inverting light mode: lower chroma near black, a touch more line height and weight for light text on dark.

## Space and layout

- Use a spacing scale on a 4-unit base.
- Keep groups tight and separation generous, and a heading sits closer to what follows it than to what came before.
- Keep four or fewer items per group or decision point. Use one primary action and one or two secondary ones.
- Lay out with a content grid with breakouts instead of nested containers. For repeating items, use an intrinsic grid: `repeat(auto-fit, minmax(min(100%, 16rem), 1fr))`.
- Touch targets are at least 44 px. Inner padding is at least 8 px (12 to 16 px is typical). On mobile, text sits at least 16 px from the viewport edge.

## Motion

- **Easing:** ease-out is `cubic-bezier(0.23, 1, 0.32, 1)` and ease-in-out is `cubic-bezier(0.77, 0, 0.175, 1)`. Avoid `ease-in` for interface motion.
- **Durations:**
  - press: 100–160 ms
  - tooltip: 125–200 ms
  - dropdown: 150–250 ms
  - modal or drawer: 200–500 ms
  - Interface motion stays under 300 ms, except modals and drawers. Exits run faster than entrances.
- **How often it's seen:** something used a hundred times a day gets no animation. Something used tens of times a day gets less. Rare moments are where delight belongs.
- **Entrances:** start entrances at a scale of 0.95 or more (*house default*; Emil's floor is 0.9) together with opacity, never from `scale(0)`. Stagger real lists only, by 30 to 80 ms, with the whole group done in about 300 ms.
- **One moment per page:** a page gets one authored moment, not the same entrance on every section.
- **Hover and press:**
  - Hover rules sit inside `@media (hover: hover) and (pointer: fine)`.
  - Hover motion never moves a neighbouring element.
  - Pressable things scale to 0.95–0.98 on `:active`, and also change colour or background so the press still shows under reduced motion.
- **Reduced motion:** transitions that move or scale sit inside `@media (prefers-reduced-motion: no-preference)`. Opacity and colour feedback stay outside it, so reduced motion means gentler motion, not none.

## States and browser surfaces

- Every control has default, hover, focus-visible, active, disabled, loading and error states.
- Every list has an empty state that says what will appear and how to start.
- Theme the browser surfaces from the palette:
  - text selection
  - caret
  - scrollbars (themed, not reinvented)
  - focus rings
  - link underline offset
  - tabular numerals

  They cost a few lines each, and generated pages almost always leave them at the browser default.

## CSS rules

From good-css (vojtaholik/good-css, MIT), in our own words:

1. Use logical properties (`margin-block-start`, `padding-inline-end`, `inset-block-start`), not physical ones.
2. Use OKLCH colours, with variants from `color-mix`. No second hex, `rgb()` or `hsl()` literal for the same colour.
3. Any size that grows with the screen is a single `clamp()` token of `rem + vw`. A font's maximum is at most 2.5× its minimum, so zoom still works.
4. Every `:hover` rule sits inside the hover and fine-pointer media query.
5. Use `:focus-visible` with a visible outline (for example `outline: max(2px, 0.08em) solid currentColor; outline-offset: 0.25em`). Never `outline: none`.
6. Everything pressable has an `:active` state.
7. Transitions that move or scale sit inside the reduced-motion query. Never `transition: all`, never `ease-in`.
8. Use `overflow: clip` rather than `overflow: hidden`. An element that a script scrolls or the user resizes still needs `hidden` or `auto`.

When the output is a claude.ai artifact, its page contract decides how themes are defined (tokens on `:root`, redefined for dark mode under its stated selectors). Follow the contract there and keep the other rules.

## Icons

From Gentleface's icon-use rules (gentleface.com, MIT), in our own words:

- Plan every meaning a screen needs before picking any icon.
- One meaning per icon, one icon per meaning, from one library in one style.
- Render at the set's design sizes on whole pixels. Colour icons with `currentColor`.
- Put the accessible label on the control, not on the icon.
- Animate an icon only when something happens.
- When no icon fits, use a word instead of drawing a substitute.

## Worst-case content

Test every mock and build with realistic hard content, not friendly samples:

- **Text:** long names with diacritics, unbreakable emails and URLs, translations about 30 percent longer.
- **Counts:** 0, 1 and 1,284 items.
- **Viewing conditions:** 320 px wide, 200 percent zoom, dark mode, and right-to-left when the content may use it.
- **Truncation:** truncate file names and emails in the middle, and never truncate numbers.

Use plausible or schema-backed data, never random strings.

## Truth

Demonstration content at full fidelity is fine when it is labelled. Never invent prices, customers, testimonials, metrics or capabilities. A bold direction is not weakened by honest placeholder data. Refusing it because the real data isn't there yet is timidity, not honesty.

## Critique of an incumbent

1. Lead with the specificity verdict: is this made for this subject, or interchangeable with a competitor's?
2. List every issue with a severity:
   - P0 blocks the job.
   - P1 is something a user would contact support or complain about.
   - P2 is minor.
   - P3 is polish.
3. Report everything, then rank. Do not pre-filter to "important" issues.
