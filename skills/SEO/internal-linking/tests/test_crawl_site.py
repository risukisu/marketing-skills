"""Crawler end to end against the fixture site (tests/fixture_site via fixture_server)."""
from __future__ import annotations

import json

import crawl_links
from crawl_links import crawl, main


def by_target(data, path):
    return data["targets"][data["start_url"] + path.lstrip("/")]


def test_crawl_finds_all_pages_and_the_sitemap_orphan(site):
    data = crawl(site, max_pages=50, delay=0)
    assert data["ok"] is True
    assert data["pages_crawled"] == 8
    assert data["cap_reached"] is False
    orphan = data["pages"][site + "blog/post-c.html"]
    assert orphan["found_via"] == "sitemap"
    assert orphan["depth"] is None
    assert data["pages"][site]["depth"] == 0
    assert data["pages"][site + "blog/post-a.html"]["depth"] == 2
    assert data["sitemaps"] == [site + "sitemap.xml"]
    assert data["blocked_prefixes"] == ["/private/"]


def test_crawl_records_link_anchor_position_and_flags(site):
    data = crawl(site, max_pages=50, delay=0)
    links = {(l["source"], l["target"], l["anchor"]): l for l in data["links"]}
    generic = links[(site + "services.html", site + "pricing.html", "click here")]
    assert generic["position"] == "main"
    nav = links[(site, site + "services.html", "Services")]  # "About" appears in nav and footer; "Services" only in nav
    assert nav["position"] == "nav"
    footer = links[(site, site + "pricing.html", "Pricing")]
    assert footer["position"] == "footer"
    nofollow = links[(site + "blog/post-b.html", site + "pricing.html", "plans")]
    assert nofollow["nofollow"] is True
    image = links[(site + "blog/post-b.html", site + "services.html", "Retrospective facilitation service")]
    assert image["is_image"] is True


def test_crawl_resolves_base_href(site):
    data = crawl(site, max_pages=50, delay=0)
    targets = {l["target"] for l in data["links"] if l["source"] == site + "blog/post-a.html"}
    assert site + "blog/post-b.html" in targets
    assert site + "post-b.html" not in targets


def test_crawl_ignores_fragment_mailto_tel(site):
    data = crawl(site, max_pages=50, delay=0)
    about_links = [l for l in data["links"] if l["source"] == site + "about.html"]
    hrefs = {l["target"] for l in about_links}
    assert not any("#" in h or h.startswith("mailto") or h.startswith("tel") for h in hrefs)
    assert site + "about.html" not in {l["target"] for l in about_links if l["position"] == "main"}
    assert data["pages"][site + "about.html"]["external_links"] == 0


def test_crawl_status_checks_targets(site):
    data = crawl(site, max_pages=50, delay=0)
    assert by_target(data, "old-page.html")["final_status"] == 404
    moved = by_target(data, "moved.html")
    assert moved["status"] == 301
    assert moved["final_status"] == 200
    assert moved["final_url"] == site + "pricing.html"
    assert moved["chain"] == [site + "pricing.html"]
    blocked = by_target(data, "private/secret.html")
    assert blocked["checked"] == "blocked"
    pdf = by_target(data, "files/brochure.pdf")
    assert pdf["final_status"] == 200
    assert site + "files/brochure.pdf" not in data["pages"]
    assert site + "moved.html" not in data["pages"]


def test_crawl_cap_stops_pages_but_still_checks_targets(site):
    data = crawl(site, max_pages=3, delay=0)
    assert data["cap_reached"] is True
    assert data["pages_crawled"] == 3
    assert data["pages_discovered"] > 3
    for l in data["links"]:
        assert l["target"] in data["targets"] or l["target"] in data["pages"]


def test_crawl_without_sitemap_never_sees_the_orphan(site):
    data = crawl(site, max_pages=50, delay=0, use_sitemap=False)
    assert site + "blog/post-c.html" not in data["pages"]
    assert data["pages_crawled"] == 7


def test_crawl_start_url_failure(site):
    data = crawl(site + "nope.html", max_pages=5, delay=0)
    assert data["ok"] is False
    assert "404" in data["error"]


def test_main_writes_file_and_exit_codes(site, tmp_path, capsys):
    out = tmp_path / "crawl.json"
    assert main([site, "--max-pages", "50", "--delay", "0", "--out", str(out)]) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["source"] == "crawl_links.py" and data["schema"] == 1
    assert "Crawled 8 pages" in capsys.readouterr().out
    assert main([site + "nope.html", "--delay", "0", "--out", str(out)]) == 2


def test_js_render_warning_fires_only_below_threshold(monkeypatch, site):
    data = crawl(site, max_pages=2, delay=0, use_sitemap=False)
    assert not any("JavaScript" in w for w in data["warnings"])  # home has 6 links and 1 script tag
    monkeypatch.setattr(crawl_links, "JS_RENDER_MIN_LINKS", 100)
    data = crawl(site, max_pages=2, delay=0, use_sitemap=False)
    assert any("JavaScript" in w for w in data["warnings"])
