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


def test_priority_gap_matches_paths_and_flags_unknown():
    inbound, outbound = al.link_index(SITE)
    counts = al.page_counts(SITE, inbound, outbound)
    pr = al.pagerank(SITE["pages"], outbound)
    rows = al.priority_gap(["/orphan.html", S + "c.html", "/missing.html"], pr, counts, S)
    assert rows[0]["url"] == S + "orphan.html" and rows[0]["priority_rank"] == 1 and rows[0]["gap"] > 0
    assert rows[1]["url"] == S + "c.html" and rows[1]["authority_rank"] <= 3
    assert rows[2]["note"] == "not crawled" and rows[2]["gap"] is None


def test_hygiene_classifies_targets_and_anchors():
    data = make(
        [page("", "Home"), page("p.html", "P", 1), page("q.html", "Q", 1)],
        [link("", "q.html", "click here"), link("", "q.html", ""), link("p.html", "gone.html", "old"),
         link("p.html", "moved.html", "moved"), link("p.html", "secret.html", "s"), link("q.html", "p.html", "P", nofollow=True)]
        + [link("q.html", "p.html", "Same Anchor")] * 5,  # five followed links, one anchor
        targets={S + "gone.html": {"status": 404, "final_status": 404, "final_url": S + "gone.html", "chain": [], "checked": "HEAD", "error": None},
                 S + "moved.html": {"status": 301, "final_status": 200, "final_url": S + "p.html", "chain": [S + "p.html"], "checked": "HEAD", "error": None},
                 S + "secret.html": {"status": None, "final_status": None, "final_url": S + "secret.html", "chain": [], "checked": "blocked", "error": None},
                 S + "p.html": {"status": 200, "final_status": 200, "final_url": S + "p.html", "chain": [], "checked": "GET", "error": None}},
    )
    inbound, _ = al.link_index(data)
    h = al.hygiene(data, inbound)
    assert [b["target"] for b in h["broken"]] == [S + "gone.html"] and h["broken"][0]["sources"] == [S + "p.html"]
    assert h["redirects"][0]["target"] == S + "moved.html" and h["redirects"][0]["final_url"] == S + "p.html"
    assert h["blocked"] == [S + "secret.html"]
    assert {g["anchor"] for g in h["generic_anchors"]} == {"click here", "(empty)"}
    assert h["nofollow_internal"][0]["source"] == S + "q.html"
    assert h["low_variety"][0]["target"] == S + "p.html" and h["low_variety"][0]["inlinks"] == 5


def test_candidate_sources_prefer_topical_overlap_and_skip_existing_links():
    data = make(
        [page("", "Home", h2=["Why teams pick us"]), page("plan.html", "Sprint planning for small teams", depth=1),
         page("retro.html", "Running retrospectives that stick", depth=1),
         page("orphan.html", "Estimating work without story points", h2=["Sprint planning without estimates"], depth=None),
         page("linked.html", "Sprint planning tools", depth=1)],
        [link("", "plan.html"), link("", "retro.html"), link("", "linked.html"), link("linked.html", "orphan.html", "estimates")],
    )
    inbound, outbound = al.link_index(data)
    pr = al.pagerank(data["pages"], outbound)
    cands = al.candidate_sources(data, inbound, pr, [S + "orphan.html"])
    sources = [c["source"] for c in cands[S + "orphan.html"]]
    assert sources[0] == S + "plan.html"  # shares "sprint" and "planning"
    assert S + "linked.html" not in sources  # already links to the target
    assert S + "orphan.html" not in sources
    assert cands[S + "orphan.html"][0]["topical"] is True
    assert "sprint" in cands[S + "orphan.html"][0]["shared_terms"]


def test_mermaid_graph_has_nodes_and_body_edges():
    inbound, outbound = al.link_index(SITE)
    pr = al.pagerank(SITE["pages"], outbound)
    g = al.mermaid_graph(SITE, outbound, pr)
    assert g.startswith("graph LR")
    assert '["/c.html"]' in g and '["/"]' in g
    assert "-->" in g


def test_analyze_end_to_end_on_fixture_site(site, tmp_path, capsys):
    from crawl_links import crawl
    data = crawl(site, max_pages=50, delay=0)
    m = al.analyze(data, priority=["/pricing.html", "/services.html", "/blog/post-c.html"])
    assert m["orphans"] == [site + "blog/post-c.html"]
    assert m["needs"][0] == site + "blog/post-c.html"
    assert [b["target"] for b in m["hygiene"]["broken"]] == [site + "old-page.html"]
    assert m["hygiene"]["redirects"][0]["final_url"] == site + "pricing.html"
    assert {g["anchor"] for g in m["hygiene"]["generic_anchors"]} == {"click here"}
    assert m["priority_gap"][0]["url"] == site + "pricing.html"
    post_a = site + "blog/post-a.html"
    assert post_a in [c["source"] for c in m["candidates"][site + "blog/post-c.html"]]
    assert m["summary"]["pages"] == 8 and m["summary"]["orphans"] == 1 and m["summary"]["broken"] == 1
    md = al.render_markdown(m)
    assert "## Pages by inbound links" in md and "## Hygiene" in md and "graph LR" in md and "## Priority gap" in md

    crawl_path = tmp_path / "crawl.json"
    crawl_path.write_text(json.dumps(data), encoding="utf-8")
    prio = tmp_path / "priority.txt"
    prio.write_text("/pricing.html\n\n# comment\n/services.html\n", encoding="utf-8")
    out = tmp_path / "metrics.json"
    assert al.main([str(crawl_path), "--priority", str(prio), "--out", str(out)]) == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert [r["url"] for r in written["priority_gap"]] == [site + "pricing.html", site + "services.html"]
    assert "## Pages by inbound links" in capsys.readouterr().out
    assert al.main([str(tmp_path / "nope.json")]) == 1
