#!/usr/bin/env python3
"""Convert a Screaming Frog export into the crawl.json that analyze_links.py reads.

    python scripts/import_crawl.py all_inlinks.csv [--pages internal_html.csv]
                                   [--start-url https://example.com/] [--out crawl.json] [--include-params]

all_inlinks.csv comes from Bulk Export > Links > All Inlinks; internal_html.csv from the
Internal tab filtered to HTML (both UTF-8, as Screaming Frog writes them). Without the pages
file, pages are derived from link sources and have no titles or headings, which weakens the
candidate shortlist; a warning says so. Column names are matched case-insensitively; a missing
column is reported by name and its field left empty. Redirect chains are not in the export, so
redirected targets carry their first status only.

Exit code 1 only when the inlinks file cannot be read. Standard library only, Python 3.9+.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crawl_links import normalize_url  # noqa: E402

# Screaming Frog's Link Position values -> this skill's positions. Unknown values become "body".
POSITION_MAP = {"navigation": "nav", "nav": "nav", "header": "header", "content": "main", "main": "main",
                "sidebar": "aside", "aside": "aside", "footer": "footer"}
# Link types that are links a reader can follow. CSS, JS, canonical, hreflang rows are not.
LINK_TYPES = {"hyperlink", "image"}
# Candidate header names per field, most common first.
INLINK_COLUMNS = {"type": ["Type"], "source": ["Source"], "target": ["Destination"], "anchor": ["Anchor", "Anchor Text"],
                  "alt": ["Alt Text"], "status": ["Status Code"], "follow": ["Follow"], "position": ["Link Position"]}
PAGE_COLUMNS = {"url": ["Address"], "content_type": ["Content Type"], "status": ["Status Code"], "title": ["Title 1"],
                "h1": ["H1-1"], "canonical": ["Canonical Link Element 1"], "meta_robots": ["Meta Robots 1"],
                "word_count": ["Word Count"], "depth": ["Crawl Depth"]}


def _read_csv(path) -> tuple:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [h.strip() for h in (reader.fieldnames or [])], list(reader)


def _resolve(headers: list, wanted: dict, label: str, warnings: list) -> dict:
    """Map field -> actual header. Missing fields are warned about by their first candidate name."""
    lower = {h.lower(): h for h in headers}
    found = {}
    for field, candidates in wanted.items():
        hit = next((lower[c.lower()] for c in candidates if c.lower() in lower), None)
        if hit is None:
            warnings.append(f"{label}: column '{candidates[0]}' not found; '{field}' left empty")
        found[field] = hit
    return found


def _get(row: dict, cols: dict, field: str) -> str:
    h = cols.get(field)
    return (row.get(h) or "").strip() if h else ""


def _int(value: str):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def import_export(inlinks_path, pages_path=None, start_url=None, include_params: bool = False) -> dict:
    warnings: list = []
    headers, rows = _read_csv(inlinks_path)
    cols = _resolve(headers, INLINK_COLUMNS, "all_inlinks", warnings)

    sources = [_get(r, cols, "source") for r in rows if _get(r, cols, "source")]
    if not sources:
        warnings.append("all_inlinks: no Source values; nothing to import")
    start = start_url or (min(sources, key=len) if sources else "https://example.invalid/")
    start_netloc = urllib.parse.urlsplit(start).netloc
    start = normalize_url(start, start, start_netloc, include_params) or start

    pages: dict = {}
    if pages_path:
        pheaders, page_rows = _read_csv(pages_path)
        pcols = _resolve(pheaders, PAGE_COLUMNS, "internal_html", warnings)
        h2_cols = sorted(h for h in pheaders if h.lower().startswith("h2-"))
        for r in page_rows:
            url = normalize_url(_get(r, pcols, "url"), start, start_netloc, include_params)
            status = _int(_get(r, pcols, "status"))
            ctype = _get(r, pcols, "content_type").lower() if pcols.get("content_type") else "text/html"
            if not url or (status or 600) >= 300 or "html" not in ctype:
                continue
            canonical = _get(r, pcols, "canonical")
            pages[url] = {"url": url, "final_url": url, "status": status, "title": _get(r, pcols, "title"),
                          "h1": _get(r, pcols, "h1"), "h2": [v for v in ((r.get(h) or "").strip() for h in h2_cols) if v],
                          "canonical": canonical, "meta_robots": _get(r, pcols, "meta_robots"),
                          "word_count": _int(_get(r, pcols, "word_count")) or 0, "depth": _int(_get(r, pcols, "depth")),
                          "found_via": "export", "external_links": 0, "script_tags": 0}
    else:
        warnings.append("No internal_html.csv given: pages derived from link sources, without titles or headings. "
                        "Export Internal > HTML and pass --pages for a better candidate shortlist.")

    links: list = []
    targets: dict = {}
    for r in rows:
        if _get(r, cols, "type").lower() not in LINK_TYPES:
            continue
        source = normalize_url(_get(r, cols, "source"), start, start_netloc, include_params)
        if not source:
            continue
        if source not in pages:
            if pages_path:
                continue  # source is not an HTML page per the export
            pages[source] = {"url": source, "final_url": source, "status": 200, "title": "", "h1": "", "h2": [],
                             "canonical": "", "meta_robots": "", "word_count": 0, "depth": None, "found_via": "export",
                             "external_links": 0, "script_tags": 0}
        raw_target = _get(r, cols, "target")
        target = normalize_url(raw_target, source, start_netloc, include_params)
        if not target:
            if raw_target:
                pages[source]["external_links"] += 1
            continue
        is_image = _get(r, cols, "type").lower() == "image"
        links.append({"source": source, "target": target,
                      "anchor": _get(r, cols, "alt") if is_image else _get(r, cols, "anchor"),
                      "position": POSITION_MAP.get(_get(r, cols, "position").lower(), "body"),
                      "nofollow": _get(r, cols, "follow").lower() == "false", "is_image": is_image})
        status = _int(_get(r, cols, "status"))
        if target not in targets:
            redirect = 300 <= (status or 0) < 400
            targets[target] = {"status": status, "final_status": status, "final_url": None if redirect else target,
                               "chain": [], "checked": "export", "error": None}
    if any(300 <= (t["status"] or 0) < 400 for t in targets.values()):
        warnings.append("Redirect targets come from the export without chains or final URLs; verify them live.")
    if pages_path:
        unexported = sorted(t for t, info in targets.items() if info["status"] == 200 and t not in pages)
        if unexported:
            warnings.append(f"{len(unexported)} link target(s) answer 200 but are not in internal_html.csv (non-HTML, "
                            f"or the export was filtered); they count as targets only: {', '.join(unexported[:10])}")

    return {"ok": True, "schema": 1, "source": "import_crawl.py",
            "crawled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "start_url": start, "host": start_netloc, "max_pages": None, "include_params": include_params,
            "cap_reached": False, "pages_discovered": len(set(pages) | set(targets)), "pages_crawled": len(pages),
            "blocked_prefixes": [], "sitemaps": [], "pages": pages, "links": links, "targets": targets,
            "warnings": warnings}


def _utf8_stdout() -> None:
    """Warnings may quote column names and URLs; legacy Windows consoles (cp1250, cp1252) cannot encode them all."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv=None) -> int:
    _utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inlinks", help="Screaming Frog all_inlinks.csv")
    ap.add_argument("--pages", help="Screaming Frog internal_html.csv")
    ap.add_argument("--start-url", help="homepage URL; default is the shortest Source in the export")
    ap.add_argument("--out", default="crawl.json")
    ap.add_argument("--include-params", action="store_true")
    args = ap.parse_args(argv)
    try:
        data = import_export(args.inlinks, args.pages, args.start_url, args.include_params)
    except OSError as e:
        print(f"Cannot read {args.inlinks}: {e}", file=sys.stderr)
        return 1
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print(f"Imported {data['pages_crawled']} pages, {len(data['links'])} internal links, "
          f"{len(data['targets'])} targets -> {args.out}")
    for w in data["warnings"]:
        print("warning:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
