import json


def load(run_dir, name):
    return json.loads((run_dir / name).read_text(encoding="utf-8"))


def by_path(crawl, path):
    return next(p for p in crawl["pages"] if p["url"].endswith(path))


def test_crawl_respects_robots_and_reads_sitemap(run_dir):
    c = load(run_dir, "crawl.json")
    assert c["meta"]["blocked_count"] == 1
    assert not any("/private/" in p["url"] for p in c["pages"] if p.get("is_html"))
    assert c["meta"]["sitemap_urls"] == 16
    assert by_path(c, "/about.html")["source"] == "link"  # not in the sitemap, found by a link


def test_crawl_separates_navigation_links_from_body_links(run_dir):
    page = by_path(load(run_dir, "crawl.json"), "/services/forecasting.html")
    body = [lk["url"] for lk in page["links"] if not lk["nav"]]
    nav = [lk["url"] for lk in page["links"] if lk["nav"]]
    assert not any(u.endswith("/contact.html") for u in body)
    assert any(u.endswith("/contact.html") for u in nav)


def test_crawl_detects_forms_ctas_dates_schema_and_keeps_title_out_of_text(run_dir):
    c = load(run_dir, "crawl.json")
    assert by_path(c, "/contact.html")["forms"][0]["email"] is True
    cta = by_path(c, "/services/data-platform.html")["cta_links"]
    assert any(x["anchor"] == "talk to an engineer" for x in cta)
    assert by_path(c, "/blog/what-is-a-data-platform.html")["published"] == "2025-03-04"
    assert not by_path(c, "/index.html")["excerpt"].startswith("Quillbridge |")
    assert "Service" in by_path(c, "/services/data-platform.html")["schema_types"]


def test_resume_continues_a_stopped_crawl(site, tmp_path):
    import crawl_site

    run = tmp_path / "run"
    assert crawl_site.main([site + "index.html", "--run-dir", str(run), "--delay", "0", "--max-pages", "6"]) == 0
    first = load(run, "crawl.json")
    assert first["meta"]["cap_reached"] and first["meta"]["html_pages"] == 6
    assert crawl_site.main([site + "index.html", "--run-dir", str(run), "--delay", "0", "--resume"]) == 0
    second = load(run, "crawl.json")
    assert second["meta"]["html_pages"] == 18  # same total as a full crawl
    assert any(p["url"].endswith("/about.html") for p in second["pages"])  # found only through links


def test_page_wide_menu_class_does_not_turn_every_link_into_navigation():
    from crawl_site import finalize_regions, parse_page

    pages = []
    for i in range(6):
        nav = "".join(f'<a href="/s{j}">Section {j}</a>' for j in range(10))
        html = (f'<html><body class="has-megamenu menu-open"><div class="site-wrapper menu">'
                f'<div>{nav}</div><p>Body text <a href="/post-{i}-next">read the next post {i}</a> '
                f'<a href="/contact">Book a call</a></p></div></body></html>')
        rec = {"url": f"https://x.example/p{i}", "is_html": True}
        rec.update(parse_page(html, rec["url"], "x.example"))
        pages.append(rec)
    assert all(lk["nav"] for lk in pages[0]["links"])  # the markup alone gets it wrong
    stats = finalize_regions(pages)
    body = [lk["url"] for lk in pages[0]["links"] if not lk["nav"]]
    assert body == ["https://x.example/post-0-next"]  # the repeated links are template
    assert stats["pages_with_markup_ignored"] == 6
    assert pages[0]["cta_links"] == []  # "Book a call" repeats on every page: template, not a body CTA


def test_prepare_excludes_non_content_and_batches_the_rest(run_dir):
    meta = load(run_dir, "pages.json")
    reasons = {p["path"]: p["excluded"] for p in meta["pages"]}
    assert reasons["/privacy.html"] == "legal"
    assert reasons["/careers.html"] == "careers"
    assert reasons["/blog/index.html"] == "listing"
    assert reasons["/blog/tag/data.html"] == "listing"
    assert reasons["/services/data-platform.html"] == ""
    content = [p for p in meta["pages"] if not p["excluded"]]
    assert len(content) == 14 and meta["batches"] == 1
    hints = {p["path"]: p["type_hint"] for p in content}
    assert hints["/contact.html"] == "contact-demo" and hints["/pricing.html"] == "pricing"


def test_site_profile_lists_navigation_and_offering_pages(run_dir):
    text = (run_dir / "site_profile.md").read_text(encoding="utf-8")
    assert "Forecasting →" in text
    assert "/services/data-platform.html | Data platform services" in text
