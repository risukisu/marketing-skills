"""Screaming Frog import in scripts/import_crawl.py."""
from __future__ import annotations

import json
from pathlib import Path

from import_crawl import import_export, main

FIX = Path(__file__).resolve().parent / "fixtures"
INLINKS = FIX / "sf_all_inlinks.csv"
PAGES = FIX / "sf_internal_html.csv"
NO_POS = FIX / "sf_all_inlinks_no_position.csv"
S = "https://www.example.com/"


def test_import_builds_pages_from_internal_html():
    data = import_export(INLINKS, PAGES)
    assert data["source"] == "import_crawl.py" and data["schema"] == 1
    assert data["start_url"] == S and data["host"] == "www.example.com"
    assert data["pages_crawled"] == 6  # the 404 row is a target, not a page
    page = data["pages"][S + "services.html"]
    assert page["title"] == "Services - Example Co"
    assert page["h2"] == ["Sprint planning", "Retrospectives"]
    assert page["depth"] == 1
    assert data["pages"][S + "blog/post-c.html"]["depth"] is None
    assert data["pages"][S + "about.html"]["canonical"] == S + "about.html"


def test_import_maps_links_positions_and_flags():
    data = import_export(INLINKS, PAGES)
    links = {(l["source"], l["target"]): l for l in data["links"] if l["anchor"] != "Pricing"}
    assert links[(S, S + "about.html")]["position"] == "nav"
    assert links[(S, S + "services.html")]["position"] == "main"
    assert links[(S + "blog/post-b.html", S + "pricing.html")]["nofollow"] is True
    image = links[(S + "blog/post-b.html", S + "services.html")]
    assert image["is_image"] is True and image["anchor"] == "Retrospective facilitation service"
    assert all(l["target"].startswith(S) for l in data["links"])  # external row dropped
    assert not any(l["target"].endswith("site.css") for l in data["links"])  # CSS row dropped
    assert data["pages"][S + "about.html"]["external_links"] == 1


def test_import_targets_carry_status_without_chains():
    data = import_export(INLINKS, PAGES)
    assert data["targets"][S + "old-page.html"]["final_status"] == 404
    moved = data["targets"][S + "moved.html"]
    assert moved["status"] == 301 and moved["chain"] == [] and moved["checked"] == "export"
    assert any("redirect" in w.lower() for w in data["warnings"])


def test_import_without_pages_file_warns_and_derives_pages():
    data = import_export(INLINKS)
    assert data["pages_crawled"] == 5  # every distinct Source with an internal link
    assert data["pages"][S]["title"] == ""
    assert any("internal_html" in w for w in data["warnings"])


def test_import_missing_column_warns_by_name():
    data = import_export(NO_POS)
    assert any("Link Position" in w for w in data["warnings"])
    assert {l["position"] for l in data["links"]} == {"body"}


def test_main_writes_file(tmp_path):
    out = tmp_path / "crawl.json"
    assert main([str(INLINKS), "--pages", str(PAGES), "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["pages_crawled"] == 6
    assert main([str(tmp_path / "missing.csv"), "--out", str(out)]) == 1


def test_import_warns_about_200_targets_missing_from_pages_export():
    data = import_export(INLINKS, PAGES)
    assert any("not in internal_html" in w and "post-a.html" in w for w in data["warnings"])
    assert import_export(INLINKS)["warnings"] and not any("not in internal_html" in w for w in import_export(INLINKS)["warnings"])


def test_import_redirect_targets_have_unknown_final_url():
    data = import_export(INLINKS, PAGES)
    assert data["targets"][S + "moved.html"]["final_url"] is None
    assert data["targets"][S + "old-page.html"]["final_url"] == S + "old-page.html"
