---
name: copy-longform
description: "Structured copyediting workflow for long-form text (ebooks, reports, whitepapers, long blog posts, decks, internal docs). Produces a tracked edit-list file as the source of truth, scrubs AI-writing tells per Wikipedia: Signs of AI writing, then walks the user page-by-page or chapter-by-chapter through every edit. Claude maintains a progress marker inside the edit-list file so a compacted or new session can resume from exactly where the previous one stopped. Use when the user wants to copyedit existing text rather than draft from scratch, asks for an \"edit pass\" / \"copyedit\" / \"polish pass\" / \"anti-AI scrub\" on a doc, or invokes /copy-longform."
---

# Copy Longform

A workflow skill for working through a defined document with structured feedback. Produces replacement copy, new paragraphs, reframed sections, and fresh prose where needed, always in context of an existing source document, a defined voice ruleset, and locked decisions.

A single edit-list file doubles as the tracker, so progress survives across sessions.

The skill assumes the structure already exists: a document, sections, defined slots where prose belongs, and feedback or direction guiding what changes. It does not start from raw notes or fuzzy ideas where the shape has not been decided.

## When this skill applies

Trigger on any of:
- "/copy-longform" or "/copyedit"
- "Help me edit this [ebook/report/whitepaper/long post]"
- "Run an edit pass on..."
- "Copyedit this for me"
- "Polish pass"
- "Strip the AI tells from..."
- "Anti-AI scrub on..."
- User pastes a long doc and asks for systematic editing
- User points at a file and asks to walk through it

Do NOT trigger when there is no source document or no defined structure to work within. The skill needs a document, sections, or slots where the prose belongs.

## Step 1 — Intake (always ask, never skip)

Even if context appears pre-loaded, ask. The user's own words shape the workflow. Ask in one batch:

1. **What's the source?** (file path, paste, or URL — load it before suggesting changes)
2. **What is it?** (ebook, report, whitepaper, blog post, deck, internal memo) — voice and stakes differ
3. **Audience and stakes.** Who reads it, what does success look like
4. **Voice template.** Is there existing material with the right voice you want to match? (other chapters, prior posts, a brand voice doc)
5. **SME / reviewer comments.** Any feedback from subject-matter experts to fold in?
6. **Anonymization rules.** Any names, clients, products that must be anonymized vs. named?
7. **Locked decisions.** Anything already decided that I should not relitigate (titles, structure, terminology choices)?
8. **Cadence.** Page-by-page (slow, granular), section/chapter (faster, more in your head), or "one big edit list, no walkthrough" (fastest, less interactive)?
9. **Where will edits be applied?** (Google Docs, Word, Markdown file, IDE) — affects how I present diffs

If the user has not done a voice rule conversation before, also ask:
10. **Voice rule preferences.** Default rules from this skill apply (see "Voice rules" below). Anything to add or override?

## Step 2 — Load grounding material

Before producing any edits, load:
- The full source text. For PDFs, use `pypdf` extraction to a staging file. For URLs, use the `defuddle` skill. For Notion/Google Docs, ask the user to export or paste.
- Voice template references (other chapters, prior writing the user wants to match).
- Any decision documents (locked-decisions file, brand voice guide, style guide).
- SME / reviewer comments if provided as a separate file.

Cite the loaded files in the edit-list file's frontmatter so future sessions know what was used.

## Step 3 — Produce the edit-list file

Create a single file: `<source-name>-edits-list.md` in the same folder as the source (or wherever the user wants it). This file is the source of truth.

### Edit-list file template

```markdown
---
title: <Source name> — Edit list
purpose: Page/section-ordered edits for <source>. Source of truth for the copyediting walkthrough.
source_file: <path to source>
voice_template: <paths to voice references>
locked_decisions:
  <key>: <value>
voice_rules:
  - No em-dashes in any new copy
  - No "X, not Y" / "X, rather than Y" / "not just X" antithesis pattern
  - No "actually" as filler
  - No "from X to Y" listing pattern
  - No "Whether you are X or Y" pattern
  - No "in today's [adjective] [noun]"
  - No buzzwords: delve, leverage, navigate, robust, comprehensive, seamless, ensure, fostering, underscores, tapestry, landscape, showcases, highlights, boasts, vital, crucial, pivotal
  - <Plus any user-added rules from intake>
progress_tracking:
  marker_section: "## 📍 Progress marker (auto-updated by Claude during walkthrough)"
  protocol: "Claude maintains the marker after each user response. Move applied items to Applied. Update Currently presenting and Next up. Pending cleanups inside already-applied copy go in their own list so they surface at end."
  resume_instruction: "Read the marker section first on a new or compacted session. Continue from Currently presenting or Next up. Do not re-present items already in Applied unless the user asks to revisit."
last_updated: <date>
---

# <Source name> — Edit list

Working document for the copyediting walkthrough. Edits are <page-ordered | section-ordered | chapter-ordered> so the user can scroll through the source sequentially.

## 📍 Progress marker (auto-updated by Claude during walkthrough)

**Last updated:** <date>
**Cadence:** <page | section | chapter>
**Editor:** User applies in <target editor>

### Applied (verified by user)

- (empty at start)

### Skipped (return at end)

- (empty at start)

### Pending cleanups in already-applied copy

- (empty at start)

### Locked deviations from earlier decisions

- (empty at start)

### Currently presenting

- (set when first page is presented)

### Next up after current

- (queue of upcoming pages/sections)

---

## Voice rules (this pass)

<Detailed bullets, including the Wikipedia AI-tells reference URL: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing >

## Vocabulary swaps (apply throughout)

| Soft / source phrasing | Replacement | Why |
|------------------------|-------------|-----|

## Page-by-page (or section-by-section) edits

### p<N> — <section heading>

**Type:** <reframing | currency | structural | partnership | etc.>
**Old:** <verbatim from source>
**New:** <replacement copy, scrubbed of tells>
**Why:** <one line>

(repeat for each location)

## QA checklist (this pass)

- [ ] No em-dashes in any new copy
- [ ] No "X, not Y" / "X, rather than Y" / "not just X" antithesis pattern
- [ ] No "actually" as filler
- [ ] No "from X to Y" listing pattern
- [ ] No "Whether you are X or Y" pattern
- [ ] (Plus any user-specific checks)

## What this pass does NOT do

- (Boundaries: what is out of scope)
```

## Step 4 — Self-check before presenting

Before showing any replacement copy to the user, scan it for:
- Em-dashes
- Antithesis pattern (`X, not Y` / `rather than` / `not just`)
- "Actually" as filler
- "From X to Y" listing
- "Whether you are X or Y"
- Buzzwords from the rules
- Repetitive parallel structure (triplets stacked on triplets)

Scrub before presenting. If a tell slips through and the user catches it, **fix the source file immediately** (the edit-list file's stored copy), then apologize tersely and re-present. Do not just fix the in-conversation copy and leave the file dirty.

## Step 5 — Walkthrough protocol

For each page (or section, depending on cadence):

1. Present heading: page number + section name
2. List all changes for this page from the edit-list file
3. For each change show:
   - **Type** (reframing / structural / etc.)
   - **Old** (verbatim from source)
   - **New** (paste-ready replacement)
   - **Why** (one line)
4. End with a single prompt: "Reply when applied (or skip / give different version)."

Wait for user response. Then update the marker:
- "applied" → move to Applied list
- "skip" → move to Skipped list with reason
- variation request → produce variation, re-present
- "pause" or end-of-session → leave marker as-is, note time

After every user response, **update the Progress marker section in the edit-list file**. Do not batch; update inline so a compacted session has accurate state.

## Step 6 — Track pending cleanups separately

When you discover an issue in already-applied copy (e.g., a tell that slipped through earlier), do NOT silently re-edit. Surface it to the user, then add to "Pending cleanups in already-applied copy" in the marker. Surface the cleanup queue at the end of the walkthrough so the user can apply them in one batch.

## Step 7 — End-of-walkthrough

When the queue is empty, run the QA checklist with the user. Surface any pending cleanups. If the source has a Table of Contents, deferred pagination, or anything skipped for layout reasons, return to those now.

## Voice rules (default set — Wikipedia: Signs of AI writing)

Reference: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing

The default rules (apply unless the user overrides):

**Punctuation**
- No em-dashes (—) in new copy. Replace with comma, semicolon, colon, period, or restructure.

**Antithesis patterns** (the strongest tell)
- No "X, not Y"
- No "X, rather than Y"
- No "not just X, but Y"
- No "It's not X, it's Y"
- No "instead of Y" inversions when used rhetorically
- Rewrite as positive claims

**Filler and hedge words**
- No "actually" as filler
- No "in today's [adjective] [noun]"
- No "It's important to note that"
- No "stands as a testament to"

**Listing patterns**
- No "from X to Y" enumerations
- No "Whether you are X or Y"
- Watch for forced triplets and stacked parallel structure

**Buzzwords**
delve, leverage, navigate (as metaphor), robust, comprehensive, seamless, seamlessly, ensure (when "make sure" works), fostering, underscores, tapestry, landscape, showcases, highlights, boasts, vital, crucial, pivotal, unlock, elevate, vibrant

**Quoted humans are exempt.** If you are quoting a real person verbatim and their phrase fits an AI-tell pattern, keep the quote and attribute clearly. Do not "fix" attributed quotes.

**Domain technical vocabulary is exempt.** Words like "containerized," "validated," "modular," "reproducibility," "auditability" are domain terms, not buzzwords. The rule of thumb: if a senior practitioner in the field uses the word in a real conversation, it is not a buzzword.

## Workflow improvements to propose at intake

When kicking off a new copyediting job, mention these options up front so the user can opt in:

1. **Voice template extraction.** If the user has 1–3 pieces of writing they like, offer to extract the voice patterns (tone, sentence shape, vocabulary) and include them in the edit-list file as a "Voice template" section. Useful for keeping multiple chapters consistent.

2. **Cleanup ledger.** Maintain a queue of post-application fixes to already-applied copy (e.g., "delete 'actually' on p4"). Surface at end so the user does not have to re-scroll.

3. **Tells audit every N pages.** Every 5 (or user-chosen N) pages, run a quick scan of recently-applied copy and flag anything that slipped through. Catches drift early.

4. **Anonymization registry.** If any names/clients/products need anonymization, keep a registry in the file frontmatter so it stays consistent across the doc.

5. **Locked-decisions file.** If the project has decisions made in earlier sessions or other docs, lock them in the frontmatter so they do not get relitigated.

6. **Companion edit-list.** For long docs that need both structural and voice work, split into two companion files (e.g. `<source>-edits-list.md` for structural/currency/compliance edits and `<source>-<purpose>-pass.md` for the voice reframe). Cross-reference between them and let one own progress tracking.

7. **Output-mode option.** Offer "page-by-page walkthrough" (default), "chapter walkthrough" (faster), or "one big edit list, no walkthrough" (for users who prefer to apply everything in one go).

8. **Diff-only mode for variations.** When producing a re-take of a piece of copy, show only the diff so the user can see what changed without reading the whole paragraph again.

9. **Pre-flight rule confirmation.** Before starting, list the default voice rules and ask: "Anything to add or override?" Lets the user inject project-specific tells (e.g., "no rule of three," "no second-person").

10. **Source-of-truth grounding.** Always read the full source before producing any edits. Do not work from memory or summary.

## Red flags during a walkthrough

- The user catches a tell I missed. Fix the file, not just the chat. Apologize tersely, re-present.
- The user goes quiet for a long stretch. Save state explicitly: ask if they want to pause, and update the marker accordingly.
- The user asks for a "different version" but does not specify what is wrong. Ask what to change before producing the variation.
- The user references an earlier decision I do not see in the file. Ask them to point at it; if it is real, add it to locked_decisions.
- I find myself wanting to do a "while we are here" cleanup beyond the user's intent. Don't. Surgical only.
- The user wants to skip the intake. Push back gently — the questions matter.

## File-naming conventions

- Edit-list file: `<source-name>-edits-list.md` (note the hyphen and plural)
- If a companion file is needed: `<source-name>-<purpose>-pass.md` (e.g., `<name>-engineering-pass.md`)
- Place in the same folder as the source, or in an `assets/` folder if one exists
- Update any project README to link the new file (discoverability)

## Boundaries

- This skill does not produce final-formatted output (PDF, DOCX, etc.). The user applies edits in their target editor; format conversion is a separate step.
- This skill does not skip intake even when context appears pre-loaded.
- This skill does not silently rewrite already-applied copy. Surface the issue, queue the cleanup, and let the user apply in their editor.
- This skill assumes a source document and a defined position for new prose. It does not start from raw notes or fuzzy ideas where the structure has not been decided.
