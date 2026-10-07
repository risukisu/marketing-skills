"""Metrics in scripts/analyze_links.py on hand-built crawl dicts."""
from __future__ import annotations

import json

import analyze_links as al

S = "https://www.example.com/"


def page(path, title="", h1="", h2=(), depth=0, canonical="", robots="", status=200):
    return {"url": S + path, "final_url": S + path, "status": status, "title": title or path, "h1": h1 or title or path,
            "h2": list(h2), "canonical": canonical, "meta_robots": robots, "word_count": 100, "depth": depth,
            "found_via": "link", "external_links": 0, "script_tags": 0}


def link(src, dst, anchor="anchor", position="main", nofollow=False):
    return {"source": S + src, "target": S + dst, "anchor": anchor, "position": position, "nofollow": nofollow, "is_image": False}


def make(pages, links, targets=None):
    return {"ok": True, "schema": 1, "source": "test", "start_url": S, "host": "www.example.com", "max_pages": 500,
            "include_params": False, "cap_reached": False, "pages_discovered": len(pages), "pages_crawled": len(pages),
            "blocked_prefixes": [], "sitemaps": [], "pages": {p["url"]: p for p in pages}, "links": links,
            "targets": targets or {}, "warnings": []}


SITE = make(
    [page("", "Home"), page("a.html", "A", depth=1), page("b.html", "B", depth=1), page("c.html", "C", depth=2),
     page("orphan.html", "Orphan", depth=None), page("nav-only.html", "Nav only", depth=1),
     page("noindex.html", "Hidden", depth=None, robots="noindex,follow"),
     page("dup.html", "Dup", depth=None, canonical="/a.html")],
    [link("", "a.html", "A page", "nav"), link("", "b.html", "B page"), link("", "nav-only.html", "Nav", "nav"),
     link("a.html", "c.html", "C page"), link("b.html", "c.html", "C again"), link("c.html", "a.html", "back to A"),
     link("a.html", "a.html", "self"), link("b.html", "a.html", "A", nofollow=True),
     link("a.html", "", "Home", "nav"), link("b.html", "", "Home", "nav")],
)


def test_is_indexable():
    assert al.is_indexable(SITE["pages"][S + "a.html"])
    assert not al.is_indexable(SITE["pages"][S + "noindex.html"])
    assert not al.is_indexable(SITE["pages"][S + "dup.html"])
    assert al.is_indexable(page("x.html", canonical="https://www.example.com/x.html"))


def test_page_counts_split_body_and_nav_and_drop_self_links():
    inbound, outbound = al.link_index(SITE)
    counts = al.page_counts(SITE, inbound, outbound)
    a = counts[S + "a.html"]
    assert a["inlinks_all"] == 3 and a["inlink_sources"] == 3  # home(nav), c, b(nofollow); self link dropped
    assert a["inlinks_body"] == 1  # only c: home is nav, b is nofollow
    assert a["outlinks_unique"] == 2  # c and home; self link dropped
    assert counts[S + "c.html"]["inlinks_body"] == 2
    assert counts[S + "nav-only.html"]["inlinks_body"] == 0
    assert counts[S]["inlinks_body"] == 0 and counts[S]["inlink_sources"] == 2


def test_find_orphans_respects_indexability_and_skips_home():
    inbound, outbound = al.link_index(SITE)
    counts = al.page_counts(SITE, inbound, outbound)
    orphans, near = al.find_orphans(counts, SITE["start_url"])
    assert orphans == [S + "orphan.html"]
    assert S + "noindex.html" not in orphans and S + "dup.html" not in orphans
    assert set(near) == {S + "nav-only.html", S + "b.html"}  # nav-only: nav inbound only; b: one source
    assert S not in near  # the homepage is linked from nav only on most sites; never flagged


def test_find_hubs_and_deep():
    inbound, outbound = al.link_index(SITE)
    counts = al.page_counts(SITE, inbound, outbound)
    assert al.find_hubs(counts, hub_outlinks=2) == [S, S + "b.html"]  # home 3 unique outlinks, b 3 (c, a, home)
    assert al.find_hubs(counts, hub_outlinks=100) == []
    deep, unreachable = al.find_deep(counts, deep_depth=2)
    assert deep == [S + "c.html"]
    assert set(unreachable) == {S + "orphan.html", S + "noindex.html", S + "dup.html"}


def test_pagerank_sums_to_one_and_ranks_the_most_linked_page_highest():
    inbound, outbound = al.link_index(SITE)
    pr = al.pagerank(SITE["pages"], outbound)
    assert abs(sum(pr.values()) - 1.0) < 1e-6
    assert pr[S + "c.html"] > pr[S + "b.html"]  # two body inlinks vs one
    assert pr[S + "orphan.html"] < pr[S + "c.html"]


def test_pagerank_ignores_nofollow_and_self_links():
    data = make([page("", "H"), page("x.html", "X", 1), page("y.html", "Y", 1)],
                [link("", "x.html", nofollow=True), link("", "y.html"), link("x.html", "x.html")])
    _, outbound = al.link_index(data)
    pr = al.pagerank(data["pages"], outbound)
    assert pr[S + "y.html"] > pr[S + "x.html"]
