---
name: frontend-design-anti-slop
description: Design distinctive frontend interfaces that don't look AI-generated. Use when building web pages, landing pages, dashboards, or any UI — especially when you want to avoid the generic "AI slop" aesthetic that plagues LLM-generated designs.
metadata:
  built: 2026-09-05
  author: risu (https://github.com/risukisu/)
  built-with: Claude Fable 5.1
  also-listed: https://skillcraft.cloud/marketplace
---

# Frontend Design — Anti-Slop Edition

Build frontend interfaces with genuine design taste. This skill exists because most AI-generated UIs look identical: purple-to-blue gradients, bento grids, rounded-xl everything, "Transform your X" hero text. This skill does the opposite.

**This is an interactive process.** Ask the user what they're building before designing anything.

## Intake

Start by asking:

> What are you building? (Landing page, dashboard, app UI, marketing page, etc.)
> Who is it for? What's the vibe — professional, playful, warm, minimal, bold?
> Any existing brand elements (colors, fonts, logo) I should work with?

Wait for answers before proceeding.

## Design Principles

Apply these in every decision:

1. **Warm over corporate.** Dark backgrounds should feel like a room at night, not a SaaS dashboard. Use brown-blacks (#12110f) over pure blacks (#000). Warm grays over cool grays.

2. **Monospace for character, display for hierarchy.** Use monospace fonts (JetBrains Mono, IBM Plex Mono, Fira Code) for UI chrome — labels, badges, buttons, metadata. Use a display or heading font (Space Grotesk, Inter Tight, Satoshi) for titles and emphasis. Never use monospace for everything. Never use a generic sans-serif for everything either.

3. **One accent color, used sparingly.** Pick one strong accent (mint green, amber, coral) and use it only for primary actions and active states. Everything else lives in the neutral palette. Two accent colors maximum. If you reach for a third, you've lost the thread.

4. **Borders > shadows.** Subtle 1px borders (#33302a on dark, #e5e5e5 on light) create structure without the floaty feeling of box-shadows. Reserve shadows for elevated elements (modals, dropdowns, toasts).

5. **Content density over whitespace theater.** Let content breathe with natural spacing (4/8/12/16px increments), not massive gaps that make users scroll past nothing. Information-rich is not the same as cluttered.

6. **Rounded-lg maximum.** No rounded-xl, no rounded-2xl, no pill shapes on cards. Subtle rounding (8px) feels intentional. Excessive rounding feels like a template.

## Anti-Patterns — Never Do These

These are the hallmarks of AI-generated design slop. Avoid every single one:

| Pattern | Why it's bad | What to do instead |
|---------|-------------|-------------------|
| Purple-to-blue gradients | Every AI UI has them. Instant "this was generated" signal. | Solid colors. If you need a gradient, use warm tones or monochrome. |
| `rounded-xl` or `rounded-2xl` on cards | Looks like every Tailwind template. | `rounded-lg` (8px) maximum. `rounded` (4px) for small elements. |
| Centered hero with gradient text saying "Transform your X" | The #1 AI slop pattern. | Start with the product, not a tagline. Show, don't tell. |
| Bento grids with rounded corners on everything | Looks like Apple keynote cosplay without the product to back it up. | Standard grid layouts. Asymmetry is fine. Not everything needs equal weight. |
| Excessive whitespace | Mistaken for "clean design." Actually just empty. | Content-first. Space serves the content, not the other way around. |
| `animate-pulse` skeleton loaders | Draws attention to loading, makes the page feel broken. | Subtle opacity fade or no animation. Skeleton should be invisible, not a feature. |
| Emojis as icons | Looks like a Discord bot. | Use an icon library (Lucide, Heroicons, Phosphor). Consistent weight and style. |
| `system-ui`, Inter, Roboto, Arial everywhere | Default fonts signal "I didn't make a design decision." | Choose fonts with intention. Even Google Fonts has distinctive options. |
| Colored top-bar stripes on cards | Early Trello/Asana pattern, now a cliché. | Border colors, subtle background tints, or icon-based categorization. |
| Floating/bobbing hover animations | Distracting, gimmicky, adds no information. | Subtle border/shadow transitions (200-300ms). Hover should clarify, not entertain. |

## Color Palette Guidance

When the user doesn't have existing brand colors:

**Dark themes:**
```
Background:  #12110f (warm dark brown, not pure black)
Surface:     #1e1c18 (cards, panels)
Border:      #33302a (subtle divider)
Text:        #e8e4dc (off-white, not pure white)
Muted:       #8a8578 (secondary text)
Accent:      Pick ONE from: #4ade80 (mint), #f59e0b (amber), #f87171 (coral), #60a5fa (sky)
```

**Light themes:**
```
Background:  #faf9f7 (warm off-white)
Surface:     #ffffff
Border:      #e8e4dc
Text:        #1e1c18
Muted:       #8a8578
Accent:      Same options, slightly deeper for contrast
```

## Component Patterns

**Cards:** `rounded-lg`, 1px border, `bg-surface`, hover changes border color or adds subtle glow. No drop shadows. No float animation.

**Buttons:** Outlined style for secondary (border + text color). Filled style for primary (accent bg + dark text). No gradient fills. No rounded-full unless it's an icon button.

**Forms:** `bg-surface`, `border-border`, `focus:border-accent`. No ring utilities. Clean, no decoration.

**Typography scale:** Don't use more than 4 font sizes on a page. Heading (xl-2xl), subheading (lg), body (sm-base), caption (xs). Enforce hierarchy through weight and font family, not just size.

## Process

1. Confirm the build target and vibe with the user
2. Choose a color palette (or use their existing one)
3. Choose fonts (heading + body/mono, Google Fonts is fine)
4. Build the layout structure first (HTML skeleton with Tailwind)
5. Apply the design system: colors, typography, spacing
6. Review against the anti-patterns list — fix any violations
7. Show the user and iterate

## When Reviewing Existing UI

If the user asks you to review or improve an existing page:

1. Check it against the anti-patterns list first
2. Identify the top 3 offenders
3. Propose specific fixes with before/after reasoning
4. Don't redesign everything — targeted improvements beat rewrites
