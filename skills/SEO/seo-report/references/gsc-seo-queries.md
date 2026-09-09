# GSC MCP Query Reference for SEO Reports

The GSC MCP (Suganthans-GSC-MCP fork) provides 20 specialized tools for Google Search Console data. These tools go beyond raw data — many include built-in analysis like benchmarking, decay detection, and cannibalization checks.

**Status:** The GSC MCP server is currently broken (hangs on initialize). This reference documents the tools for when it becomes available. The tool names use the prefix `mcp__gsc__`.

## Table of Contents

1. [Overview Tools](#overview)
2. [Opportunity Analysis](#opportunities)
3. [Problem Detection](#problems)
4. [Content Analysis](#content)
5. [Technical / Indexing](#technical)
6. [Custom Queries](#custom)
7. [Recommended Query Sequence for SEO Report](#sequence)

---

## Overview Tools {#overview}

### Site Snapshot
```
Tool: mcp__gsc__site_snapshot
```
Quick overview of site performance with period comparison. Use this first to get the lay of the land — total clicks, impressions, average CTR, average position, and how these compare to the previous period.

---

## Opportunity Analysis {#opportunities}

### Quick Wins (Low-Hanging Fruit)
```
Tool: mcp__gsc__quick_wins
```
Keywords at positions 4-15 with high impressions that could reach page 1 with optimization. These are the highest-ROI SEO actions — you're already close to ranking well. Map directly to the "Recommendations > High Priority" section of the report.

### CTR Opportunities
```
Tool: mcp__gsc__ctr_opportunities
```
Pages with high impressions but low CTR. Indicates title tags and meta descriptions aren't compelling enough, or there's a rich snippet opportunity. These pages rank well but don't get clicked — fixing titles/descriptions is often the cheapest SEO win.

### Content Gaps
```
Tool: mcp__gsc__content_gaps
```
Topics where the site has search demand (impressions) but no real ranking (positions >20). Identifies content that needs to be created or substantially improved to capture existing demand.

---

## Problem Detection {#problems}

### Traffic Drops
```
Tool: mcp__gsc__traffic_drops
```
Pages that lost the most traffic recently, with root cause analysis. Critical for detecting algorithm impact, content quality issues, or technical problems. Maps to report sections on content quality and technical health.

### Content Decay
```
Tool: mcp__gsc__content_decay
```
Pages declining over three consecutive 30-day periods. Unlike traffic_drops (which catches sudden losses), this catches slow, steady decline — often the first sign that content is becoming outdated or competitors have improved.

### Check Alerts
```
Tool: mcp__gsc__check_alerts
```
Position drops, CTR collapses, click losses, disappeared pages — with severity ratings. Use as an early warning system. Flag anything rated "high severity" as CRITICAL in the report.

### Cannibalization Check
```
Tool: mcp__gsc__cannibalization_check
```
Keywords where multiple pages on the site compete against each other. Internal competition dilutes ranking power — consolidating or differentiating these pages is often a high-impact fix.

---

## Content Analysis {#content}

### CTR vs Benchmark
```
Tool: mcp__gsc__ctr_vs_benchmark
```
Compare actual CTR against industry benchmarks by position. If a page ranks #3 but gets half the expected CTR, it's an optimization opportunity. If it gets above-benchmark CTR, it's a model to replicate.

### Topic Cluster Performance
```
Tool: mcp__gsc__topic_cluster_performance
```
Aggregate performance for pages matching a URL pattern. Useful for evaluating content clusters (e.g., all `/blog/seo-*` pages). Shows whether content strategy is working at the topic level.

### Content Recommendations
```
Tool: mcp__gsc__content_recommendations
```
Actionable recommendations: pages to update, content to create, pages to consolidate. This tool does its own analysis — use it as a cross-check against your own recommendations.

---

## Technical / Indexing {#technical}

### URL Inspection
```
Tool: mcp__gsc__inspect_url
```
Check if a specific URL is indexed, show indexing status, canonical info, mobile usability. Use for spot-checking important pages mentioned in the GA4 data — if a high-traffic landing page has indexing issues, that's critical.

### Sitemap Tools
```
Tool: mcp__gsc__list_sitemaps
```
List all submitted sitemaps with status and indexed page counts. Compare "submitted" vs "indexed" counts — a large gap indicates indexing problems.

```
Tool: mcp__gsc__submit_sitemap
```
Notify Google of a new/updated sitemap. Useful as a follow-up action after the report.

### URL Submission
```
Tool: mcp__gsc__submit_url
```
Submit a single URL to Google's Indexing API for crawling. Useful for important pages that aren't indexed.

```
Tool: mcp__gsc__submit_batch
```
Batch submit up to 200 URLs (daily quota: 200). For broader indexing pushes.

---

## Custom Queries {#custom}

### Advanced Search Analytics
```
Tool: mcp__gsc__advanced_search_analytics
```
Custom query with flexible dimensions (query, page, country, device, date) and filters. Use when the built-in tools don't cover what you need — for example, filtering by country or device to identify geographic/device-specific issues.

### Multi-Site Dashboard
```
Tool: mcp__gsc__multi_site_dashboard
```
Health check across multiple GSC properties. Useful if the user manages several sites.

### Generate Report
```
Tool: mcp__gsc__generate_report
```
The GSC MCP's own comprehensive markdown report. Can be used as a companion to the GA4-based report, or as raw material to incorporate into the unified SEO report.

### Verify Claim
```
Tool: mcp__gsc__verify_claim
```
Verify numeric claims against live GSC data. Use for self-checking — before putting a number in the report, verify it.

---

## Recommended Query Sequence for SEO Report {#sequence}

When GSC is available, run these in this order:

### Phase 1: Overview (run first)
1. `site_snapshot` — baseline performance and trends

### Phase 2: Opportunities (run in parallel)
2. `quick_wins` — low-hanging keyword opportunities
3. `ctr_opportunities` — title/description optimization targets
4. `content_gaps` — new content opportunities

### Phase 3: Problems (run in parallel)
5. `traffic_drops` — recent losses
6. `content_decay` — gradual decline
7. `check_alerts` — severity-rated issues
8. `cannibalization_check` — internal competition

### Phase 4: Deeper analysis (selective, based on findings)
9. `ctr_vs_benchmark` — for pages flagged in Phase 2
10. `topic_cluster_performance` — for content cluster evaluation
11. `inspect_url` — for specific pages with issues
12. `content_recommendations` — cross-check your recommendations
13. `list_sitemaps` — technical health check

### Phase 5: Actions (optional, user-directed)
14. `submit_url` / `submit_batch` — if indexing issues found
15. `submit_sitemap` — if sitemap issues found
