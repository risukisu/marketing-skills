# Bans: the named defaults

A vague instruction like "avoid a generic AI look" mostly swaps one default for another. Naming the exact patterns works. This list is a seed. After each render, add whatever the mocks fell back on.

**Scope.** Bans apply where the brief leaves the look free. A brand colour, face or style the person pinned wins over any ban here: the person's clear choice outranks your taste. A ban also gives way when a direction's world truly calls for the pattern, for example a real newspaper referent that uses hairlines, or when the job itself needs the function (three figures read in under a minute). Even then, the card's Avoids field says why it was earned and how it does the job without the template look. Benchmark may keep a category convention that appears here (`directions.md`, role rules).

Sections 1 to 8 are what the fresh agent receives. Paste them as text into its prompt.

## 1. Anthropic's named defaults

Anthropic's prompting guide for Claude Opus 5.5 names five patterns the model falls back on when given no design direction:

- a cream or off-white background
- italic accent words in headlines
- numbered "01 / 02 / 03" section labels
- monospace labels
- pill-shaped buttons

The guide recommends naming these, then checking which styles the first result used instead and extending the list. The same guidance for earlier Opus models names more:

- serif display in Georgia, Fraunces or Playfair
- a terracotta or amber accent
- Inter, Roboto, Arial and system fonts
- Space Grotesk, a face models converge on across generations
- purple gradients on white or dark backgrounds
- timid palettes with every colour spread evenly

Source: platform.claude.com/docs, "Prompting Claude Opus 5.5" (frontend design defaults), plus the Opus 4.8 and general best-practice pages.

## 2. The four saturated looks

Generated interfaces cluster around four looks, whatever the subject:

1. **Warm editorial:** cream paper, a contrasty serif for headlines, and an accent in terracotta or red.
2. **Dark neon:** an almost-black page, a single neon colour, and edges that glow.
3. **Broadsheet:** hairline rules, italic display serif, and small tracked monospace labels.
4. **Flat brutalist:** flat saturated colour, black-outlined boxes, shadows offset without blur, and heavy condensed headlines.

Each is legitimate when the brief asks for it. Where the brief leaves the look free, landing in one means the direction failed. Self-test: if someone could guess the look from the category alone ("a tech product, so dark and neon"), or from the category plus "the opposite of the usual", rework it.

**The warm-subject prior.** Subjects that are warm, bookish, about family, or aimed at children pull models toward cream grounds, serif display with italics, and lamplight, even when no direction asked for them. For those subjects, treat that palette as already used up unless it is pinned.

Source: ideas from Impeccable (pbakaus/impeccable, Apache-2.0), rewritten.

## 3. The rut

Every category has a page it always ships, and a predictable opposite that people reach for to avoid it. Both are the rut. Name them in the fresh run and exclude both. A direction defined by avoiding the default is still defined by the default.

Source: an idea from Impeccable, rewritten.

## 4. Reflex fonts

These faces turn up when nobody chose a face. They are what training data reaches for first:

- **Serif:** Georgia, Playfair Display, Fraunces, Newsreader, Lora, Instrument Serif, DM Serif, Recoleta, Cormorant, Crimson.
- **Sans:** Inter and Roboto as display, Arial, Helvetica, Open Sans, Lato, Montserrat, Space Grotesk, Geist, Mona Sans, DM Sans, Plus Jakarta Sans, Outfit, Instrument Sans, IBM Plex, Syne.
- **Mono, as decoration:** Space Mono, Geist Mono, and JetBrains Mono (the last one added from this skill's own test renders).

Use one only when no other face can do the job. "This subject usually gets this kind of face" is not a reason: a serif for a book club and a mono for a developer tool are the reflex itself. Operate and Read surfaces may use a system stack or a workhorse face (Inter included) for body text and controls, since familiarity serves the task there.

Sources: Anthropic's guidance (section 1), Impeccable and taste-skill font lists, merged and reordered.

## 5. Layout and component bans

- An eyebrow or kicker label above a heading.
- Grids of identical cards, each an icon, a heading and a line of text. Equal cards told apart only by a coloured top border are the same thing.
- Nested cards.
- The hero-metric template: a big number, a small label, and a row of supporting stats.
- The template hero: text left and product picture right with badges under them, or a centred headline sitting on a row of cards.
- A bordered status chip in the masthead ("Live", "New", "v2").
- Gradient text.
- Glass, blur or frosted panels as decoration.
- A thick coloured stripe down one side of a card, list item, callout or alert.
- Hard offset shadows outside a real brutalist world.
- A thin border combined with a wide soft shadow.
- Decorative grid, dot or stripe backgrounds that don't stand for a real canvas, map or plan.
- Emoji or Unicode glyphs used as icons.
- A modal as the first answer to any interaction.
- Sparklines, progress rings or soft rounded rectangles standing in for real content.
- Imitation materials made in CSS (bevels, embossing, stamped metal, chalk).
- A footer with a giant cut-off wordmark over a big closing call to action. In one look at footer.design's first page, 8 of 13 footers used it, so it reads as a default now.
- This skill's own rules: bento grids by default, and the same large radius on every element.
- Across a set: the same chart form, or the same hero arrangement, in every direction.

Sources: Impeccable's anti-pattern rules and taste-skill's layout tells, rewritten. The footer.design observation, the status chip, the coloured top borders and the last two items are this skill's own, the chip and borders from its test renders.

## 6. Motion bans

- A fade-up on scroll for every section or card.
- A hover scale on every card.
- Gradient orbs or blobs.
- Pulsing badges or dots.
- Glowing borders.
- Shimmer that never ends.
- Numbers counting up on load.
- Charts redrawing on mount.
- Bounce, elastic or overshoot easing by reflex.
- `ease-in` on interface motion.
- Entrances from `scale(0)`.
- `transition: all`.
- Animation on anything used a hundred times a day.
- Marquees, and blinking cursors used as decoration.
- Parallax on text, and scroll-jacking.

Sources: Emil Kowalski's skills (MIT) and good-css (MIT) for easing, duration, scale and frequency; Impeccable's detector rules for marquees, cursors and bounce; taste-skill for parallax and scroll-jacking. All rewritten.

## 7. Colour bans

- Purple or violet to blue gradients.
- Cyan on dark.
- Dark mode chosen because the category is "tech".
- Grey secondary text on a coloured ground (derive it from that ground's hue instead).
- Five to seven competing brand colours where one or two would carry the identity.

Sources: Anthropic's guidance (section 1) and Impeccable's colour rules, rewritten.

## 8. Copy bans

Copy is part of the design, and machine-made copy undoes a good layout.

- **Buzzwords:** "seamless", "cutting-edge", "best-in-class", "world-class", "next-generation", "future-proof", "game-changer", "harness the power", "trusted by leading…", "Transform your…", and any verb from "empower / unleash / supercharge / streamline" aimed at "your…".
- **Shapes:** the negation pivot ("not just X, it's Y"), runs of "X. No Y." aphorisms, triads everywhere, paragraphs of identical length, em dashes as the default connector.
- **Invention:** lorem ipsum, invented testimonials, customers, logos, figures, prices or years, and stale years in footers. Demonstration content is fine when it is labelled as demonstration.
- **The house voice:** the same warm, wry, slightly literary tone for every client, a dry one-line closer, and a sign-off in the footer.

Run copy-deslop or the harness's equivalent on the mock copy in step 7, and on every piece of copy in the build.

Sources: Impeccable's style guide and taste-skill's copy tells (Leonxlnx/taste-skill, MIT), rewritten and merged.

## 9. Bans added this run

Keep a section with this heading in each `proposal.md`. List every default the renders fell back on that you had not chosen, and how it was corrected. When the same addition shows up across several runs, add it to this file.
