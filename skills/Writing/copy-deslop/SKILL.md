---
name: copy-deslop
description: Clean up AI-sounding copy. Use when text feels generic, robotic, or obviously LLM-generated. Catches overused words, hollow phrases, false enthusiasm, and structural patterns that signal AI writing. Fetches the latest tells from Wikipedia entry on "Signs of AI writing" before each analysis. Works on any text — marketing copy, blog posts, emails, docs.
---

# Copy De-Slop

Detect and fix AI-sounding writing. This skill exists because LLM-generated text has recognizable patterns — and readers have learned to spot them. If your copy triggers even one "this was written by AI" alarm, trust drops instantly.

**How to use:** Paste text, or point to a file. The skill analyzes it, flags problems, and rewrites the flagged sections.

## What to Flag

### Tier 1: Dead Giveaway Words

These words appear in AI writing at 10-100x their normal human frequency. Replace or remove every instance:

| Word/Phrase | Why it's a flag | Fix |
|-------------|----------------|-----|
| delve, delves, delving | Extremely rare in human writing, ubiquitous in LLM output | explore, dig into, look at, examine — or just cut it |
| utilize | People say "use" | use |
| leverage (as verb) | Corporate AI-speak | use, take advantage of, build on |
| tapestry | AI loves weaving tapestries | cut entirely, replace with specific description |
| landscape (metaphorical) | "the marketing landscape" — meaningless | the market, the industry, what's happening in X |
| realm | "in the realm of" | in |
| multifaceted | AI's favorite adjective | complex, varied, or just describe the specific facets |
| comprehensive | Usually means nothing specific | thorough, complete, full, or describe what's actually covered |
| crucial, pivotal | AI over-emphasizes importance | important, key, or let the content speak for itself |
| foster | "foster innovation/collaboration/growth" | build, encourage, create, support |
| streamline | Vague efficiency buzzword | simplify, speed up, cut steps from — be specific |
| robust | Everything is "robust" in AI copy | strong, reliable, tested, or describe the actual quality |
| seamless, seamlessly | Nothing is seamless. Ever. | smooth, easy, simple — or just describe the experience |
| navigate (metaphorical) | "navigate the challenges" | deal with, handle, work through |
| empower | Performative corporate altruism | help, enable, let, give you |
| harness | "harness the power of" | use |
| spearhead | Nobody says this in real life | lead, start, drive |
| underscore | "this underscores the importance" | shows, proves, highlights |
| in today's [X] | "In today's fast-paced world" — filler | cut entirely |
| it's worth noting that | Stalling before making a point | just make the point |
| game-changer | Hyperbole that means nothing | describe the actual change |
| nestled | "nestled in the heart of" — travel brochure AI | located in, based in |
| vibrant | AI's default adjective for anything positive | specific — busy, colorful, energetic, what is it? |
| tapestry | "a rich tapestry of" — meaningless poetry | cut, describe the actual elements |
| interplay | "the interplay between X and Y" | relationship, connection, how X affects Y |
| meticulous/meticulously | AI's favorite adverb of quality | careful, detailed, thorough — or just show the quality |
| garner | "garnered attention" — nobody talks like this | got, earned, attracted |
| enduring | "enduring legacy/impact" — AI loves permanence | lasting, long-running, or question if it's really enduring |
| bolstered | corporate AI filler | strengthened, supported, helped |
| stands as / serves as | AI avoids "is" | just say "is" |

### Tier 2: Structural Patterns

These aren't individual words but writing patterns that signal AI:

**The Three-Part List Habit**
AI loves tripling: "efficiency, innovation, and growth" / "clear, concise, and compelling." Humans naturally vary list length. If every sentence has exactly three items, it's a tell.
→ **Fix:** Vary structure. Sometimes two things. Sometimes four. Sometimes one.

**The Topic-Sentence-Then-Elaborate Pattern**
Every paragraph starts with a clear topic sentence, then elaborates. Real writing meanders, starts with examples, buries the point, or leads with a question.
→ **Fix:** Start some paragraphs with a detail, a question, or a contradiction.

**The Balanced Paragraph**
AI paragraphs are suspiciously uniform in length — 3-5 sentences each, all roughly the same size. Human writing has short punchy paragraphs and longer flowing ones.
→ **Fix:** Let paragraphs be different sizes. One-sentence paragraphs are fine.

**False Enthusiasm**
"This is a great question!" / "Absolutely!" / "That's an excellent point!" — AI's reflex to validate before answering. Humans don't do this in written text.
→ **Fix:** Cut all performative agreement. Just answer.

**The Disclaimer Sandwich**
Opening with a caveat, making a point, then hedging again. "While there are many approaches, X is generally considered... though of course it depends on context."
→ **Fix:** Make the point. Add caveats only when they change the reader's decision.

**Excessive Transitions**
"Furthermore," "Moreover," "Additionally," "In conclusion," — AI uses formal transitions between every point. Real writing lets points flow or uses casual connectors.
→ **Fix:** Cut most transitions. "And" / "But" / "So" / "Also" or just start a new paragraph.

**The Definition Opening**
Starting with "X is a Y that Z" — AI defines before it discusses. Humans assume shared context.
→ **Fix:** Skip the definition unless the reader genuinely might not know the term.

**"Not Just X, But Also Y"**
"It's not just a tool, it's a platform." / "Not only does it X, but it also Y." AI loves this parallelism. One or two is fine. Five in one piece is a dead giveaway.
→ **Fix:** Just say the positive thing. "It's a platform." Done.

**Elegant Variation**
Referring to the same thing by different names to avoid repetition: "the company," "the firm," "the organization," "the enterprise." AI does this compulsively. Humans just say the name again.
→ **Fix:** Repeat the name. It's fine. Clarity beats variety.

**Em Dash Overuse**
AI inserts em dashes — like this — mechanically throughout text. One or two per piece is natural. Seven is a pattern.
→ **Fix:** Replace most with commas, periods, or parentheses. Reserve em dashes for genuine asides.

### Tier 3: Tone Markers

**Confident hedging:** "It's important to remember that..." — adds nothing.
**Empty amplifiers:** "Very," "really," "extremely," "incredibly" — weaken rather than strengthen.
**Passive formality:** "It should be noted" / "It can be observed" — just say who did what.
**Question-then-answer:** "What makes this approach effective? The answer lies in..." — a rhetorical tic AI can't quit.

## Process

When analyzing text:

0. **Live Wikipedia check** — fetch the current AI-writing tells reference. Use whichever method works in your environment:

   **Claude Code (CLI):** use defuddle for clean markdown output:
   ```
   defuddle parse https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing --md
   ```

   **Claude Windows App / web / any environment:** use the Wikipedia REST API directly — it's designed for programmatic access and won't block:
   ```
   https://en.wikipedia.org/api/rest_v1/page/summary/Wikipedia:Signs_of_AI_writing
   ```
   For full content: `https://en.wikipedia.org/api/rest_v1/page/html/Wikipedia:Signs_of_AI_writing`

   Scan the output for any words or patterns not already in the Tier 1, 2, or 3 lists above. If new tells are found, surface them to the user before proceeding: "The Wikipedia page lists X and Y that aren't in this skill's defaults — flagging those too."

   If both fetch attempts fail, proceed with the hardcoded rules and note: "Live Wikipedia check unavailable — using built-in rules only."

1. **Read the full text first** — understand what it's trying to say
2. **Flag Tier 1 words** — highlight each with a replacement
3. **Flag Tier 2 patterns** — identify structural issues with specific line references
4. **Flag Tier 3 tone markers** — note any that weaken the text
5. **Present findings** as a numbered list with original → suggested fix
6. **Offer to rewrite** the flagged sections while preserving the author's intent and voice

## What NOT to Change

- **Domain-specific terminology** — "leverage" in finance actually means leverage. "Robust" in engineering has a real meaning. Only flag when used as generic filler.
- **The author's genuine voice** — if someone naturally writes long sentences or uses particular phrases, that's style, not slop.
- **Intentional formality** — legal docs, academic papers, and official comms have their own register. Don't casualize everything.
- **Correct use of flagged words** — "delve" is a real word. It's fine if used once in an article about archaeology. It's a flag when every AI paragraph "delves deeper."

## Severity Scale

When reporting, categorize each flag:

- 🔴 **Cut immediately** — dead giveaway words, filler phrases
- 🟡 **Rephrase** — structural patterns, hedging, could be improved
- 🟢 **Minor** — tone markers, could go either way

Focus effort on 🔴 items. A text with zero 🔴 flags already reads as human even if it has some 🟡.
