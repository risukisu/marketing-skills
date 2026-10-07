---
name: internal-linking
description: >-
  Audit a website's internal linking and hand back the fixes. Crawls the site (or imports a
  Screaming Frog export), finds orphan pages, under-linked priority pages, over-linked hubs,
  broken links, redirect chains, generic and repetitive anchors, then proposes concrete links
  (source page, target page, anchor text, draft sentence) and a top-20 action plan in one
  markdown report. Use when the user says "/internal-linking", "internal links", "internal
  linking audit", "orphan pages", "link equity", "anchor text audit", "which pages should link
  to X", "spread authority to this page", or asks why a page gets no internal links. Not for
  backlinks from other sites, and not for planning new content clusters (that is /seo-cluster).
---

# /internal-linking — Internal Linking Audit

Crawl, measure, judge, report. The scripts do the counting; you do the relevance judgment and
the writing. Rules: [references/linking-rules.md](references/linking-rules.md). Output:
[references/report-template.md](references/report-template.md). File formats:
[references/crawl-data.md](references/crawl-data.md).

Requires Python 3.9+ on the PATH (`python` or `python3`), standard library only. Static HTML
only: links rendered by JavaScript are not seen; such sites go through the import path.

## Workflow

Copy this checklist into your response and tick items as you go:

```
Internal linking audit:
- [ ] Step 0: Context intake (scan, list, ask, read only what is approved)
- [ ] Step 1: Intake question (site, priority pages, cluster map, cap)
- [ ] Step 2: Crawl (scripts/crawl_links.py) or import (scripts/import_crawl.py)
- [ ] Step 3: Analyze (scripts/analyze_links.py)
- [ ] Step 4: Judgment pass (sources, anchors, draft sentences, reasons)
- [ ] Step 5: Write the report from references/report-template.md
- [ ] Step 6: Verify against the proposal checklist in references/linking-rules.md
```

**Step 0: Context intake.** The skill has no fixed place for site context and never uses it
without the user's say-so.

1. Scan the launch directory (cwd and its repo) for `CLAUDE.md`, `AGENTS.md`, a `context/`
   folder, files named for brand, ICP, SEO strategy, or site structure, and earlier
   `internal-linking-*.md` reports. List filenames only.
2. Ask one question: use these files / point me at another folder or file / paste the context
   as text / start with none. Wait.
3. Read only what was approved. An earlier report, if approved, is the baseline: note which
   earlier actions were done. "None" means the audit stands on crawl data alone.
4. Optional extra: a machine-local `~/.claude/skills/workspace.local.md` (never shipped) may
   define an output path. List it in the same question; use it only if approved. "None"
   declines it too: the report then goes to the launch folder.

**Step 1: Intake question.** Ask once, then do not ask again. Ask only for what the user's
message has not already given; if it answers everything, confirm the values in one line and
proceed without a question.

> **Which site, and which pages matter most?**
>
> 1. Start URL (the homepage). Not needed when you import an export: the host comes from it.
> 2. Priority pages, most important first: paste a list, or say "pull from analytics" and I'll
>    use the top 20 organic landing pages (needs the GA4 or Search Console MCP connected), or
>    "none".
> 3. Optional: a pillar/cluster map, a Screaming Frog export (`all_inlinks.csv` and
>    `internal_html.csv`) for a JavaScript-rendered site, or a different page cap (default 500).

If the user says "pull from analytics": with the GA4 MCP use `analytics-mcp:run_report`
(in Claude Code: `mcp__analytics-mcp__run_report`) with dimension `landingPagePlusQueryString`,
metric `sessions`, filter `sessionDefaultChannelGroup = Organic Search`, last 90 days, limit 20;
with the Search Console MCP use `gsc:advanced_search_analytics` (in Claude Code:
`mcp__gsc__advanced_search_analytics`) with dimension `page`, last 90 days, sorted by clicks,
top 20. Strip query strings. If neither MCP is connected, say so and ask for the list as text.
Never guess priority pages.

**Step 2: Crawl or import.** Run from the skill folder (`~/.claude/skills/internal-linking`)
or with full paths. Write outputs into the launch folder.

```bash
python scripts/crawl_links.py https://example.com/ --out crawl.json
```

Options: `--max-pages 500` (cap), `--delay 0.5` (seconds between requests), `--include-params`
(keep query strings), `--no-sitemap` (do not seed from the sitemap; orphans then cannot be
found). Exit code 2 means the start URL could not be fetched: report the error and stop.

For a Screaming Frog export or a JavaScript-rendered site:

```bash
python scripts/import_crawl.py all_inlinks.csv --pages internal_html.csv --out crawl.json
```

Read the printed summary and every `warning:` line; they go into the report's limits.

**Step 3: Analyze.** Write the priority pages to `priority.txt` (one per line, most important
first; paths like `/pricing` are fine), then:

```bash
python scripts/analyze_links.py crawl.json --priority priority.txt --out metrics.json
```

Omit `--priority` when none were given. The script prints markdown tables (paste them into
the report sections they are named for) and writes `metrics.json`, whose `needs` list is the
action-plan order and whose `candidates` map is the source shortlist per target. Override
thresholds only when the user asks: `--hub-outlinks`, `--deep-depth`.

**Step 4: Judgment pass.** This is the part only you can do. For every target in `needs`:

1. Read its candidates (`candidates[target]`: source, title, shared terms, PageRank, topical,
   parent). The shortlist is a hint, not a fence: a `parent: true` row is the target's own
   index or category page and is usually the first fix; sources may also come from outside
   the list when a page's title or headings make the topic link obvious. Open the source and
   target pages' titles and headings from `crawl.json`; fetch the source page text only when
   the headings are not enough to place a sentence. On the import path there is no page text:
   place sentences from titles and headings and say so under limits.
2. Pick 2–3 sources that are truly about a related topic (Rule 1). Prefer sources at or above
   the target's authority (Rule 6) and body placement (Rule 5). Reject candidates that would
   exist only for SEO (Rule 2). If none fit, say so for that target rather than forcing one.
   A body link is not a duplicate of an existing nav or footer link to the same target.
3. For each chosen source write: a descriptive anchor of 3–7 words that differs from the other
   anchors to the same target (Rules 3, 4); one draft sentence that would sit naturally in the
   source page with the anchor in it; one short reason (shared topic, fixes orphan, closes a
   priority gap).
4. Keep a running count of new links per source page; stop adding to a source at 5 (Rule 7).
5. For hygiene items decide the fix: update the link to the final URL, restore or redirect a
   404, rewrite a generic anchor, vary a repeated anchor, drop nofollow on an internal link.

**Step 5: Write the report.** Follow `references/report-template.md` exactly. File name
`internal-linking-<host>-<YYYY-MM-DD>.md` in the launch folder (or the approved output path);
in `<host>` replace `:` and any character that is not a letter, digit, dot, or hyphen with
`-`. Write the file with a file-writing tool, not a shell heredoc: the report holds quotes
and fences. Section 6 (action plan) is the first 20 rows of section 4 in `needs` order:
orphans, then priority pages by gap, then near-orphans; on a small site fewer than 20 rows
is right, say so rather than pad. Say what the data source was and every limit.

**Step 6: Verify.** Copy the proposal checklist from `references/linking-rules.md`, tick each
line against the report, fix anything that fails, then hand back the file path and the
three-sentence summary.

## When things go wrong

| Situation | Do this |
|---|---|
| Crawler exits 2 | Report the error (DNS, 4xx/5xx, non-HTML start page); ask for a different start URL |
| `warning: Few links on the start page…` | Site renders links with JavaScript: ask for a Screaming Frog export and use the import path |
| `warning: Page cap … reached` | Say so in the limits; offer a rerun with `--max-pages` raised |
| `blocked_prefixes` not empty | List them under limits; pages there are neither crawled nor proposed as sources |
| No priority pages and no MCP | Omit the priority-gap table; order the plan by orphans then PageRank |
| A target in the priority list was not crawled | It shows as "not crawled" in the gap table; check the URL with the user |
| Site has thousands of pages | Keep the cap; the report says which part of the site it covers |

## Scope

Audits and proposes. Does not edit the site, render JavaScript, audit external backlinks, or
schedule re-crawls. Rerun the skill after changes to measure the difference against the
earlier report.
