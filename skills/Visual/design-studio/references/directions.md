# Directions: format, roles, and checks

## The card

Every direction uses the same fields, so the person compares like with like. Tokens are closed: the mock uses these values and no others. A model follows an explicit spec precisely, and drifts back to its defaults wherever the spec is vague.

| Field | What goes in it |
|---|---|
| Name | Two to four words naming the referent. Never "Option A". |
| Role | Refine, Benchmark, On-brand, Bridge, Fresh or Wildcard. |
| Thesis | One sentence on the one idea, and the default arrangement it refuses. |
| Referent | A concrete thing in the world that you could point at or photograph. An adjective ("clean", "bold") is not a referent. |
| Axes changed | Refine and Bridge only: which of the six axes below change, and how. |
| Palette | Four to seven colours in OKLCH, each with a role. Add hex only when a tool computed it, never by estimate. Name the colour strategy. State light or dark, and the scene sentence that decided it. |
| Type | Display and text faces that fit the medium (`media.md`), each with a one-line reason, the scale ratio, and the scripts the content needs. Coverage is checked at render. |
| Shape and surface | Radius values, a single way to show elevation (borders or shadows, not both), and any texture or material. |
| Structure | The sections or screens it proposes, in order, and the navigation labels. |
| Voice | The headline and the main action label. |
| First viewport | What sits where, at what size, and where the main action is. |
| Next screen | What follows the first viewport. |
| Signature | The single move you would still spot with all the content stripped out. |
| Motion | The stance, the one authored moment, and its duration and easing. |
| Imagery and icons | What kind, from where, and in what treatment. |
| Keeps and replaces | Required for Bridge. For Refine, everything outside the changed axes is kept. |
| Avoids | The bans it is most at risk of, and how it stays clear of them. |
| Risk | The honest cost or failure mode. |
| Right choice when | One sentence. |
| Build effort | S, M or L, and what it touches (tokens only, templates, content model). |

When you brief an agent, show it this format, not a filled-in card. Agents copy a filled example's choices along with its structure.

**Card against craft floor.** The card decides style: palette, faces, radius, the motion moment. `craft-floor.md` decides the accessibility and usability numbers: contrast, sizes, targets, reduced motion. When a card value breaks a floor number, the floor wins, and `proposal.md` lists the deviation.

## Role rules

**Refine.** It starts from the identity lock. It keeps the identity and changes one or two of these six axes:

1. Hierarchy: what leads, what follows, relative scale.
2. Layout topology: stacked, split, grid, asymmetric, overlay.
3. Type system: within or close to the current faces, with scale, weights and measure.
4. Colour strategy: within the current tokens, moving between restrained, committed, full and drenched.
5. Density: minimal, comfortable or dense.
6. Structure: merge, split, or progressive disclosure.

It fixes every P0 and P1 issue from the critique. Two Refine variants on the same axis would be one direction.

**Benchmark** (when nothing exists). The category's conventions, done straight, at the level of two or three named real products. Name them for their level of execution, not as looks to copy. It is honest about being familiar. When the category's standard is itself on the ban list (an impact report's big figures, for example), Benchmark may keep that convention and says so on its card. The other bans still apply to it.

**On-brand** (brand guidelines exist, no artifact does). The guidelines applied straight, at the craft level of the Benchmark products. Bridge then sits between On-brand and Fresh.

**Fresh.** It comes from the isolated agent and the neutral brief (`fresh-brief.md`). It shares nothing with the incumbent that the brief did not force.

**Bridge.** It is written after Fresh and Refine exist. It has a keep list (the assets with equity) and a replace list (ideas taken from Fresh). It replaces at least two of: palette strategy, type system, layout topology, surface treatment. It keeps at least two traits a returning visitor would recognise. Polish on the old look is a second Refine, and Fresh with the old logo is a second Fresh. Both fail.

**Wildcard.** The fresh agent's best candidate from a material family other than Fresh's. Show it only if it passes the distinctness and leak checks. When it fails, replace it with the next-ranked candidate from another family, through the isolated agent, or drop it.

**When nothing exists.** There is no identity lock and no critique. Bridge keeps at least two conventions from Benchmark or On-brand that carry trust for this audience, in place of recognisable traits.

## Modes

Choose the mode from the surface being designed, not from the product. A developer tool's landing page is Persuade, and a fashion brand's help centre is Read. The mode limits how far a direction's world may reach. When the job pulls one way and the surface another (a portfolio whose job is to get hired), choose the mode the main action needs, and note the choice in the brief.

| Mode | The visitor | How far the world reaches |
|---|---|---|
| Persuade | decides and acts: landing pages, campaigns, pricing | Full commitment. The opening makes the offer clear and desirable and shows the real action in working form. |
| Operate | completes a task: app UI, dashboards, admin, tools | The world lends its faces, colours, density and a single signature move. Navigation, controls and layout follow conventions people already know. Novelty that slows a task down is the failure here. |
| Read | understands something: reports, docs, articles, guides | The world owns the frame (masthead, rail, openers, table and chart setting). The reading column stays calm. |
| Experience | is inside the work: portfolios, galleries, showcases | The work leads from the first viewport, and the interface recedes. |

## Colour strategies

- **Restrained**: tinted neutrals plus one accent used sparingly. The default floor for Operate.
- **Committed**: one saturated colour carries 30 to 60 percent of the surface.
- **Full palette**: three or four named colour roles, each owning regions.
- **Drenched**: the surface is the colour.

Let a colour decision show across the whole page: a colour that holds a region says more than small accents dotted over grey. Light or dark is never chosen by category ("tech means dark"). The scene sentence decides it.

## Checks

**Distinctness.** First the family pass: label each direction with a concrete family. Two that share a label are one direction. Then the sentence pass: read the thesis sentences side by side. Two that rhyme are one direction. Directions that differ only in accent colour or copy are one direction. At thumbnail size (25 percent), each mock should be identifiable without its name.

**Memory test.** What would someone describe an hour after seeing only the first viewport? A specific image or arrangement passes. A mood does not.

**Specificity.** Swap the subject's name for a competitor's. If nothing in the direction becomes wrong, it is generic.

## Scoring

Score from the rendered mocks, not the cards. Score each direction against the brief's success criteria, 1 to 3 per criterion, with a one-line reason. Then add:

- Specificity: 1 to 3, from the check above.
- Build cost: S, M or L.
- Risk: one line.

Show the scores in `proposal.md`. In chat, give the four-column table from SKILL.md step 8, then a one-sentence recommendation tied to the scores, marked as yours.
