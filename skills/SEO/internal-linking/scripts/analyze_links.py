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
