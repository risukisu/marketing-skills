# Data files

## Contents

- crawl.json (written by crawl_links.py and import_crawl.py)
- metrics.json (written by analyze_links.py)
- priority.txt (written by the skill for analyze_links.py)
- Screaming Frog column mapping (import_crawl.py)

## crawl.json

One object. `pages` holds crawled HTML pages keyed by normalized URL; `links` every internal
link from those pages; `targets` the fetched status of every internal URL, crawled pages
included.

| Key | Type | Meaning |
|---|---|---|
| `schema` | int | 1 |
| `source` | string | `crawl_links.py` or `import_crawl.py` |
| `crawled_at` | string | ISO 8601 UTC |
| `start_url` | string | normalized start page |
| `host` | string | netloc the crawl was pinned to |
| `max_pages` | int or null | page cap (null for imports) |
| `include_params` | bool | query strings kept as distinct URLs |
| `cap_reached` | bool | crawl stopped at the cap |
| `pages_discovered` | int | internal URLs seen, crawled or not |
| `pages_crawled` | int | HTML pages parsed |
| `blocked_prefixes` | list | robots.txt Disallow paths for `*` |
| `sitemaps` | list | sitemap URLs read |
| `pages` | object | url → page record |
| `links` | list | link records |
| `targets` | object | url → target record |
| `warnings` | list | strings for the report's limits section |

Page record: `url`, `final_url`, `status`, `title`, `h1`, `h2` (list), `canonical`, `meta_robots`,
`word_count`, `depth` (int, or null when reachable only through the sitemap), `found_via`
(`start`, `link`, `sitemap`, `export`), `external_links` (count), `script_tags` (count).

Link record: `source`, `target`, `anchor`, `position` (`nav`, `header`, `main`, `aside`,
`footer`, `body`), `nofollow` (bool), `is_image` (bool).

Target record: `status` (first response code, 301 for a redirect), `final_status`, `final_url`,
`chain` (list of hop URLs), `checked` (`GET`, `HEAD`, `blocked`, `export`), `error` (string or
null; `timeout` after one retry).

URL normalization: absolute, scheme and host lowercased, www and bare host collapsed onto the
start host, fragment dropped, query dropped unless `--include-params`, path left as served.

## metrics.json

| Key | Meaning |
|---|---|
| `summary` | `pages`, `orphans`, `near_orphans`, `broken`, `redirects`, `priority_under_linked`, `priority_given` |
| `thresholds` | the constants used, for the report's method section |
| `pages` | url → `inlinks_all`, `inlink_sources`, `inlinks_body`, `outlinks_unique`, `depth`, `indexable`, `title`, `pagerank`, `authority_rank` |
| `ranking_by_inlinks` | urls, fewest body inlinks first |
| `orphans`, `near_orphans` | indexable pages with 0 sources; with 1 source or nav/footer links only (start page skipped) |
| `hubs` | pages over the outbound threshold |
| `deep`, `unreachable_by_links` | depth ≥ threshold; depth null |
| `top_authority` | top 10 urls by internal PageRank |
| `priority_gap` | per priority page: `priority_rank`, `authority_rank`, `inlinks_body`, `gap`, `note` |
| `needs` | targets that need links, in action-plan order: orphans, under-linked priority pages, near-orphans |
| `candidates` | target → up to 5 sources with `title`, `overlap`, `pagerank`, `shared_terms`, `topical` |
| `hygiene` | `broken`, `redirects`, `blocked`, `nofollow_internal`, `generic_anchors`, `low_variety` |
| `mermaid` | graph of the top 30 pages with followed body links |

Body inlinks count distinct source pages linking from `main` or `body` positions without
nofollow. Under-linked priority page: authority rank worse than priority rank, or fewer than 2
body inlinks.

## priority.txt

One URL or path per line, most important first. Blank lines and lines starting with `#` are
ignored. Paths resolve against the start URL.

## Screaming Frog column mapping

`all_inlinks.csv` (Bulk Export → Links → All Inlinks): `Type` (only `Hyperlink` and `Image`
rows are links), `Source`, `Destination`, `Anchor`, `Alt Text` (anchor for image links),
`Status Code`, `Follow` (`False` → nofollow), `Link Position` (`Navigation` → nav, `Header` →
header, `Content` → main, `Sidebar` → aside, `Footer` → footer, anything else → body).

`internal_html.csv` (Internal tab, HTML filter): `Address`, `Content Type`, `Status Code`,
`Title 1`, `H1-1`, every `H2-n`, `Canonical Link Element 1`, `Meta Robots 1`, `Word Count`,
`Crawl Depth`.

Headers match case-insensitively. A missing column is named in `warnings` and left empty.
Redirect chains are not in the export; redirected targets carry their first status only.
