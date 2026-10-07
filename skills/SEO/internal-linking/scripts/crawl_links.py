#!/usr/bin/env python3
"""Crawl one site and record its internal links.

    python scripts/crawl_links.py https://example.com/ [--max-pages 500] [--delay 0.5]
                                  [--out crawl.json] [--include-params] [--no-sitemap]

Writes crawl.json (schema in references/crawl-data.md): every crawled page with its title,
headings, canonical and depth; every internal link with anchor text and position (nav, header,
main, aside, footer, body); the status of every internal link target, past the page cap too.
Pages listed only in the sitemap are crawled and marked depth null, which is how orphans are
found. Static HTML only: links that JavaScript renders are invisible; use import_crawl.py with a
Screaming Frog export for such sites.

Exit code 2 when the start URL cannot be fetched. Every other problem is recorded in the file
under warnings or targets and the crawl continues. Standard library only, Python 3.9+.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser

# Matches the /seo-audit crawl cap so both skills see the same site.
DEFAULT_MAX_PAGES = 500
# Half a second between requests is polite to small hosts and still crawls 500 pages in
# under five minutes.
DEFAULT_DELAY = 0.5
# Most pages answer in a few seconds; 15 s leaves room for slow shared hosting without
# stalling the crawl on one dead URL.
TIMEOUT = 15
# Names the crawler to site owners; some hosts block urllib's default agent string.
USER_AGENT = "internal-linking-skill/1.0 (+https://github.com/risukisu/marketing-skills)"
# Landmark elements that decide a link's position. A link under none of them is "body".
LANDMARKS = ("nav", "header", "main", "aside", "footer")
# Elements whose contents are neither text nor links a reader sees.
SKIP_ELEMENTS = ("script", "style", "noscript", "template", "svg")
# A start page with fewer links than this and at least one script tag is the usual sign of
# a JavaScript-rendered site.
JS_RENDER_MIN_LINKS = 3
# Schemes that can be crawled. Everything else (mailto, tel, javascript) is not a page.
CRAWLABLE_SCHEMES = ("http", "https")
# Sitemap <loc> entries.
LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)


def host_key(netloc: str) -> str:
    """Lowercase host without credentials, port, or a leading 'www.', so variants compare equal."""
    host = netloc.lower().rsplit("@", 1)[-1].split(":", 1)[0]
    return host[4:] if host.startswith("www.") else host


def normalize_url(href: str, base: str, start_netloc: str, include_params: bool = False):
    """Absolute, fragment-free URL on the start host, or None for anything that is not a page there.

    Resolves href against base, lowercases scheme and host, rewrites the start host's www and
    bare variants onto start_netloc, drops the fragment, drops the query unless include_params,
    and leaves the path as served (trailing slashes are not touched: a site that serves both
    /blog and /blog/ has a redirect worth reporting). Fragment-only hrefs resolve to the page
    itself and are rejected.
    """
    href = (href or "").strip()
    if not href or href.startswith("#"):
        return None
    absolute = urllib.parse.urljoin(base, href)
    parts = urllib.parse.urlsplit(absolute)
    if parts.scheme.lower() not in CRAWLABLE_SCHEMES:
        return None
    if host_key(parts.netloc) != host_key(start_netloc):
        return None
    path = parts.path or "/"
    query = parts.query if include_params else ""
    return urllib.parse.urlunsplit((parts.scheme.lower(), start_netloc.lower(), path, query, ""))


class PageParser(HTMLParser):
    """Collects a page's title, headings, canonical, meta robots, base href, word count, and links.

    Each link records href, anchor text (image alt for image links), the nearest landmark
    ancestor as position, nofollow, and is_image. Content inside script, style, noscript,
    template, and svg is ignored.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.h1 = ""
        self.h2: list[str] = []
        self.canonical = ""
        self.meta_robots = ""
        self.base_href = ""
        self.links: list[dict] = []
        self.words = 0
        self.script_tags = 0
        self._landmarks: list[str] = []
        self._skip_depth = 0
        self._text_target = None  # "title", "h1", or "h2" while inside one
        self._buffer: list[str] = []
        self._link = None
        self._link_text: list[str] = []

    def _flush_link(self) -> None:
        if self._link is not None:
            self._link["anchor"] = " ".join(" ".join(self._link_text).split())
            self.links.append(self._link)
            self._link = None
            self._link_text = []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag in SKIP_ELEMENTS:
            self._skip_depth += 1
            if tag == "script":
                self.script_tags += 1
            return
        if self._skip_depth:
            return
        if tag in LANDMARKS:
            self._landmarks.append(tag)
        elif tag == "base":
            if a.get("href") and not self.base_href:
                self.base_href = a["href"]
        elif tag == "link":
            if "canonical" in a.get("rel", "").lower().split():
                self.canonical = a.get("href", "")
        elif tag == "meta":
            if a.get("name", "").lower() == "robots":
                self.meta_robots = a.get("content", "")
        elif tag in ("title", "h1", "h2"):
            self._text_target = tag
            self._buffer = []
        elif tag == "a":
            self._flush_link()
            if a.get("href"):
                rel = a.get("rel", "").lower().split()
                self._link = {
                    "href": a["href"],
                    "position": self._landmarks[-1] if self._landmarks else "body",
                    "nofollow": "nofollow" in rel,
                    "is_image": False,
                }
                self._link_text = []
        elif tag == "img" and self._link is not None:
            self._link["is_image"] = True
            if a.get("alt"):
                self._link_text.append(a["alt"])

    def handle_endtag(self, tag):
        if tag in SKIP_ELEMENTS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag in LANDMARKS:
            while self._landmarks:  # pop through unclosed inner landmarks too
                if self._landmarks.pop() == tag:
                    break
        elif tag == self._text_target:
            text = " ".join("".join(self._buffer).split())
            if tag == "title":
                self.title = self.title or text
            elif tag == "h1":
                self.h1 = self.h1 or text
            else:
                self.h2.append(text)
            self._text_target = None
        elif tag == "a":
            self._flush_link()

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._text_target:
            self._buffer.append(data)
        if self._link is not None:
            self._link_text.append(data)
        self.words += len(data.split())

    def close(self):
        super().close()
        self._flush_link()


class _ChainRecorder(urllib.request.HTTPRedirectHandler):
    """Records every redirect hop as (status, url) so chains can be reported."""

    def __init__(self) -> None:
        super().__init__()
        self.hops: list = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.hops.append((code, newurl))
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url: str, method: str = "GET") -> dict:
    """Fetch url following redirects. Never raises.

    status is the first response code (301 for a redirect), final_status the last one, chain
    the redirect hops. body is bytes for GET (empty on HEAD or error). A HEAD that answers 405
    is retried as GET. A timeout is retried once, then recorded as error "timeout".
    """
    result = {"url": url, "status": None, "final_status": None, "final_url": url, "chain": [],
              "body": b"", "content_type": "", "error": None}
    for attempt in (1, 2):
        recorder = _ChainRecorder()
        opener = urllib.request.build_opener(recorder)
        req = urllib.request.Request(url, method=method, headers={
            "User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"})
        try:
            with opener.open(req, timeout=TIMEOUT) as resp:
                result["final_url"] = resp.geturl()
                result["content_type"] = resp.headers.get("Content-Type", "")
                result["chain"] = [u for _, u in recorder.hops]
                result["status"] = recorder.hops[0][0] if recorder.hops else resp.status
                result["final_status"] = resp.status
                if method == "GET":
                    result["body"] = resp.read()
                return result
        except urllib.error.HTTPError as e:
            result["status"] = recorder.hops[0][0] if recorder.hops else e.code
            result["final_status"] = e.code
            result["final_url"] = getattr(e, "url", None) or url
            result["chain"] = [u for _, u in recorder.hops]
            if e.code == 405 and method == "HEAD":
                return fetch(url, "GET")
            return result
        except (urllib.error.URLError, OSError, ValueError) as e:
            reason = getattr(e, "reason", e)
            timed_out = isinstance(reason, TimeoutError) or "timed out" in str(reason).lower()
            result["error"] = "timeout" if timed_out else str(reason)
            if not timed_out or attempt == 2:
                return result
    return result


def _decode(body: bytes, content_type: str) -> str:
    m = re.search(r"charset=([\w-]+)", content_type or "", re.IGNORECASE)
    try:
        return body.decode(m.group(1) if m else "utf-8", errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def disallow_prefixes(robots_text: str) -> list:
    """Disallow paths in the 'User-agent: *' group, for the report's limits section."""
    prefixes, applies = set(), False
    for raw in robots_text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            applies = value == "*"
        elif key == "disallow" and applies and value:
            prefixes.add(value)
    return sorted(prefixes)


def load_robots(start_url: str, warnings: list):
    """Fetch robots.txt. Returns (parser, sitemap_urls, blocked_prefixes). A missing file allows all."""
    rp = urllib.robotparser.RobotFileParser()
    robots_url = urllib.parse.urljoin(start_url, "/robots.txt")
    resp = fetch(robots_url)
    text = _decode(resp["body"], resp["content_type"]) if resp["final_status"] == 200 else ""
    if resp["error"] or resp["final_status"] != 200:
        rp.allow_all = True
    rp.parse(text.splitlines())
    if resp["error"]:
        warnings.append(f"robots.txt could not be fetched ({resp['error']}); crawling everything")
    sitemaps = [s for s in (rp.site_maps() or []) if s]
    return rp, sitemaps, disallow_prefixes(text)


def _pause(delay: float) -> None:
    if delay > 0:
        time.sleep(delay)


def load_sitemap_pages(sitemap_urls: list, start_netloc: str, include_params: bool, warnings: list, delay: float) -> list:
    """Page URLs from each sitemap, recursing one level into a sitemap index. Gzip handled."""
    pages: list = []
    seen: set = set()

    def read(url: str) -> str:
        resp = fetch(url)
        _pause(delay)
        if resp["error"] or (resp["final_status"] or 600) >= 400:
            warnings.append(f"sitemap {url} not readable ({resp['error'] or resp['final_status']})")
            return ""
        body = resp["body"]
        if body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return _decode(body, resp["content_type"])

    for sm in sitemap_urls:
        text = read(sm)
        children = LOC_RE.findall(text)
        if "<sitemapindex" in text.lower():
            locs = []
            for child in children:
                locs.extend(LOC_RE.findall(read(child)))
        else:
            locs = children
        for loc in locs:
            u = normalize_url(loc, sm, start_netloc, include_params)
            if u and u not in seen:
                seen.add(u)
                pages.append(u)
    return pages


def crawl(start_url: str, max_pages: int = DEFAULT_MAX_PAGES, delay: float = DEFAULT_DELAY,
          include_params: bool = False, use_sitemap: bool = True) -> dict:
    """Breadth-first crawl from start_url, then sitemap-only pages, then status checks of uncrawled targets."""
    warnings: list = []
    first = fetch(start_url)
    if first["error"] or (first["final_status"] or 600) >= 400 or "html" not in first["content_type"].lower():
        return {"ok": False, "start_url": start_url, "warnings": warnings,
                "error": first["error"] or f"HTTP {first['final_status']} ({first['content_type'] or 'no content type'})"}
    start_netloc = urllib.parse.urlsplit(first["final_url"]).netloc
    start = normalize_url(first["final_url"], first["final_url"], start_netloc, include_params)
    _pause(delay)
    robots, sitemap_urls, blocked = load_robots(start, warnings)
    _pause(delay)
    if use_sitemap and not sitemap_urls:
        sitemap_urls = [urllib.parse.urljoin(start, "/sitemap.xml")]
    sitemap_pages = load_sitemap_pages(sitemap_urls, start_netloc, include_params, warnings, delay) if use_sitemap else []

    pages: dict = {}
    links: list = []
    targets: dict = {}
    depth: dict = {start: 0}
    found_via: dict = {start: "start"}
    link_queue = deque([start])
    sitemap_queue = deque()
    for u in sitemap_pages:
        if u not in depth:
            depth[u] = None
            found_via[u] = "sitemap"
            sitemap_queue.append(u)
    pending = {start: first}
    cap_reached = False

    def blocked_record(url: str) -> dict:
        return {"status": None, "final_status": None, "final_url": url, "chain": [], "checked": "blocked", "error": None}

    while link_queue or sitemap_queue:
        url = link_queue.popleft() if link_queue else sitemap_queue.popleft()
        if url in pages or url in targets:
            continue
        if len(pages) >= max_pages:
            cap_reached = True
            break
        if not robots.can_fetch(USER_AGENT, url):
            targets[url] = blocked_record(url)
            continue
        resp = pending.pop(url, None)
        if resp is None:
            resp = fetch(url)
            _pause(delay)
        targets[url] = {"status": resp["status"], "final_status": resp["final_status"], "final_url": resp["final_url"],
                        "chain": resp["chain"], "checked": "GET", "error": resp["error"]}
        if resp["error"] or (resp["final_status"] or 600) >= 400 or "html" not in resp["content_type"].lower():
            continue
        final = normalize_url(resp["final_url"], resp["final_url"], start_netloc, include_params)
        if final != url:
            if final and final not in depth:
                depth[final] = depth[url]
                found_via[final] = found_via[url]
                link_queue.appendleft(final)
            continue
        parser = PageParser()
        parser.feed(_decode(resp["body"], resp["content_type"]))
        parser.close()
        base = urllib.parse.urljoin(resp["final_url"], parser.base_href) if parser.base_href else resp["final_url"]
        page = {"url": url, "final_url": resp["final_url"], "status": resp["final_status"], "title": parser.title,
                "h1": parser.h1, "h2": parser.h2, "canonical": parser.canonical, "meta_robots": parser.meta_robots,
                "word_count": parser.words, "depth": depth[url], "found_via": found_via[url],
                "external_links": 0, "script_tags": parser.script_tags}
        pages[url] = page
        d = depth[url]
        for l in parser.links:
            t = normalize_url(l["href"], base, start_netloc, include_params)
            if t is None:
                href = l["href"].strip()
                scheme = urllib.parse.urlsplit(urllib.parse.urljoin(base, href)).scheme.lower()
                if scheme in CRAWLABLE_SCHEMES and not href.startswith("#"):
                    page["external_links"] += 1  # another host; mailto/tel/javascript are not links to pages
                continue
            links.append({"source": url, "target": t, "anchor": l["anchor"], "position": l["position"],
                          "nofollow": l["nofollow"], "is_image": l["is_image"]})
            if t not in depth:
                depth[t] = None if d is None else d + 1
                found_via[t] = "link"
                link_queue.append(t)
            elif depth[t] is None and d is not None:
                depth[t] = d + 1
                if t not in pages and t not in targets:
                    link_queue.append(t)

    for t in sorted({l["target"] for l in links}):
        if t in targets or t in pages:
            continue
        if not robots.can_fetch(USER_AGENT, t):
            targets[t] = blocked_record(t)
            continue
        resp = fetch(t, "HEAD")
        _pause(delay)
        targets[t] = {"status": resp["status"], "final_status": resp["final_status"], "final_url": resp["final_url"],
                      "chain": resp["chain"], "checked": "HEAD", "error": resp["error"]}

    for u, p in pages.items():
        p["depth"] = depth.get(u)
    home_links = sum(1 for l in links if l["source"] == start)
    if home_links < JS_RENDER_MIN_LINKS and pages.get(start, {}).get("script_tags", 0) > 0:
        warnings.append("Few links on the start page but script tags present: the site may render links with "
                        "JavaScript. Use scripts/import_crawl.py with a Screaming Frog export instead.")
    if cap_reached:
        warnings.append(f"Page cap {max_pages} reached; {len(depth)} URLs discovered. Raise --max-pages for a full crawl.")

    return {"ok": True, "schema": 1, "source": "crawl_links.py",
            "crawled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "start_url": start, "host": start_netloc, "max_pages": max_pages, "include_params": include_params,
            "cap_reached": cap_reached, "pages_discovered": len(depth), "pages_crawled": len(pages),
            "blocked_prefixes": blocked, "sitemaps": sitemap_urls if use_sitemap else [],
            "pages": pages, "links": links, "targets": targets, "warnings": warnings}


def _utf8_stdout() -> None:
    """Warnings may quote page titles and URLs; legacy Windows consoles (cp1250, cp1252) cannot encode them all."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv=None) -> int:
    _utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("start_url")
    ap.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    ap.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    ap.add_argument("--out", default="crawl.json")
    ap.add_argument("--include-params", action="store_true", help="keep query strings as distinct URLs")
    ap.add_argument("--no-sitemap", action="store_true", help="do not seed pages from the sitemap")
    args = ap.parse_args(argv)
    data = crawl(args.start_url, args.max_pages, args.delay, args.include_params, not args.no_sitemap)
    if not data["ok"]:
        print(f"Cannot fetch {args.start_url}: {data['error']}", file=sys.stderr)
        return 2
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    broken = sum(1 for t in data["targets"].values() if (t["final_status"] or 0) >= 400)
    sitemap_only = sum(1 for p in data["pages"].values() if p["depth"] is None)
    print(f"Crawled {data['pages_crawled']} pages ({data['pages_discovered']} URLs discovered), "
          f"{len(data['links'])} internal links, {sitemap_only} sitemap-only pages, {broken} broken targets -> {args.out}")
    for w in data["warnings"]:
        print("warning:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
