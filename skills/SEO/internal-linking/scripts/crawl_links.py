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
