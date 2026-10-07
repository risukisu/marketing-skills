#!/usr/bin/env python3
"""Compute internal-link metrics from crawl.json. Deterministic, no network.

    python scripts/analyze_links.py crawl.json [--priority priority.txt] [--out metrics.json]
                                    [--hub-outlinks 100] [--deep-depth 4]

Prints markdown tables for the report and writes metrics.json (schema in
references/crawl-data.md): inbound and outbound counts per page, orphans and near-orphans,
over-linked hub pages, click depth, internal PageRank, the priority-gap table, hygiene
findings, and a candidate-source shortlist for every page that needs links. Relevance
judgment is not done here; the shortlist is for the model to judge.

priority.txt holds one URL per line, most important first. Exit code 1 only when crawl.json
cannot be read. Standard library only, Python 3.9+.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from collections import defaultdict

# Google's long-standing "keep the links on a page to a reasonable number" was read as about
# 100 for years; above it a page spreads what it passes on too thin. Override with --hub-outlinks.
HUB_OUTLINKS = 100
# Four or more clicks from the start page is where crawl frequency and authority drop off.
DEEP_DEPTH = 4
# A target with this many inbound links and a single anchor text reads as manipulation and tells
# the crawler less than varied anchors would.
VARIETY_MIN_INLINKS = 5
# Enough candidate sources for the model to judge relevance without reading the whole site.
CANDIDATES_PER_TARGET = 5
# PageRank parameters from the original paper (0.85) and typical convergence on sites of a few
# thousand pages (50 iterations); tolerance stops early once the ranking has settled.
DAMPING = 0.85
ITERATIONS = 50
TOLERANCE = 1e-6
# Two body links from different pages is the floor below which a page leans on navigation alone.
MIN_BODY_INLINKS = 2
# More nodes than this and the Mermaid graph is unreadable in a markdown preview.
MERMAID_NODES = 30
# Anchors that tell the reader and the crawler nothing about the target.
GENERIC_ANCHORS = {"click here", "here", "read more", "learn more", "this", "link", "more", "this post",
                   "this article", "this page", "continue reading", "see more", "website", "page", "article"}
# Link positions that count as editorial body links. Nav, header, aside, footer carry less weight.
BODY_POSITIONS = {"main", "body"}
# Words ignored when comparing titles and headings for the candidate shortlist.
STOP_WORDS = {"a", "an", "and", "the", "of", "for", "to", "in", "on", "with", "by", "at", "from", "is", "are",
              "how", "what", "why", "your", "you", "our", "we", "it", "that", "this", "or", "as", "be", "vs"}
TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


def load(path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _same_page(a: str, b: str) -> bool:
    return a.rstrip("/") == b.rstrip("/")


def is_indexable(page: dict) -> bool:
    """200 HTML page without noindex whose canonical, if any, points at itself."""
    if (page.get("status") or 0) != 200:
        return False
    if "noindex" in (page.get("meta_robots") or "").lower():
        return False
    canonical = (page.get("canonical") or "").strip()
    if canonical:
        resolved = urllib.parse.urljoin(page["url"], canonical)
        if not _same_page(resolved.split("#")[0], page["url"]):
            return False
    return True


def link_index(data: dict):
    """Per-target inbound and per-source outbound link records; self links dropped."""
    inbound: dict = defaultdict(list)
    outbound: dict = defaultdict(list)
    for l in data["links"]:
        if l["source"] == l["target"]:
            continue
        inbound[l["target"]].append(l)
        outbound[l["source"]].append(l)
    return inbound, outbound


def page_counts(data: dict, inbound: dict, outbound: dict) -> dict:
    counts = {}
    for url, page in data["pages"].items():
        inl = inbound.get(url, [])
        counts[url] = {
            "title": page.get("title") or page.get("h1") or url,
            "inlinks_all": len(inl),
            "inlink_sources": len({l["source"] for l in inl}),
            "inlinks_body": len({l["source"] for l in inl if l["position"] in BODY_POSITIONS and not l["nofollow"]}),
            "outlinks_unique": len({l["target"] for l in outbound.get(url, [])}),
            "depth": page.get("depth"),
            "indexable": is_indexable(page),
        }
    return counts


def find_orphans(counts: dict, start_url: str):
    """Orphans: indexable pages nobody links to. Near-orphans: one source, or nav/footer links only.

    The start page is skipped: on most sites it is linked from navigation only, which is normal.
    """
    orphans, near = [], []
    for url, c in counts.items():
        if not c["indexable"] or url == start_url:
            continue
        if c["inlink_sources"] == 0:
            orphans.append(url)
        elif c["inlink_sources"] == 1 or c["inlinks_body"] == 0:
            near.append(url)
    return sorted(orphans), sorted(near)


def find_hubs(counts: dict, hub_outlinks: int = HUB_OUTLINKS) -> list:
    return sorted(u for u, c in counts.items() if c["outlinks_unique"] > hub_outlinks)


def find_deep(counts: dict, deep_depth: int = DEEP_DEPTH):
    deep = sorted(u for u, c in counts.items() if c["depth"] is not None and c["depth"] >= deep_depth)
    unreachable = sorted(u for u, c in counts.items() if c["depth"] is None)
    return deep, unreachable


def pagerank(pages: dict, outbound: dict, damping: float = DAMPING, iterations: int = ITERATIONS,
             tolerance: float = TOLERANCE) -> dict:
    """Internal PageRank over crawled pages; followed links only; dangling mass spread evenly."""
    nodes = list(pages)
    n = len(nodes)
    if n == 0:
        return {}
    out_targets = {u: {l["target"] for l in outbound.get(u, []) if not l["nofollow"] and l["target"] in pages} for u in nodes}
    in_sources: dict = defaultdict(set)
    for u, ts in out_targets.items():
        for t in ts:
            in_sources[t].add(u)
    pr = {u: 1.0 / n for u in nodes}
    for _ in range(iterations):
        dangling = sum(pr[u] for u in nodes if not out_targets[u])
        new = {}
        for u in nodes:
            inflow = sum(pr[s] / len(out_targets[s]) for s in in_sources.get(u, ()))
            new[u] = (1 - damping) / n + damping * (inflow + dangling / n)
        delta = sum(abs(new[u] - pr[u]) for u in nodes)
        pr = new
        if delta < tolerance:
            break
    return pr


def _match_url(raw: str, known: dict, start_url: str):
    """Find a crawled page for a user-typed URL: full URL, or a path like /pricing.html."""
    raw = (raw or "").strip()
    if not raw:
        return None
    candidate = urllib.parse.urljoin(start_url, raw) if raw.startswith("/") else raw
    for variant in (candidate, candidate.rstrip("/"), candidate + "/"):
        if variant in known:
            return variant
    return None


def priority_gap(priority: list, pr: dict, counts: dict, start_url: str) -> list:
    """Each priority page's internal-authority rank against its priority rank. Positive gap = under-linked."""
    ranked = sorted(pr, key=pr.get, reverse=True)
    rank_of = {u: i + 1 for i, u in enumerate(ranked)}
    rows = []
    for i, raw in enumerate(priority, 1):
        url = _match_url(raw, counts, start_url)
        if url is None:
            rows.append({"url": raw, "priority_rank": i, "authority_rank": None, "inlinks_body": None, "gap": None,
                         "note": "not crawled"})
            continue
        rows.append({"url": url, "priority_rank": i, "authority_rank": rank_of[url],
                     "inlinks_body": counts[url]["inlinks_body"], "gap": rank_of[url] - i, "note": ""})
    return rows


def _generic(anchor: str) -> bool:
    text = (anchor or "").strip().lower().rstrip(".!:,")
    return not text or text in GENERIC_ANCHORS


def hygiene(data: dict, inbound: dict, variety_min: int = VARIETY_MIN_INLINKS) -> dict:
    """Broken and redirected targets, blocked targets, nofollow internal links, generic anchors, low anchor variety."""
    def sources_of(t):
        return sorted({l["source"] for l in inbound.get(t, [])})

    broken, redirects, blocked = [], [], []
    for t, info in data["targets"].items():
        if info.get("checked") == "blocked":
            blocked.append(t)
        elif info.get("error") or (info.get("final_status") or 0) >= 400:
            broken.append({"target": t, "status": info.get("final_status"), "error": info.get("error"), "sources": sources_of(t)})
        elif info.get("chain") or 300 <= (info.get("status") or 0) < 400:
            redirects.append({"target": t, "status": info.get("status"), "final_url": info.get("final_url"),
                              "hops": len(info.get("chain") or []), "sources": sources_of(t)})
    nofollow, generic = [], []
    for l in data["links"]:
        if l["source"] == l["target"]:
            continue
        if l["nofollow"]:
            nofollow.append({"source": l["source"], "target": l["target"], "anchor": l["anchor"]})
        if _generic(l["anchor"]):
            generic.append({"source": l["source"], "target": l["target"], "anchor": l["anchor"].strip() or "(empty)",
                            "position": l["position"]})
    low_variety = []
    for t, inl in inbound.items():
        followed = [l for l in inl if not l["nofollow"]]
        if len(followed) >= variety_min and len({l["anchor"].strip().lower() for l in followed}) == 1:
            low_variety.append({"target": t, "inlinks": len(followed), "anchor": followed[0]["anchor"]})
    return {"broken": sorted(broken, key=lambda b: b["target"]), "redirects": sorted(redirects, key=lambda r: r["target"]),
            "blocked": sorted(blocked), "nofollow_internal": nofollow, "generic_anchors": generic,
            "low_variety": sorted(low_variety, key=lambda v: -v["inlinks"])}


def tokens(text: str) -> set:
    return {t for t in TOKEN_RE.findall((text or "").lower()) if t not in STOP_WORDS}


def _page_tokens(page: dict) -> set:
    return tokens(" ".join([page.get("title") or "", page.get("h1") or ""] + list(page.get("h2") or [])))


def candidate_sources(data: dict, inbound: dict, pr: dict, needs: list, per_target: int = CANDIDATES_PER_TARGET) -> dict:
    """Shortlist of pages that could link to each target: title/heading overlap weighted by PageRank.

    Excludes the target itself, pages that already link to it, and non-indexable pages. When no
    page shares a term, falls back to the highest-authority pages and marks them topical=False.
    """
    toks = {u: _page_tokens(p) for u, p in data["pages"].items()}
    out = {}
    for t in needs:
        existing = {l["source"] for l in inbound.get(t, [])}
        tt = toks.get(t, set())
        scored = []
        for s, st in toks.items():
            if s == t or s in existing or not is_indexable(data["pages"][s]):
                continue
            shared = tt & st
            overlap = len(shared) / len(tt | st) if (tt or st) else 0.0
            scored.append((overlap * (pr.get(s, 0.0) + 1e-9), overlap, pr.get(s, 0.0), s, shared))
        topical = sorted((c for c in scored if c[1] > 0), key=lambda c: (-c[0], c[3]))[:per_target]
        chosen, is_topical = (topical, True) if topical else (sorted(scored, key=lambda c: (-c[2], c[3]))[:per_target], False)
        out[t] = [{"source": s, "title": data["pages"][s].get("title") or s, "overlap": round(o, 3),
                   "pagerank": round(p, 5), "shared_terms": sorted(sh)[:8], "topical": is_topical}
                  for _, o, p, s, sh in chosen]
    return out


def _label(url: str, start_url: str) -> str:
    path = url[len(start_url) - 1:] if url.startswith(start_url) else url
    return (path or "/").replace('"', "'")


def mermaid_graph(data: dict, outbound: dict, pr: dict, limit: int = MERMAID_NODES) -> str:
    """Top pages by PageRank with their followed body links, as a Mermaid graph."""
    top = sorted(pr, key=lambda u: (-pr[u], u))[:limit]
    ids = {u: f"n{i}" for i, u in enumerate(top)}
    lines = ["graph LR"] + [f'  {ids[u]}["{_label(u, data["start_url"])}"]' for u in top]
    seen = set()
    for s in top:
        for l in outbound.get(s, []):
            t = l["target"]
            if t in ids and not l["nofollow"] and l["position"] in BODY_POSITIONS and (s, t) not in seen:
                seen.add((s, t))
                lines.append(f"  {ids[s]} --> {ids[t]}")
    return "\n".join(lines)


def analyze(data: dict, priority=None, hub_outlinks: int = HUB_OUTLINKS, deep_depth: int = DEEP_DEPTH) -> dict:
    priority = [p for p in (priority or []) if p and not p.strip().startswith("#")]
    inbound, outbound = link_index(data)
    counts = page_counts(data, inbound, outbound)
    pr = pagerank(data["pages"], outbound)
    ranked = sorted(pr, key=lambda u: (-pr[u], u))
    rank_of = {u: i + 1 for i, u in enumerate(ranked)}
    for u, c in counts.items():
        c["pagerank"] = round(pr.get(u, 0.0), 6)
        c["authority_rank"] = rank_of.get(u)
    orphans, near = find_orphans(counts, data["start_url"])
    hubs = find_hubs(counts, hub_outlinks)
    deep, unreachable = find_deep(counts, deep_depth)
    gap_rows = priority_gap(priority, pr, counts, data["start_url"]) if priority else []
    under_linked = [r["url"] for r in gap_rows if r["gap"] is not None and (r["gap"] > 0 or r["inlinks_body"] < MIN_BODY_INLINKS)]
    needs = []
    for u in orphans + under_linked + near:
        if u not in needs:
            needs.append(u)
    hyg = hygiene(data, inbound)
    return {
        "schema": 1, "source": data.get("source"), "start_url": data["start_url"], "host": data.get("host"),
        "crawled_at": data.get("crawled_at"), "pages_crawled": data.get("pages_crawled"),
        "pages_discovered": data.get("pages_discovered"), "cap_reached": data.get("cap_reached"),
        "blocked_prefixes": data.get("blocked_prefixes", []), "warnings": data.get("warnings", []),
        "thresholds": {"hub_outlinks": hub_outlinks, "deep_depth": deep_depth, "variety_min_inlinks": VARIETY_MIN_INLINKS,
                       "min_body_inlinks": MIN_BODY_INLINKS, "candidates_per_target": CANDIDATES_PER_TARGET,
                       "damping": DAMPING, "iterations": ITERATIONS},
        "summary": {"pages": len(counts), "orphans": len(orphans), "near_orphans": len(near), "broken": len(hyg["broken"]),
                    "redirects": len(hyg["redirects"]), "priority_under_linked": len(under_linked),
                    "priority_given": len(priority)},
        "pages": counts,
        "ranking_by_inlinks": sorted(counts, key=lambda u: (counts[u]["inlinks_body"], counts[u]["inlinks_all"], u)),
        "orphans": orphans, "near_orphans": near, "hubs": hubs, "deep": deep, "unreachable_by_links": unreachable,
        "top_authority": ranked[:10], "priority_gap": gap_rows, "needs": needs,
        "candidates": candidate_sources(data, inbound, pr, needs), "hygiene": hyg,
        "mermaid": mermaid_graph(data, outbound, pr),
    }


def _row(cells) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def _table(headers, rows) -> str:
    return "\n".join([_row(headers), _row(["---"] * len(headers))] + [_row(r) for r in rows]) if rows else "_none_"


def render_markdown(m: dict) -> str:
    L = lambda u: _label(u, m["start_url"])  # noqa: E731
    pages = m["pages"]
    s = m["summary"]
    out = [f"# Internal link metrics for {m['host']}", "",
           f"Pages {s['pages']} · orphans {s['orphans']} · near-orphans {s['near_orphans']} · broken targets {s['broken']} · "
           f"redirected targets {s['redirects']} · priority pages under-linked {s['priority_under_linked']} of {s['priority_given']}", ""]
    out += ["## Pages by inbound links (lowest first, top 30)", "",
            _table(["Page", "Body inlinks", "All inlinks", "Sources", "PageRank", "Depth", "Indexable"],
                   [[L(u), pages[u]["inlinks_body"], pages[u]["inlinks_all"], pages[u]["inlink_sources"], pages[u]["pagerank"],
                     "sitemap only" if pages[u]["depth"] is None else pages[u]["depth"], "yes" if pages[u]["indexable"] else "no"]
                    for u in m["ranking_by_inlinks"][:30]]), ""]
    out += ["## Orphans and near-orphans with candidate sources", ""]
    for group, urls in (("Orphan", m["orphans"]), ("Near-orphan", m["near_orphans"])):
        for u in urls:
            cands = "; ".join(f"{L(c['source'])} ({', '.join(c['shared_terms']) or 'no shared terms'})" for c in m["candidates"].get(u, []))
            out.append(f"- **{group}** {L(u)} — {pages[u]['title']} → candidates: {cands or 'none'}")
    if not m["orphans"] and not m["near_orphans"]:
        out.append("_none_")
    out += ["", "## Priority gap", ""]
    if m["priority_gap"]:
        out.append(_table(["Priority", "Page", "Authority rank", "Body inlinks", "Gap", "Note"],
                          [[r["priority_rank"], L(r["url"]) if r["note"] != "not crawled" else r["url"], r["authority_rank"] or "-",
                            r["inlinks_body"] if r["inlinks_body"] is not None else "-", r["gap"] if r["gap"] is not None else "-", r["note"]]
                           for r in m["priority_gap"]]))
        for u in [r["url"] for r in m["priority_gap"] if r["url"] in m["candidates"]]:
            cands = "; ".join(f"{L(c['source'])} ({', '.join(c['shared_terms']) or 'no shared terms'})" for c in m["candidates"][u])
            out.append(f"- candidates for {L(u)}: {cands or 'none'}")
    else:
        out.append("_no priority pages given_")
    out += ["", "## Top authority (internal PageRank)", "",
            _table(["Rank", "Page", "PageRank", "Body inlinks", "Outlinks"],
                   [[i + 1, L(u), pages[u]["pagerank"], pages[u]["inlinks_body"], pages[u]["outlinks_unique"]] for i, u in enumerate(m["top_authority"])]),
            "", "## Structure", "",
            f"- Over-linked pages (> {m['thresholds']['hub_outlinks']} unique outlinks): " + (", ".join(L(u) for u in m["hubs"]) or "none"),
            f"- Deep pages (depth ≥ {m['thresholds']['deep_depth']}): " + (", ".join(L(u) for u in m["deep"]) or "none"),
            "- Reachable only through the sitemap: " + (", ".join(L(u) for u in m["unreachable_by_links"]) or "none"),
            "", "```mermaid", m["mermaid"], "```", ""]
    h = m["hygiene"]
    out += ["## Hygiene", "", "### Broken targets", _table(["Target", "Status", "Linked from"],
            [[L(b["target"]), b["status"] or b["error"], ", ".join(L(x) for x in b["sources"])] for b in h["broken"]]),
            "", "### Redirected targets", _table(["Target", "Status", "Final URL", "Hops", "Linked from"],
            [[L(r["target"]), r["status"], L(r["final_url"]) if r["final_url"] else "-", r["hops"], ", ".join(L(x) for x in r["sources"])] for r in h["redirects"]]),
            "", "### Generic anchors", _table(["Source", "Target", "Anchor", "Position"],
            [[L(g["source"]), L(g["target"]), g["anchor"], g["position"]] for g in h["generic_anchors"]]),
            "", "### Low anchor variety", _table(["Target", "Followed inlinks", "The one anchor"],
            [[L(v["target"]), v["inlinks"], v["anchor"]] for v in h["low_variety"]]),
            "", "### Nofollow internal links", _table(["Source", "Target", "Anchor"],
            [[L(n["source"]), L(n["target"]), n["anchor"]] for n in h["nofollow_internal"]]),
            "", "### Blocked by robots.txt", ", ".join(L(b) for b in h["blocked"]) or "_none_", ""]
    if m["warnings"]:
        out += ["## Warnings", ""] + [f"- {w}" for w in m["warnings"]] + [""]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("crawl", help="crawl.json from crawl_links.py or import_crawl.py")
    ap.add_argument("--priority", help="text file, one URL or path per line, most important first")
    ap.add_argument("--out", default="metrics.json")
    ap.add_argument("--hub-outlinks", type=int, default=HUB_OUTLINKS)
    ap.add_argument("--deep-depth", type=int, default=DEEP_DEPTH)
    args = ap.parse_args(argv)
    try:
        data = load(args.crawl)
    except (OSError, ValueError) as e:
        print(f"Cannot read {args.crawl}: {e}", file=sys.stderr)
        return 1
    priority = []
    if args.priority:
        with open(args.priority, encoding="utf-8") as f:
            priority = [line.strip() for line in f if line.strip()]
    metrics = analyze(data, priority, args.hub_outlinks, args.deep_depth)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=1, ensure_ascii=False)
    print(render_markdown(metrics))
    print(f"\n_metrics written to {args.out}_")
    return 0


if __name__ == "__main__":
    sys.exit(main())
