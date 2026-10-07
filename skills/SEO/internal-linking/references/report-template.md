# Report template

ALWAYS use this exact structure. Fill every section; write "none found" rather than leaving a
section out. Keep paths relative to the host (`/blog/post`) except in the header. The Mermaid
block uses `~~~` fences so it can sit inside this template; in the report file, `~~~mermaid` is
fine for GitHub and Obsidian.

```markdown
# Internal linking audit: {host}

**Date:** {YYYY-MM-DD}
**Data source:** {crawl_links.py, N pages crawled of M discovered | Screaming Frog export, N pages}
**Priority pages:** {user list | top organic landing pages from GA4/GSC | none given}
**Limits:** {static HTML only; cap reached or not; robots-blocked prefixes; warnings from the scripts}

## 1. Summary

| Pages | Orphans | Near-orphans | Broken targets | Priority pages under-linked |
|---|---|---|---|---|
| {n} | {n} | {n} | {n} | {n of m} |

{Three sentences: what the structure looks like, the single biggest problem, what to do first.}

## 2. Pages by inbound links (lowest first)

{Table from analyze_links.py: Page, Body inlinks, All inlinks, Sources, PageRank, Depth, Indexable. Top 30.}

## 3. Orphans and near-orphans

{One bullet per page: path, title, why it matters, then the recommended sources (2+ for orphans).}

## 4. Internal link opportunities

| # | Source | Target | Anchor | Draft sentence | Why |
|---|---|---|---|---|---|
| 1 | /source | /target | descriptive anchor | A sentence that would sit in the source page with the anchor in it. | shared topic; source authority; fixes orphan |

## 5. Link equity map

- **Depth tiers:** {pages at depth 0, 1, 2, 3, 4+, sitemap-only}
- **Top authority:** {table from analyze_links.py}
- **Priority gap:** {table from analyze_links.py, or "no priority pages given"}

~~~mermaid
{graph from analyze_links.py}
~~~

## 6. Action plan: top 20 links to add now

| # | Source | Target | Anchor | Fixes |
|---|---|---|---|---|
| 1 | /source | /target | anchor | orphan / priority gap / near-orphan |

{Order: orphans first, then priority pages by gap, then near-orphans. Each row is one row from section 4.}

## 7. Hygiene

- **Broken targets:** {table}
- **Redirected targets:** {table}
- **Generic anchors:** {table}
- **Low anchor variety:** {table}
- **Nofollow internal links:** {table}
- **Over-linked pages:** {list with unique outlink counts}
- **Blocked by robots.txt:** {list}

## 8. Method and limits

Scripts: `crawl_links.py` ({cap}, {delay}), `analyze_links.py` (hub threshold {n}, deep depth {n},
PageRank damping {n}). Static HTML only; JavaScript-rendered links are not seen. {Any warning.}
```
