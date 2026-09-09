---
name: seo-report
description: >-
  Generate a comprehensive SEO health report for any website using live GA4 data (via analytics-mcp) and optionally
  Google Search Console data (via gsc MCP). Evaluates the site against Google's official SEO best practices including
  E-E-A-T, helpful content guidelines, technical SEO, Core Web Vitals, and on-page optimization. Produces a structured
  report with traffic analysis, content quality signals, and prioritized recommendations.
  Use this skill whenever the user asks for an SEO audit, SEO report, organic traffic analysis, search performance
  review, content quality assessment, or wants to understand how their site performs in Google Search. Also trigger
  when the user mentions "SEO check", "search rankings", "organic performance", "Google traffic", or asks questions
  like "how is my site doing in search" or "what should I fix for SEO". Works for any website connected to GA4.
---

# /seo-report — SEO Health Report

Generate a data-driven SEO health report by pulling live analytics data and evaluating the site against Google's official search quality guidelines.

## Before You Start

This skill requires at minimum the **GA4 MCP** (`analytics-mcp`). The **GSC MCP** (`gsc`) adds search query data and indexing insights but is optional — the report adapts to whatever data sources are available.

Check which MCP servers are connected:
- `mcp__analytics-mcp__*` tools → GA4 is available
- `mcp__gsc__*` tools → GSC is available (if not, skip GSC sections and note it)

Read `references/ga4-seo-queries.md` for the exact query patterns to use. Read `references/google-seo-checklist.md` for the evaluation framework.

## Step 0: Company context (every run, ask before reading)

The skill has no fixed place for site or company context and never uses it without the
user's say-so.

1. Scan the launch directory (cwd and its repo) for likely context: `CLAUDE.md`, `AGENTS.md`, a
   `context/` folder, files named for brand, ICP, or SEO strategy, and earlier `seo-report-*.md`
   files this skill produced. List filenames only; don't read contents yet.
2. Ask one question: use these files / point me at another folder or file / paste the context as
   text / start with none. Wait.
3. Read only what was approved. An earlier report, if approved, is the baseline to compare
   against. "None" means the report stands on GA4/GSC data alone.
4. Optional extra: a machine-local `~/.claude/skills/workspace.local.md` (never shipped) may define
   output paths and a portfolio of sites for the current root. List it in the same question; use
   it only if approved.

## Step 1: Intake

Ask the user one question:

> **Which website do you want the SEO report for?**
>
> I'll pull your GA4 data and evaluate against Google's SEO best practices. If you have multiple GA4 properties, tell me which one — or I'll list what's available.
>
> Optional: Any specific concerns? (e.g., traffic dropped, launching new content, preparing for a redesign)

If the user provides a property ID, use it directly. Otherwise, run `mcp__analytics-mcp__get_account_summaries` to list available properties and let them pick.

Once you have the property ID, run `mcp__analytics-mcp__get_property_details` to get the site URL and property name for the report header.

## Step 2: Data Collection

Pull data in parallel where possible. Read `references/ga4-seo-queries.md` for the exact query structures — use the queries as documented there, adapting the property_id.

### Required GA4 queries (run all of these):

1. **Organic traffic overview** — total organic sessions, users, engagement rate (90 days)
2. **Organic traffic trend** — weekly sessions for trend line (90 days)
3. **Organic traffic sources** — Google vs Bing vs others
4. **Top landing pages** — top 30 organic landing pages with engagement metrics
5. **Device breakdown** — mobile vs desktop organic performance
6. **New vs returning** — organic user loyalty
7. **Period comparison** — month-over-month organic change
8. **Content engagement** — top 50 pages by views with engagement metrics
9. **Event signals** — event types and counts (to assess tracking maturity)

### If GSC MCP is available, also pull:

Read `references/gsc-seo-queries.md` for the full GSC tool reference. Run in this sequence:

**Phase 1 — Overview:**
10. `mcp__gsc__site_snapshot` — baseline performance and trends

**Phase 2 — Opportunities (run in parallel):**
11. `mcp__gsc__quick_wins` — keywords at positions 4-15 with high impressions (low-hanging fruit)
12. `mcp__gsc__ctr_opportunities` — pages with high impressions but low CTR
13. `mcp__gsc__content_gaps` — topics with search demand but no real ranking

**Phase 3 — Problems (run in parallel):**
14. `mcp__gsc__traffic_drops` — pages that lost the most traffic with root cause analysis
15. `mcp__gsc__content_decay` — pages declining over three consecutive 30-day periods
16. `mcp__gsc__check_alerts` — position drops, CTR collapses, severity-rated issues
17. `mcp__gsc__cannibalization_check` — keywords where multiple pages compete

**Phase 4 — Deeper analysis (selective, based on findings):**
18. `mcp__gsc__ctr_vs_benchmark` — compare CTR against position benchmarks
19. `mcp__gsc__inspect_url` — spot-check important pages for indexing issues
20. `mcp__gsc__list_sitemaps` — sitemap health and indexed page counts

### If GSC is NOT available:

Note this limitation in the report header. The report will focus on what GA4 can tell us about organic search health, and flag areas where GSC data would add insight (query-level analysis, indexing issues, manual actions).

## Step 3: Analysis

With the data collected, evaluate against the Google SEO checklist. Read `references/google-seo-checklist.md` for the full evaluation framework.

For each area, assign a rating based on the evidence:

| Rating | When to use |
|--------|-------------|
| **STRONG** | Metrics clearly healthy, no issues found |
| **ADEQUATE** | Meeting baseline but specific improvements possible |
| **NEEDS WORK** | Clear problems visible in the data |
| **CRITICAL** | Fundamental issues that likely hurt rankings |
| **N/A** | Can't assess — missing data source or insufficient data |

### What GA4 data tells you about each SEO area:

**Content Quality (E-E-A-T signals):**
- High engagement rates on topic clusters = expertise signals working
- Returning organic visitors = building authority
- Long session durations on in-depth content = satisfying user intent

**Helpful Content signals:**
- Pages with high traffic but low engagement = content not meeting user expectations
- High bounce rates from organic = possible search intent mismatch
- Declining organic traffic across the site = possible helpful content system impact

**Technical health indicators:**
- 404 pages appearing in data = broken links
- Unusual traffic patterns = possible crawling issues
- Very low organic percentage of total traffic = discoverability problems

**Mobile performance:**
- Engagement rate gap between mobile and desktop > 15% = mobile UX issues
- Mobile bounce rate significantly higher = mobile-specific problems
- Mobile traffic share declining = possible mobile rendering issues

**Content performance patterns:**
- Identify the top-performing content (high traffic + high engagement)
- Identify underperformers (traffic but low engagement, or engagement but low traffic)
- Look for content gaps (topic areas with no pages ranking)

## Step 4: Generate the Report

Save the report to a markdown file. Use this path pattern:
- Default: `<ROOT>/writing/notes/seo-report-{site-name}-{YYYY-MM-DD}.md` under the current launch root
- Machine-specific per-root output maps (day-job workspaces, portfolio setups) live in `~/.claude/skills/workspace.local.md` — if it exists and defines a destination for the current root, use that instead

**Portfolio mode:** when approved context (Step 0) shows the workspace manages a set of
sites/companies, resolve **scope** first — one site or the set. Set scope → loop the
active list, one report per site plus a short comparative summary. If analytics access isn't wired
for a site yet, say so and offer what works without it (crawl-based on-page checks, public SERP
context). Ask which scope if ambiguous.
- Or ask the user where they want it saved

### Report Template

```markdown
# SEO Health Report: {Site Name}
**Date:** {YYYY-MM-DD}
**GA4 Property:** {property name} ({property ID})
**Period analyzed:** Last 90 days ({start date} — {end date})
**Data sources:** GA4{, GSC if available}

---

## Executive Summary

{2-3 sentence overview of organic search health. Lead with the most important finding — is organic traffic growing, flat, or declining? What's the single biggest opportunity or risk?}

### Scorecard

| Area | Rating | Key Finding |
|------|--------|-------------|
| Organic Traffic Trend | {rating} | {one line} |
| Content Quality | {rating} | {one line} |
| Landing Page Performance | {rating} | {one line} |
| Mobile Experience | {rating} | {one line} |
| User Engagement | {rating} | {one line} |
| Search Visibility | {rating} | {one line — or N/A if no GSC} |
| Technical Health | {rating} | {one line} |

---

## 1. Organic Traffic Overview

### Trend (last 90 days)

{Show weekly organic sessions as a simple ASCII/text trend or table. Include total sessions, users, and engagement rate.}

### Month-over-Month Change

| Metric | This Month | Last Month | Change |
|--------|-----------|------------|--------|
| Organic Sessions | {n} | {n} | {+/-n%} |
| Organic Users | {n} | {n} | {+/-n%} |
| Engagement Rate | {n%} | {n%} | {+/-n pp} |

### Traffic Sources

| Source | Sessions | % of Organic | Engagement Rate |
|--------|----------|-------------|-----------------|
| Google | {n} | {n%} | {n%} |
| Bing | {n} | {n%} | {n%} |
| ... | ... | ... | ... |

---

## 2. Top Landing Pages (Organic)

{Top 15-20 pages by organic sessions, with engagement metrics}

| Page | Sessions | Users | Engagement Rate | Avg Duration | Bounce Rate |
|------|----------|-------|----------------|-------------|-------------|
| /... | {n} | {n} | {n%} | {n}s | {n%} |

### High-Traffic, Low-Engagement Pages (Red Flags)

{Pages that get organic traffic but have engagement rate < 40% or bounce rate > 70%. These are the most actionable items — content that Google sends traffic to but users don't find satisfying.}

| Page | Sessions | Engagement Rate | Bounce Rate | Issue |
|------|----------|----------------|-------------|-------|
| /... | {n} | {n%} | {n%} | {description} |

---

## 3. Content Quality Assessment

### Engagement Signals

{Overall engagement metrics from organic traffic. Frame these in terms of what they tell us about content quality per Google's helpful content guidelines.}

- **Average engagement rate:** {n%} — {interpretation}
- **Average session duration:** {n}s — {interpretation}
- **New vs Returning ratio:** {n%} new / {n%} returning — {interpretation}

### Content Depth Indicators

{Are users engaging deeply or bouncing? Evidence of E-E-A-T signals.}

---

## 4. Mobile vs Desktop

| Metric | Mobile | Desktop | Gap |
|--------|--------|---------|-----|
| Sessions | {n} ({n%}) | {n} ({n%}) | — |
| Engagement Rate | {n%} | {n%} | {n pp} |
| Avg Duration | {n}s | {n}s | {n}s |
| Bounce Rate | {n%} | {n%} | {n pp} |

{Interpret: is mobile underperforming? If engagement gap > 15pp, flag as a ranking risk due to mobile-first indexing.}

---

## 5. Search Performance (GSC)

{If GSC data is available, include:}
- Top 20 queries by impressions
- Queries with high impressions but low CTR (optimization opportunities)
- Pages with declining position
- Indexing coverage summary

{If GSC is NOT available:}

> **GSC data not available.** Search query analysis, indexing status, and click-through rate optimization require Google Search Console access. Recommend connecting GSC MCP for deeper search insights.
>
> **What you're missing without GSC:**
> - Which queries drive impressions and clicks
> - Pages with high impressions but low CTR (title/description optimization opportunities)
> - Indexing errors and coverage issues
> - Manual actions or security issues

---

## 6. Recommendations

{Prioritized list of actions, ordered by expected impact. Each recommendation should:}
- State the problem clearly (with data)
- Explain why it matters (link to Google's guidelines)
- Give a specific action to take

### High Priority
1. {recommendation with evidence}
2. {recommendation with evidence}

### Medium Priority
3. {recommendation}
4. {recommendation}

### Low Priority / Quick Wins
5. {recommendation}
6. {recommendation}

### Not Assessed (Requires Manual Check)

{Items from the Google SEO checklist that can't be evaluated from GA4/GSC data alone:}
- Structured data implementation → check with Rich Results Test
- Core Web Vitals → check with PageSpeed Insights ({site URL})
- robots.txt and sitemap configuration → check manually or via GSC
- Title tags and meta descriptions → check via site crawl
- Internal linking structure → check via site crawl

---

## Methodology

This report evaluates {site name} against Google's official Search quality guidelines, including:
- [Creating helpful, reliable, people-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)
- [SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
- [Core Web Vitals](https://developers.google.com/search/docs/appearance/core-web-vitals)
- [Mobile-first indexing](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing)

Data was pulled from GA4{/GSC} on {date}. Ratings reflect what the data shows — areas rated N/A require additional tools or manual inspection.
```

## Step 5: Present & Discuss

After saving the report file:

1. Display the **Executive Summary** and **Scorecard** directly in the conversation
2. Tell the user where the full report is saved
3. Offer to dive deeper into any section:

> Full report saved to `{path}`. Want me to dig into any area? I can:
> - Analyze specific pages or content clusters in more detail
> - Pull additional date ranges for trend comparison
> - Focus on a specific recommendation with an action plan
> - Generate a follow-up report comparing to a future period

## Handling Edge Cases

### Very little organic traffic
If organic sessions are < 100 in 90 days, the site likely hasn't established organic visibility yet. Shift the report from "audit existing performance" to "SEO foundation assessment" — focus on what's missing rather than what's underperforming.

### New GA4 property (< 90 days of data)
Reduce the date range to what's available. Note the limited data in the report and recommend re-running after more data accumulates.

### Property has no organic traffic filter
If `session_default_channel_group` doesn't include "Organic Search", the site might not be getting any search traffic at all. This is itself the finding — explain what it means and recommend foundational SEO work.

### GA4 quota limits
If you hit API quota limits (the `run_report` tool can return quota info with `return_property_quota: true`), prioritize the most important queries and skip lower-priority ones. Note any skipped sections in the report.

## Important Notes

- Always use the query patterns from `references/ga4-seo-queries.md` — they use the correct snake_case field names for the protobuf API
- The evaluation framework in `references/google-seo-checklist.md` is based on Google's official documentation, not third-party SEO advice
- Be honest about what the data can and can't tell you — don't speculate about ranking factors beyond what Google has officially documented
- If something can't be assessed from the available data, say so and point the user to the right tool (PageSpeed Insights, Rich Results Test, GSC, site crawl tool)

## Related Skills

If the user has SEO plugin skills installed (seo-*, from the SEO plugin), this skill complements them:

- This skill (`seo-report`) focuses on **data from your own GA4/GSC MCPs** — your actual traffic, engagement, and search performance
- `seo-google` covers PageSpeed Insights, CrUX data, and Indexing API — use it for Core Web Vitals and field performance data
- `seo-technical` does crawl-based technical audits — use it for robots.txt, sitemaps, and crawlability checks
- `seo-content` does E-E-A-T analysis on actual page content — use it to deep-dive pages flagged in this report
- `seo-page` does single-page analysis — use it to investigate specific underperforming pages
- `seo-schema` handles structured data — use it if this report flags missing schema markup

When these skills are available, reference them in the "Not Assessed" section as next steps rather than only pointing to external tools.
