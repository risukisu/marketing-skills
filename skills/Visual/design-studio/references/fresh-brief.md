# The neutral brief and the fresh agent

Fresh is the direction that keeps the proposal honest. If it inherits the incumbent's palette, faces, layout or tone, the person is choosing between three versions of what they already have. In a no-skill test, an agent asked for a "zero-bias" direction after reading a site and its notes produced a red one hue step away from the site's accent, a serif-led voice that mirrored the site's text face, the same page set, and the humour of the site's existing copy. In later tests with the skill, the leaks that got through came from three places: a content list copied from notes, words and navigation written into the mock after the incumbent had been read, and git history read during the context scan. The order below closes each of them.

## Rules for writing the brief

Write it from the intake answers only, before opening any file, URL, screenshot or commit history of the incumbent.

1. **Facts, not looks.** Describe what the thing is, who uses it, where and when they use it, what they must do, and what content it carries. Leave out every colour, typeface, shape, texture, mood or style word, including ones the person used about the current design ("clean", "warm", "techy"). The person's dislikes are look words too, so they stay out; they are checked on every card in step 6.
2. **No pointers to the incumbent.** No URLs, domains, paths, project names or product names that would let a model recall the existing look. Describe the thing as "`<who>`'s `<what>`", naming the owner's role and the thing's purpose. The one exception is the name the design must display (the business or the person), which goes in as a factual line, because a mock without it can't be judged. When that name is well known enough for a model to recall its look, write a stand-in of similar length and script, and swap the real name in when you save the mock.
3. **Content as material, not structure.** List what the design must carry and how much of it (for example eight case studies, two essays, one CV), the languages and scripts, and a few factual lines: a name, an offer, a figure with its unit, the main action by name. Don't list the current pages, sections, navigation or their order. Structure is part of the incumbent, and Fresh proposes its own. Don't quote existing marketing copy; its voice is part of the incumbent too.
4. **Jobs, not pages.** For a multi-page surface, name the jobs it must do, each with its visitor and one action. Never name the current page list.
5. **Hard constraints only.** Accessibility level, stack or medium, required languages, legal requirements, and assets that must appear, stated by function ("a logo mark exists and must appear"), never by look. When the person gave no accessibility level, write WCAG 2.2 AA and mark it as assumed.
6. **Pins stay out by default.** A brand colour or face the person wants kept binds Refine and Bridge, not Fresh. Include a pin only when the person said it applies to every direction.
7. **The physical scene.** One sentence about who uses this, where, on what device, and under what light, from the intake answer to that question. That sentence later decides light or dark.
8. **Success criteria are checkable.** Three to five, in the shape "`<who>` can `<do what>` within `<limit>`". Leave out "looks made for this subject": specificity is scored separately.

Read the finished brief once against rules 1 to 4. Any word that describes a look, and any line that describes the current structure, gets cut. Anything you had to assume goes in with the word "assumed".

## Template

```xml
<brief>
  <surface>What is being designed, its medium, and where it ships.</surface>
  <mode>Persuade | Operate | Read | Experience (see directions.md)</mode>
  <audience>Who looks at it, and what they already know.</audience>
  <scene>One sentence: who, where, which device, what light.</scene>
  <jobs>
    For each job: the visitor, what they must understand, and the one action they take.
  </jobs>
  <success_criteria>
    1. <who> can <do what> within <limit>.
    2. ...
    (three to five)
  </success_criteria>
  <content>
    Material and counts: what must be carried, how much of it, languages and scripts.
    Factual lines the design must carry: names, offers, figures with units, the main action by name.
  </content>
  <constraints>Accessibility, stack or medium, legal requirements, required assets by function.</constraints>
</brief>
```

## Component variant

When the request is a component or section inside an established design, the identity is fixed for every direction, Fresh included. Add this block to the brief, filled with the incumbent's real tokens:

```xml
<fixed_identity>
  Colours (OKLCH, with roles), faces and weights, radius, elevation, spacing unit.
  These are fixed. Every direction uses them.
</fixed_identity>
```

In the rank prompt, replace "seven candidate worlds" with "seven candidate structures and interaction models", drawn from the same sources (objects, instruments, printed matter, screen traditions). On the cards, the Palette and Type fields read "uses the fixed identity", and the agent fills in structure, density, states and interaction instead. In the build prompt, ask for the section's HTML and CSS only. You place it, unchanged, into a copy of the real page, so the mock shows it in context.

## The rank prompt (turn 1)

Fill `{BRIEF}` and `{BANS}` (sections 1 to 8 of `bans.md`, pasted as text), then send it as the whole prompt. Attach no files and no paths.

```xml
You are a design director starting a new visual direction from a written brief. You have not seen the current version of this thing, and that is deliberate: this direction is the one in the proposal that inherits nothing, so the person can compare their current design against a genuinely independent alternative.

Work from the brief below and nothing else. Use no tools: do not search, fetch, list or open files.

Begin your reply with one line, "CONTEXT SEEN:", naming (names only, no contents) any person, brand, workspace, project or memory notes present in your instructions, or "none". Then work from the brief alone.

<brief>
{BRIEF}
</brief>

<bans>
{BANS}
</bans>

<method>
1. Name the rut: the default version of this category, and the obvious contrarian take on it. Exclude both, because a direction chosen by avoiding the default is still defined by it.
2. List seven candidate worlds drawn from the audience's own culture: objects, places, rituals, printed matter, signage, notation, instruments, or screen traditions they know well. Give each one line on why it fits this audience and one line on how it would look (ground and main colours, type voice, one signature). The seven span at least three material families, meaning the kind of physical material or medium a world is made of. At most one comes from the tools the audience uses at work, since a work tool's look worn as a theme reads as costume. For each, ask what this thing would be as an object you could hold, and how its world worked before it had a screen. Every candidate must be one you would defend shipping; replace any that is there only as contrast. Order the list by how strongly each fits.
</method>

<output>
Return exactly these parts, in plain markdown:

CONTEXT SEEN: the line described above.

RUT: one sentence naming the category default and its predictable opposite.

CANDIDATES: the seven, numbered in ranked order, one line each: name, material family, why it fits, how it looks.

Then stop. A number will follow in the next message.
</output>
```

## The build prompt (turn 2)

Send this to the same agent after rolling. When the harness can't continue an agent, start a new one of the same type with the whole rank prompt (role, isolation lines, the `CONTEXT SEEN:` request, `<brief>` and `<bans>`), minus its `<method>` and `<output>` blocks, plus a `<candidates>` block holding the returned list, followed by this text.

```xml
The roll is {ROLL}.

Build candidate {ROLL} as the direction called Fresh, whatever its rank. A roll is used because the top-ranked candidate is the most predictable one. Then build the strongest candidate from a material family different from Fresh's as the direction called Wildcard. If that is your top-ranked candidate, say in its Risk line that it is the most familiar one.

<craft>
The mocks must meet these, whatever the direction:
- Body text at least 16px on screens; measure 60 to 75 characters; body leading 1.5 to 1.7.
- Contrast at least 4.5:1 for body text, 3:1 for large text, controls and focus rings.
- Colours in oklch(); logical properties (margin-block, padding-inline); overflow: clip, not hidden.
- Hover rules inside @media (hover: hover) and (pointer: fine). A visible :focus-visible outline, never outline: none. An :active state on everything pressable.
- Movement and scale inside @media (prefers-reduced-motion: no-preference); opacity and colour feedback may sit outside it. Never transition: all or ease-in. Ease-out is cubic-bezier(0.23, 1, 0.32, 1).
- Touch targets at least 44px; text at least 16px from the edge on a 390px screen; no horizontal scroll at 390px.
- tabular-nums wherever numbers sit in columns.
- Fonts from Google Fonts, loading only the weights used, with the subsets the content's scripts need.
- Content from the brief only. Every word on the page, every label and every navigation item comes from the brief or is written by you for this direction. Anything the brief lacks is labelled as demonstration. Never invent prices, customers, testimonials, years or figures.
</craft>

<output>
First, two direction cards, Fresh and Wildcard, each with these fields:
- Name: two to four words naming the referent (never "Option A").
- Thesis: one sentence on the one idea, and the default arrangement it refuses.
- Referent: the concrete real-world thing it draws on.
- Palette: four to seven colours as OKLCH, each with its role (canvas, raised surface, primary text, secondary text, accent or action, border, any status colours). Name the colour strategy: restrained, committed, full palette, or drenched. State light or dark, and the line of the scene that decided it.
- Type: faces that fit the medium in <surface>: web faces from Google Fonts or a free foundry for screens, embeddable faces for documents, a system stack for email. A system or workhorse face is allowed for Operate and Read body text. A monospace face only if the content has code or tabular data. Each with a one-line reason, the scale ratio, and the scripts the content needs.
- Shape and surface: radius values, borders or shadows (one way to show elevation), and any texture or material.
- Structure: the sections or screens this direction proposes, in order, and the navigation labels.
- Voice: the headline and the main action label, written from the brief's factual lines.
- First viewport: exactly what sits where, at what size, and where the main action is.
- Next screen: what follows the first viewport.
- Signature: the single move you would still spot with all the content stripped out.
- Motion: the stance, the one authored moment, and its duration and easing.
- Imagery and icons: what kind, from where, and in what treatment.
- Avoids: which bans this direction is most at risk of, and how it stays clear of them.
- Risk: the honest cost or failure mode.
- Right choice when: one sentence.

For each choice, give a one-line rationale. Do not include your working beyond that.

Then the two mocks, each as one complete HTML file with inline CSS in its own fenced code block, labelled fresh.html and wildcard.html. Each shows the first viewport and the next screen, using exactly the card's tokens.
</output>
```

## After it returns

- Save `fresh.html` and `wildcard.html` exactly as returned. Your own edits stay mechanical (overflow, contrast arithmetic, broken markup). Anything else goes back to the same agent, or to a new isolated one with the brief and the candidate list.
- Run the leak check in SKILL.md step 6 on both cards and both mocks.
- Keep the `CONTEXT SEEN:` line, the rut and the seven candidates in `proposal.md`. When the person asks for another fresh option, send the agent the next candidate from a different material family.
