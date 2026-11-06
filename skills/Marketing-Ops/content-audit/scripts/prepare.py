"""Turn crawl.json into the content universe, a site profile and classification batches.

Writes into the run folder:
  pages.json        every crawled HTML page with an id, a page-type hint, lead-capture signals,
                    and either an exclusion reason or a batch number
  site_profile.md   the evidence the offering map is derived from (homepage, navigation,
                    service-type pages, URL sections)
  batches/batch_NN.json   pages for the classification subagents, ~50 per file

    python prepare.py --run-dir content-audit-example.com-2026-01-31 [--batch-size 50]
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import assert_outside_skill, path_key, read_json, utf8_console, write_json  # noqa: E402

# Order matters: the first match wins.
EXCLUDE_RULES = [
    ("legal", re.compile(r"/(privacy|cookie|cookies|terms|legal|gdpr|imprint|impressum|disclaimer|"
                         r"accessibility|security-policy|dpa|sla|modern-slavery)([\-/.]|$)")),
    ("post-conversion", re.compile(r"/(thank-?you|thanks|confirmation|success|submitted|"
                                   r"unsubscribe|preferences|subscription-center)([\-/.]|$)")),
    ("utility", re.compile(r"/(login|log-in|signin|sign-in|account|cart|checkout|search|404|"
                           r"password|reset|portal|admin|wp-admin|feed|rss)([\-/.]|$)")),
    ("listing", re.compile(r"/(tag|tags|category|categories|author|authors|topic|topics|archive|"
                           r"archives)/|/page/\d+$|[?&]page=\d+|"
                           r"^/(blog|blogs|news|insights|articles|resources|posts|stories)(/index(\.html?|\.php)?)?/?$")),
    ("careers", re.compile(r"/(careers?|jobs?|join-us|vacanc(y|ies)|open-positions|work-with-us)([\-/.]|$)")),
]
TYPE_RULES = [
    ("contact-demo", re.compile(r"/(contact|contact-us|demo|request-a-demo|book|book-a-call|schedule|"
                                r"talk-to|get-in-touch|quote|get-a-quote|consultation|lets-talk)([\-/.]|$)")),
    ("pricing", re.compile(r"/(pricing|plans|price|packages)([\-/.]|$)")),
    ("case-study", re.compile(r"/(case-stud(y|ies)|customers?|success-stor(y|ies)|client-stor(y|ies)|"
                              r"clients|portfolio|work|projects)([/.]|$)")),
    ("comparison", re.compile(r"(-vs-|-versus-|/compare|/comparison|/alternatives?)")),
    ("webinar-event", re.compile(r"/(webinars?|events?|conference|summit|meetups?|workshops?)([/.]|$)")),
    ("whitepaper-ebook", re.compile(r"/(ebooks?|e-books?|whitepapers?|white-papers?|reports?|"
                                    r"downloads?|guides?/download)([/.]|$)")),
    ("glossary", re.compile(r"/(glossary|dictionary|definitions?|what-is)([/.]|$)")),
    ("docs", re.compile(r"/(docs|documentation|help|support|knowledge-base|kb|faq|api)([/.]|$)")),
    ("video-podcast", re.compile(r"/(videos?|podcasts?|episodes?)([/.]|$)")),
    ("newsletter", re.compile(r"/(newsletter|subscribe)([/.]|$)")),
    ("news-pr", re.compile(r"/(news|press|press-releases?|media|newsroom|announcements?)([/.]|$)")),
    ("about-team", re.compile(r"/(about|about-us|team|our-team|company|leadership|who-we-are|mission|"
                              r"values|history)([/.]|$)")),
    ("partner", re.compile(r"/(partners?|partnerships?|integrations?)([/.]|$)")),
    ("industry", re.compile(r"/(industr(y|ies)|sectors?|verticals?)([/.]|$)")),
    ("service", re.compile(r"/(services?|solutions?|offerings?|capabilities|what-we-do|expertise|"
                           r"consulting|products?|platform|features?)([/.]|$)")),
    ("guide", re.compile(r"/(guides?|resources?|learn|academy|playbooks?|templates?|tools?)([/.]|$)")),
    ("blog", re.compile(r"/(blog|blogs|post|posts|articles?|insights?|stories|journal|perspectives?)([/.]|$)")),
]
OFFERING_SECTIONS = re.compile(r"^/(services?|solutions?|products?|platform|offerings?|capabilities|"
                               r"what-we-do|expertise|industr(y|ies)|use-cases?|features?)([/.]|$)")


def exclusion(path: str) -> str:
    for reason, rx in EXCLUDE_RULES:
        if rx.search(path):
            return reason
    return ""


def type_hint(page: dict) -> str:
    path = urlsplit(page["url"]).path.lower() or "/"
    if path == "/":
        return "homepage"
    for name, rx in TYPE_RULES:
        if rx.search(path):
            return name
    types = {t.lower() for t in page.get("schema_types", [])}
    if types & {"blogposting", "article", "newsarticle", "techarticle"} or page.get("og_type") == "article":
        return "blog"
    if types & {"service", "product", "softwareapplication"}:
        return "service"
    if types & {"event"}:
        return "webinar-event"
    return "other"


def lead_capture(page: dict) -> dict:
    forms = [f for f in page.get("forms", []) if not f.get("in_nav")]
    return {
        "email_form": any(f.get("email") for f in forms),
        "form_embed": page.get("form_embeds", 0) > 0,
        "booking": page.get("booking_embeds", 0) > 0,
        "cta_links": len(page.get("cta_links", [])),
    }


def build(run_dir: Path, batch_size: int) -> dict:
    crawl = read_json(run_dir / "crawl.json")
    host = crawl["meta"]["host"]
    html = [p for p in crawl["pages"] if p.get("is_html") and p.get("status") == 200]

    # De-duplicate: one record per final URL; canonicals pointing elsewhere are excluded.
    by_final: dict[str, dict] = {}
    for p in sorted(html, key=lambda r: (r["url"] != r.get("final_url"), r["url"])):
        by_final.setdefault(p.get("final_url") or p["url"], p)
    keys_present = {path_key(u) for u in by_final}

    pages = []
    for i, (final, p) in enumerate(sorted(by_final.items()), start=1):
        path = urlsplit(final).path.lower() or "/"
        reason = exclusion(path)
        canon = p.get("canonical") or ""
        if not reason and canon and path_key(canon) != path_key(final) and path_key(canon) in keys_present:
            reason = "canonicalised"
        if not reason and p.get("word_count", 0) < 30 and not p.get("h1") and not p.get("title"):
            reason = "empty"
        pages.append({
            "id": f"p{i:04d}", "url": final, "path": path_key(final), "status": p["status"],
            "title": p.get("title", ""), "h1": (p.get("h1") or [""])[0], "meta_description": p.get("meta_description", ""),
            "type_hint": type_hint(p), "word_count": p.get("word_count", 0),
            "published": p.get("published", ""), "modified": p.get("modified", ""),
            "noindex": p.get("noindex", False), "canonical": canon, "lang": p.get("lang", ""),
            "in_sitemap": p.get("in_sitemap", False), "depth": p.get("depth", 0),
            "lead_capture": lead_capture(p), "documents": len(p.get("documents", [])),
            "excluded": reason, "batch": None,
        })

    content = [p for p in pages if not p["excluded"]]
    # Keep sections together so one agent sees related pages side by side.
    content.sort(key=lambda p: (p["path"].split("/")[1] if p["path"].count("/") else "", p["path"]))
    batches_dir = run_dir / "batches"
    batches_dir.mkdir(exist_ok=True)
    (run_dir / "labels").mkdir(exist_ok=True)  # where the classification subagents write
    # Older batch files beyond the new count are left alone: pages.json records how many are live,
    # and check_labels.py validates every label file against the live batch it belongs to.
    crawl_by_url = {p.get("final_url") or p["url"]: p for p in html}
    n_batches = 0
    for b in range(0, len(content), batch_size):
        chunk = content[b:b + batch_size]
        rows = []
        for p in chunk:
            p["batch"] = n_batches
            src = crawl_by_url.get(p["url"], {})
            rows.append({
                "id": p["id"], "url": p["url"], "type_hint": p["type_hint"], "title": p["title"],
                "h1": p["h1"], "meta_description": p["meta_description"], "h2": src.get("h2", [])[:10],
                "excerpt": src.get("excerpt", "")[:1200], "word_count": p["word_count"],
                "lead_capture": p["lead_capture"],
                "body_link_targets": [lk["url"] for lk in src.get("links", []) if not lk["nav"]][:15],
            })
        write_json(batches_dir / f"batch_{n_batches:02d}.json", rows)
        n_batches += 1

    write_json(run_dir / "pages.json", {"host": host, "batch_size": batch_size, "batches": n_batches,
                                        "pages": pages})
    write_site_profile(run_dir, crawl, pages)
    return {"pages": len(pages), "content": len(content), "batches": n_batches,
            "excluded": Counter(p["excluded"] for p in pages if p["excluded"])}


def write_site_profile(run_dir: Path, crawl: dict, pages: list[dict]) -> None:
    host = crawl["meta"]["host"]
    raw = {p.get("final_url") or p["url"]: p for p in crawl["pages"] if p.get("is_html")}
    home = raw.get(crawl["meta"]["start_url"]) or next(iter(raw.values()), {})
    lines = [f"# Site profile: {host}", "",
             "Evidence for the offering map. Generated by prepare.py from crawl.json; derive offerings "
             "from this file, then open individual pages only where it is not enough.", ""]
    lines += ["## Homepage", "", f"- URL: {home.get('url', '')}", f"- Title: {home.get('title', '')}",
              f"- Meta description: {home.get('meta_description', '')}",
              f"- H1: {' | '.join(home.get('h1', []))}", f"- H2s: {' | '.join(home.get('h2', [])[:15])}", "",
              "Text excerpt:", "", "> " + (home.get("excerpt", "")[:1800] or "(no text extracted)"), ""]

    nav: dict[str, str] = {}
    for lk in home.get("links", []):
        if lk["nav"] and lk["anchor"] and lk["url"] not in nav.values():
            nav.setdefault(lk["anchor"][:60], lk["url"])
    lines += ["## Navigation links on the homepage", ""]
    lines += [f"- {a} → {u}" for a, u in list(nav.items())[:80]] or ["- (none detected)"]
    lines.append("")

    candidates = [p for p in pages if not p["excluded"] and (
        p["type_hint"] in {"service", "industry", "pricing", "product", "solution"} or OFFERING_SECTIONS.search(p["path"]))]
    candidates.sort(key=lambda p: (p["depth"], p["path"]))
    lines += [f"## Offering-type pages ({len(candidates)}; first 60 shown)", ""]
    for p in candidates[:60]:
        lines.append(f"- {p['path']} | {p['title']} | H1: {p['h1']} | {p['meta_description'][:200]}")
    if not candidates:
        lines.append("- (no /services, /solutions, /products-style pages found: read the navigation and homepage)")
    lines.append("")

    about = next((raw.get(p["url"]) for p in pages if p["type_hint"] == "about-team"), None)
    if about:
        lines += ["## About page excerpt", "", f"- URL: {about['url']}", "",
                  "> " + about.get("excerpt", "")[:1200], ""]

    sections = Counter((p["path"].split("/")[1] or "/") if p["path"] != "/" else "/" for p in pages if not p["excluded"])
    lines += ["## URL sections (content pages)", "", "| Section | Pages |", "|---|---:|"]
    lines += [f"| /{s} | {n} |" for s, n in sections.most_common(30)]
    hints = Counter(p["type_hint"] for p in pages if not p["excluded"])
    lines += ["", "## Page-type hints (from URL patterns and schema)", "", "| Hint | Pages |", "|---|---:|"]
    lines += [f"| {h} | {n} |" for h, n in hints.most_common()]
    excluded = Counter(p["excluded"] for p in pages if p["excluded"])
    if excluded:
        lines += ["", "## Excluded from the journey analysis", "", "| Reason | Pages |", "|---|---:|"]
        lines += [f"| {r} | {n} |" for r, n in excluded.most_common()]
    (run_dir / "site_profile.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--batch-size", type=int, default=50)
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    assert_outside_skill(run_dir)
    if not (run_dir / "crawl.json").exists():
        print("error: crawl.json not found; run crawl_site.py first", file=sys.stderr)
        return 2
    s = build(run_dir, args.batch_size)
    print(f"{s['pages']} pages; {s['content']} content pages in {s['batches']} batches of up to {args.batch_size}")
    for reason, n in s["excluded"].most_common():
        print(f"  excluded {n}: {reason}")
    print(f"Wrote {run_dir / 'pages.json'}, {run_dir / 'site_profile.md'}, {run_dir / 'batches'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
