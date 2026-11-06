# Report rules

The report is a diagnosis for the person who runs marketing. It tells them how content works as an
inbound channel and where it fails, so they can decide where to invest (create content, SEO,
distribution, paid, conversion work) and brief whoever executes. It is not a content plan and not a
brief.

`build_report.py` renders the page from `metrics.json` (numbers) and `narrative.json` (words). You
write only `narrative.json`. Every section, table and chart is generated; never hand-edit the HTML.

## `narrative.json`

```json
{
 "title": "Content audit of Example Co",
 "verdict": "Three to five sentences. How content works as a lead channel today and where it breaks.",
 "works": ["Specific things that work, each with its number"],
 "doesnt": ["Specific things that do not, each with its number"],
 "channel_read": "Where to invest and where not, per offering, from the primary gaps. One paragraph.",
 "journey_read": "One or two sentences that read the grid for the reader.",
 "offering_notes": {"<offering id>": "Two to four sentences per offering: where its journey breaks and why it matters."},
 "valueprop_read": "What a first-time buyer can and cannot learn; the weakest criterion.",
 "findability_read": "Only with Search Console. Branded vs non-branded, which offerings and stages are found.",
 "traffic_read": "Only with GA4, HubSpot or Ads. Where traffic and first-touch contacts come from.",
 "content_state_read": "Volume, mix, audience fit, freshness, duplicates.",
 "priorities": [
  {"rank": 1, "gap": "content", "offering": "<offering id or 'site'>", "stage": "desire",
   "action": "What to do, concretely", "evidence": "The number that justifies it", "handoff": "/content-strategy"}
 ],
 "limits": ["What this read cannot tell, and why"]
}
```

`gap` is one of `content`, `conversion_path`, `findability`, `conversion`, `distribution`,
`paid_reliance`, `valueprop`. `stage` is an AIDA stage or null. Five to ten priorities, ranked by
expected effect on leads, each tied to a primary gap in `metrics.json`.

## Writing rules

1. **The verdict comes first and answers the question.** "Content brings traffic to tutorials that do
   not sell anything; the two offerings that sell have no Desire pages" is a verdict. "The site has a
   rich content library with opportunities" is not.
2. **Every number comes from `metrics.json`.** The build stops on any number it cannot find there.
   Do not compute new figures in your head; if you need one, add it to the analyzer or leave it out.
   Small counts up to 12 and years are exempt.
3. **Literal language.** Say what the data shows in plain words. No metaphors, no flourish ("a parameter
   worth testing", not "a dial worth turning").
4. **Headings and titles have no final period**, are sentence case, and never use "From X to Y",
   "Beyond the X" or "Not just X, it's Y" formulas.
5. **Separate what was measured from what was judged.** Classification and value-proposition scores
   are judgements (with evidence and confidence); exports and crawl counts are measurements. Say which.
6. **Name what was not assessed.** A verdict that needs a missing export is "not assessed", and the
   priorities say which export would settle it. Never fill the gap with a guess.
7. **Technical and data-quality notes go at the bottom** (`limits`); the top of the report is for the
   reader's decisions.
8. **No client names from CRM data in the narrative.** HubSpot and Ads data stay aggregated. The page
   is marked confidential automatically when either is loaded.
9. **Point each priority at the skill that picks it up** (see `diagnosis-rules.md`): the report
   diagnoses, other skills fix.

## Before building

Run a clean-up pass over the narrative strings: if `/copy-deslop` is installed, run it on them;
otherwise remove inflated words (leverage, robust, seamless, unlock, landscape, holistic, empower,
elevate, delve), hedges and filler. `build_report.py` prints `style:` lines for the most common tells
and for headings that end in a period; fix every one.

## Build and check

```bash
python ~/.claude/skills/content-audit/scripts/build_report.py --run-dir RUN
```

Writes `RUN/<run folder name>.html`, `.md` and `-pages.csv`. If it lists unverified numbers, correct
`narrative.json` and build again; use `--allow-unverified` only when the user asks and say so in the
reply. Then check the page against this list:

- [ ] The verdict answers "how does content work as a lead channel, and where does it fail" in five
      sentences or fewer
- [ ] Every confirmed offering has a primary gap and an offering note
- [ ] Every priority names an offering (or site), a gap, a concrete action, its evidence and a next skill
- [ ] Every "not assessed" check is named in `limits` with the export that would settle it
- [ ] No heading ends in a period; no `style:` warnings remain
- [ ] Crawl warnings and truncated exports appear under "Method and data quality"

## Announce

Reply with three or four sentences (the verdict and the top priority), then the page path on its own
line with the marker, and the markdown and CSV paths:

```
📄 file:///C:/work/content-audit-example.com-2026-01-31/content-audit-example.com-2026-01-31.html
`C:\work\content-audit-example.com-2026-01-31\content-audit-example.com-2026-01-31.html`
```

On a Phase 1 run, end with the ingest folder path and what each export would add.
