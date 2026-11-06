"""Crawl a website for the content audit and write crawl.json.

Seeds from robots.txt sitemaps and /sitemap.xml, then follows internal links until the page cap.
Records, per HTML page: title, meta description, H1, H2s, text excerpt, word count, dates,
schema types, links (body vs navigation), forms, booking embeds and call-to-action links.

Standard library only. Static HTML only: content rendered by JavaScript is not seen.

    python crawl_site.py https://example.com/ --run-dir content-audit-example.com-2026-01-31
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import sys
import time
import zlib
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib import robotparser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    assert_outside_skill, normalize_url, same_site, utf8_console, warn, write_json, read_json,
)

USER_AGENT = "Mozilla/5.0 (compatible; content-audit/1.0; +https://github.com/)"
SKIP_EXT = re.compile(
    r"\.(jpe?g|png|gif|svg|webp|avif|ico|css|js|mjs|json|xml|txt|zip|gz|rar|7z|mp4|mov|webm|mp3|wav|"
    r"woff2?|ttf|eot|otf|exe|dmg|msi|csv|xlsx?|docx?|pptx?)$", re.I)
DOC_EXT = re.compile(r"\.(pdf|docx?|pptx?|xlsx?)$", re.I)
NAV_TAGS = {"nav", "header", "footer", "aside"}
NAV_ROLES = {"navigation", "banner", "contentinfo", "complementary"}
NAV_TOKENS = {"nav", "navbar", "navigation", "menu", "megamenu", "footer", "header", "breadcrumb",
              "breadcrumbs", "cookie", "cookies", "sidebar", "topbar", "site-header", "site-footer"}
NEVER_NAV = {"html", "body", "main", "article", "head", "link", "meta", "script", "style", "form"}
CLASS_NAV_TAGS = {"div", "ul", "ol", "section", "span", "menu", "li"}
SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg", "iframe", "select", "option"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
        "track", "wbr"}
CTA_TEXT = re.compile(
    r"\b(contact|talk to|speak (to|with)|book|schedule|demo|quote|request|consult|get started|"
    r"sign ?up|subscribe|download|free trial|start (a |your )?trial|get in touch|let'?s talk|"
    r"register|reserve|apply now|join|enquir|inquir|call us|email us|get (the|your|a) )", re.I)
BOOKING_HOSTS = re.compile(
    r"(calendly\.com|meetings\.hubspot\.com|chilipiper\.com|savvycal\.com|cal\.com|"
    r"youcanbook\.me|acuityscheduling\.com|tidycal\.com|zcal\.co|hubspot\.com/meetings)", re.I)
FORM_EMBED = re.compile(
    r"(hbspt\.forms\.create|js\.hsforms\.net|hs-form|forms\.hsforms|marketo|mktoForm|pardot|"
    r"typeform\.com|jotform|formstack|gravityforms|wpforms|tally\.so|forms\.office\.com|"
    r"docs\.google\.com/forms|webflow-form|w-form|fluentform|ninja-forms|elementor-form)", re.I)


class PageParser(HTMLParser):
    """One pass over the HTML: metadata, headings, text, links, forms, regions."""

    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.stack: list[tuple[str, bool]] = []  # (tag, is_nav_region)
        self.title = ""
        self._in_title = False
        self.meta: dict[str, str] = {}
        self.canonical = ""
        self.lang = ""
        self.hreflang: list[str] = []
        self.h1: list[str] = []
        self.h2: list[str] = []
        self.h3_count = 0
        self._heading: str | None = None
        self._heading_buf: list[str] = []
        self.text_main: list[str] = []
        self.text_all: list[str] = []
        self._skip_depth = 0
        self._main_depth = 0
        self.has_main = False
        self.links: list[dict] = []
        self._link: dict | None = None
        self.forms: list[dict] = []
        self._form: dict | None = None
        self.iframes: list[str] = []
        self.jsonld: list[str] = []
        self._in_jsonld = False
        self._jsonld_buf: list[str] = []
        self.times: list[str] = []
        self.embed_hits = 0
        self._raw_script: list[str] = []
        self._in_script = False

    # region helpers
    def _in_nav(self) -> bool:
        return bool(self.stack) and self.stack[-1][1]

    @staticmethod
    def _is_nav(tag: str, attrs: dict) -> bool:
        if tag in NEVER_NAV:
            return False  # page-level wrappers often carry classes like "has-megamenu"
        if tag in NAV_TAGS:
            return True
        if (attrs.get("role") or "").lower() in NAV_ROLES:
            return True
        if tag not in CLASS_NAV_TAGS:
            return False
        tokens = set()
        for key in ("class", "id"):
            for tok in re.split(r"[\s_]+", (attrs.get(key) or "").lower()):
                if tok:
                    tokens.add(tok)
                    tokens.update(t for t in tok.split("-") if t)
        return bool(tokens & NAV_TOKENS)

    def handle_starttag(self, tag, attrs_list):
        attrs = {k.lower(): (v or "") for k, v in attrs_list}
        nav = self._in_nav() or self._is_nav(tag, attrs)
        if tag not in VOID:
            self.stack.append((tag, nav))
        if tag in SKIP_TEXT_TAGS:
            self._skip_depth += 1
        if tag == "html" and attrs.get("lang"):
            self.lang = attrs["lang"].lower()
        elif tag == "title" and not self.title:
            self._in_title = True
        elif tag == "meta":
            name = (attrs.get("name") or attrs.get("property") or attrs.get("itemprop") or "").lower()
            if name and "content" in attrs:
                self.meta.setdefault(name, attrs["content"])
        elif tag == "link":
            rel = (attrs.get("rel") or "").lower().split()
            if "canonical" in rel and attrs.get("href"):
                self.canonical = urljoin(self.base_url, attrs["href"])
            if "alternate" in rel and attrs.get("hreflang"):
                self.hreflang.append(attrs["hreflang"].lower())
        elif tag in ("main", "article") or (attrs.get("role") or "").lower() == "main":
            self._main_depth += 1
            self.has_main = True
        elif tag in ("h1", "h2", "h3"):
            if tag == "h3":
                self.h3_count += 1
            else:
                self._heading = tag
                self._heading_buf = []
        elif tag == "a" and attrs.get("href"):
            self._link = {"href": attrs["href"], "text": [], "nav": nav,
                          "rel": (attrs.get("rel") or "").lower(), "aria": attrs.get("aria-label", "")}
        elif tag == "form":
            self._form = {"email": False, "fields": 0, "action": attrs.get("action", ""), "nav": nav,
                          "search": "search" in (attrs.get("role", "") + attrs.get("class", "") +
                                                 attrs.get("action", "")).lower()}
        elif tag in ("input", "textarea", "select") and self._form is not None:
            itype = (attrs.get("type") or "text").lower()
            if itype not in ("hidden", "submit", "button"):
                self._form["fields"] += 1
            if itype == "email" or "email" in (attrs.get("name", "") + attrs.get("id", "")).lower():
                self._form["email"] = True
            if itype == "search":
                self._form["search"] = True
        elif tag == "iframe" and attrs.get("src"):
            self.iframes.append(attrs["src"])
        elif tag == "script":
            stype = (attrs.get("type") or "").lower()
            if stype == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_buf = []
            else:
                self._in_script = True
                if FORM_EMBED.search(attrs.get("src", "")):
                    self.embed_hits += 1
        elif tag == "time" and attrs.get("datetime"):
            self.times.append(attrs["datetime"])
        if tag in ("div", "section") and FORM_EMBED.search(attrs.get("class", "") + " " + attrs.get("id", "")):
            self.embed_hits += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2") and self._heading == tag:
            text = _clean(" ".join(self._heading_buf))
            if text:
                (self.h1 if tag == "h1" else self.h2).append(text)
            self._heading = None
        elif tag == "a" and self._link is not None:
            self._link["text"] = _clean(" ".join(self._link["text"])) or _clean(self._link["aria"])
            self.links.append(self._link)
            self._link = None
        elif tag == "form" and self._form is not None:
            self.forms.append(self._form)
            self._form = None
        elif tag == "script":
            if self._in_jsonld:
                self.jsonld.append("".join(self._jsonld_buf))
                self._in_jsonld = False
            self._in_script = False
        if tag in ("main", "article") and self._main_depth:
            self._main_depth -= 1
        if tag in SKIP_TEXT_TAGS and self._skip_depth:
            self._skip_depth -= 1
        # pop to the matching tag; tolerate unclosed children
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._in_title:
            self.title += data
            return
        if self._in_jsonld:
            self._jsonld_buf.append(data)
            return
        if self._in_script:
            if FORM_EMBED.search(data):
                self.embed_hits += 1
            return
        if self._skip_depth:
            return
        if self._heading:
            self._heading_buf.append(data)
        if self._link is not None:
            self._link["text"].append(data)
        if data.strip():
            self.text_all.append(data)
            if not self._in_nav() and (self._main_depth or not self.has_main):
                self.text_main.append(data)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _jsonld_info(blocks: list[str]) -> tuple[list[str], str, str]:
    types: list[str] = []
    published = modified = ""

    def walk(node):
        nonlocal published, modified
        if isinstance(node, dict):
            t = node.get("@type")
            for v in (t if isinstance(t, list) else [t]):
                if isinstance(v, str) and v not in types:
                    types.append(v)
            published = published or str(node.get("datePublished") or "")
            modified = modified or str(node.get("dateModified") or "")
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for raw in blocks:
        try:
            walk(json.loads(raw.strip()))
        except (ValueError, TypeError):
            continue
    return types, published, modified


def _date(value: str) -> str:
    m = re.search(r"(19|20)\d{2}-\d{2}-\d{2}", value or "")
    return m.group(0) if m else ""


def parse_page(html: str, url: str, host: str) -> dict:
    p = PageParser(url)
    try:
        p.feed(html)
        p.close()
    except Exception as exc:  # html.parser is lenient; this is a last resort
        warn(f"parse error on {url}: {exc}")
    types, ld_pub, ld_mod = _jsonld_info(p.jsonld)
    published = _date(ld_pub) or _date(p.meta.get("article:published_time", "")) or \
        _date(p.meta.get("datepublished", "")) or (_date(p.times[0]) if p.times else "")
    modified = _date(ld_mod) or _date(p.meta.get("article:modified_time", "")) or \
        _date(p.meta.get("og:updated_time", "")) or _date(p.meta.get("datemodified", ""))
    main_text = _clean(" ".join(p.text_main))
    if len(main_text.split()) < 40:  # pages without clear regions: fall back to everything
        main_text = _clean(" ".join(p.text_all))

    links, docs, cta, booking = [], [], [], 0
    seen = set()
    for link in p.links:
        href = link["href"].strip()
        if href.startswith(("#", "javascript:", "data:")):
            continue
        anchor = link["text"][:120]
        if href.startswith(("mailto:", "tel:")):
            if not link["nav"]:
                cta.append({"url": href.split("?")[0], "anchor": anchor, "kind": href.split(":")[0]})
            continue
        absolute = urljoin(url, href)
        parts = urlsplit(absolute)
        if parts.scheme not in ("http", "https"):
            continue
        if BOOKING_HOSTS.search(absolute):
            booking += 1
            if not link["nav"]:
                cta.append({"url": absolute, "anchor": anchor, "kind": "booking"})
            continue
        if not same_site(parts.hostname or "", host):
            continue
        if DOC_EXT.search(parts.path):
            docs.append({"url": normalize_url(absolute), "anchor": anchor})
            continue
        norm = normalize_url(absolute)
        key = (norm, link["nav"])
        if key in seen:
            continue
        seen.add(key)
        links.append({"url": norm, "anchor": anchor, "nav": link["nav"],
                      "nofollow": "nofollow" in link["rel"]})
        if anchor and CTA_TEXT.search(anchor):
            # kept with its region; finalize_regions() drops the ones that turn out to be template
            cta.append({"url": norm, "anchor": anchor, "kind": "link", "nav": link["nav"]})
    booking += sum(1 for s in p.iframes if BOOKING_HOSTS.search(s))
    embed_forms = p.embed_hits + sum(1 for s in p.iframes if FORM_EMBED.search(s))
    forms = [f for f in p.forms if not f["search"]]
    robots = (p.meta.get("robots", "") + " " + p.meta.get("googlebot", "")).lower()
    return {
        "title": _clean(p.title)[:300],
        "meta_description": _clean(p.meta.get("description", "") or p.meta.get("og:description", ""))[:500],
        "og_type": p.meta.get("og:type", ""),
        "canonical": normalize_url(p.canonical) if p.canonical else "",
        "noindex": "noindex" in robots,
        "lang": p.lang,
        "hreflang": sorted(set(p.hreflang)),
        "h1": p.h1[:3],
        "h2": p.h2[:25],
        "h3_count": p.h3_count,
        "word_count": len(main_text.split()),
        "excerpt": main_text[:2500],
        "published": published,
        "modified": modified,
        "schema_types": types[:15],
        "links": links,
        "documents": docs,
        "cta_links": cta[:60],
        "forms": [{"email": f["email"], "fields": f["fields"], "in_nav": f["nav"]} for f in forms],
        "form_embeds": embed_forms,
        "booking_embeds": booking,
    }


def finalize_regions(pages: list[dict]) -> dict:
    """Decide which links are site template (navigation, header, footer) and which are body links.

    Markup alone is not reliable: some themes put a 'menu' class on a page-wide wrapper, others
    build the footer from plain divs. A link (same URL and anchor) that repeats on many pages is
    template whatever the markup says; when the markup marks nearly every link on a page as
    navigation, it is ignored for that page and repetition decides alone.
    """
    html = [p for p in pages if p.get("is_html")]
    n = len(html)
    freq: dict[tuple[str, str], int] = {}
    for p in html:
        for key in {(lk["url"], lk["anchor"].lower()) for lk in p.get("links", [])}:
            freq[key] = freq.get(key, 0) + 1
    threshold = max(3, int(0.4 * n + 0.5))
    template = {k for k, c in freq.items() if c >= threshold} if n >= 5 else set()
    distrusted = 0
    for p in html:
        links = p.get("links", [])
        nav_share = sum(1 for lk in links if lk["nav"]) / len(links) if links else 0
        distrust = len(links) >= 10 and nav_share >= 0.95
        distrusted += distrust
        for lk in links:
            parser_nav = lk["nav"] and not distrust
            lk["nav"] = parser_nav or (lk["url"], lk["anchor"].lower()) in template
        kept = []
        for c in p.get("cta_links", []):
            if c.get("kind") == "link":
                is_nav = (c.get("nav") and not distrust) or (c["url"], c["anchor"].lower()) in template
                if is_nav:
                    continue
            c.pop("nav", None)
            kept.append(c)
        p["cta_links"] = kept[:40]
    return {"template_links": len(template), "pages_with_markup_ignored": distrusted}


class Fetcher:
    def __init__(self, timeout: float, delay: float):
        self.timeout = timeout
        self.delay = delay
        self._last = 0.0

    def get(self, url: str) -> tuple[int, str, str, bytes]:
        """Return (status, final_url, content_type, body). Status 0 means a network error."""
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        req = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate",
                                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.5"})
        for attempt in range(3):
            try:
                with urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read(8_000_000)
                    enc = (resp.headers.get("Content-Encoding") or "").lower()
                    if enc == "gzip" or body[:2] == b"\x1f\x8b":
                        try:
                            body = gzip.decompress(body)
                        except OSError:
                            pass
                    elif enc == "deflate":
                        try:
                            body = zlib.decompress(body)
                        except zlib.error:
                            body = zlib.decompress(body, -zlib.MAX_WBITS)
                    return resp.status, resp.geturl(), resp.headers.get("Content-Type", ""), body
            except HTTPError as exc:
                if exc.code in (429, 503) and attempt < 2:
                    time.sleep(2 + attempt * 3)
                    continue
                return exc.code, url, "", b""
            except (URLError, TimeoutError, ConnectionError, OSError) as exc:
                if attempt < 2:
                    time.sleep(1 + attempt)
                    continue
                warn(f"fetch failed {url}: {exc}")
                return 0, url, "", b""
        return 0, url, "", b""


def decode(body: bytes, content_type: str) -> str:
    m = re.search(r"charset=([\w\-]+)", content_type or "", re.I)
    candidates = [m.group(1)] if m else []
    head = body[:2048].decode("ascii", "ignore")
    m2 = re.search(r"<meta[^>]+charset=[\"']?([\w\-]+)", head, re.I)
    if m2:
        candidates.append(m2.group(1))
    candidates.append("utf-8")
    for enc in candidates:
        try:
            return body.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", "replace")


def sitemap_urls(fetcher: Fetcher, roots: list[str], host: str, limit: int = 50_000) -> list[str]:
    found: list[str] = []
    queue, seen = deque(roots), set()
    while queue and len(seen) < 200 and len(found) < limit:
        sm = queue.popleft()
        if sm in seen:
            continue
        seen.add(sm)
        status, _, _, body = fetcher.get(sm)
        if status != 200 or not body:
            continue
        try:
            root = ElementTree.parse(io.BytesIO(body)).getroot()
        except ElementTree.ParseError:
            continue
        tag = root.tag.split("}")[-1]
        locs = [el.text.strip() for el in root.iter() if el.tag.split("}")[-1] == "loc" and el.text]
        if tag == "sitemapindex":
            queue.extend(locs)
        else:
            for loc in locs:
                if same_site(urlsplit(loc).hostname or "", host):
                    found.append(loc)
    return found


def crawl(start_url: str, max_pages: int, delay: float, timeout: float, use_sitemap: bool,
          include_params: bool, exclude: list[str], seed_file: str | None, existing: dict | None,
          checkpoint=None) -> dict:
    start = normalize_url(start_url)
    host = urlsplit(start).hostname or ""
    fetcher = Fetcher(timeout, delay)
    warnings: list[str] = []
    excl = [re.compile(x) for x in exclude]

    status, final, ctype, body = fetcher.get(start)
    if status != 200 or "html" not in ctype.lower():
        print(f"error: start URL returned status {status} ({ctype or 'no content type'})", file=sys.stderr)
        sys.exit(2)
    final_host = urlsplit(final).hostname or host
    if not same_site(final_host, host):
        warnings.append(f"Start URL redirects to another host ({final_host}); crawling that host")
    host = final_host
    start = normalize_url(final)

    rp = robotparser.RobotFileParser()
    robots_url = f"{urlsplit(start).scheme}://{urlsplit(start).netloc}/robots.txt"
    sm_roots = []
    rs, _, _, rbody = fetcher.get(robots_url)
    if rs == 200:
        text = decode(rbody, "")
        rp.parse(text.splitlines())
        sm_roots = [line.split(":", 1)[1].strip() for line in text.splitlines()
                    if line.lower().startswith("sitemap:")]
    else:
        rp.parse([])
    base = f"{urlsplit(start).scheme}://{urlsplit(start).netloc}"
    sm_roots = sm_roots or [f"{base}/sitemap.xml", f"{base}/sitemap_index.xml"]

    seeds: list[str] = []
    if seed_file:
        seeds = [ln.strip() for ln in Path(seed_file).read_text(encoding="utf-8").splitlines() if ln.strip()]
    sitemap_set: set[str] = set()
    if use_sitemap and not seed_file:
        sm = sitemap_urls(fetcher, sm_roots, host)
        sitemap_set = {normalize_url(u, keep_query=include_params) for u in sm}
        if not sm:
            warnings.append("No sitemap found or it was empty; pages were discovered by following links only")
        seeds = sorted(sitemap_set)

    pages: dict[str, dict] = {}
    if existing:
        pages = {p["url"]: p for p in existing.get("pages", [])}
    queue = deque([(start, 0, "start")] + [(normalize_url(u, keep_query=include_params), 1, "sitemap" if not seed_file else "list") for u in seeds])
    queued = {q[0] for q in queue}
    if pages and not seed_file:  # resuming: links found on pages already fetched still need a visit
        for p in list(pages.values()):
            for link in p.get("links", []):
                if link["url"] not in queued and link["url"] not in pages:
                    queued.add(link["url"])
                    queue.append((link["url"], p.get("depth", 0) + 1, "link"))
    blocked, skipped_external, fetched_now = [], 0, 0
    cap_reached = False
    follow_links = not seed_file

    while queue:
        url, depth, source = queue.popleft()
        if url in pages:
            continue
        html_count = sum(1 for p in pages.values() if p.get("is_html"))
        if html_count >= max_pages:
            cap_reached = True
            break
        path = urlsplit(url).path
        if SKIP_EXT.search(path) or DOC_EXT.search(path) or any(r.search(url) for r in excl):
            continue
        if not rp.can_fetch(USER_AGENT, url):
            blocked.append(url)
            continue
        status, final, ctype, body = fetcher.get(url)
        fetched_now += 1
        record = {"url": url, "status": status, "final_url": normalize_url(final) if final else url,
                  "depth": depth, "source": source, "in_sitemap": url in sitemap_set, "is_html": False}
        if status == 200 and "html" in (ctype or "").lower():
            if not same_site(urlsplit(final).hostname or "", host):
                skipped_external += 1
                continue
            record["is_html"] = True
            record.update(parse_page(decode(body, ctype), final or url, host))
            if follow_links:
                for link in record["links"]:
                    lu = link["url"] if include_params else normalize_url(link["url"])
                    if lu not in queued and lu not in pages:
                        queued.add(lu)
                        queue.append((lu, depth + 1, "link"))
        pages[url] = record
        if fetched_now % 25 == 0:
            print(f"  crawled {sum(1 for p in pages.values() if p.get('is_html'))} HTML pages, queue {len(queue)}",
                  file=sys.stderr)
        if checkpoint and fetched_now % 50 == 0:
            # A partial crawl.json, so a run stopped by a timeout can continue with --resume.
            checkpoint({"meta": {"start_url": start, "host": host, "partial": True,
                                 "sitemap_urls": len(sitemap_set), "warnings": []},
                        "pages": list(pages.values())})

    html_pages = [p for p in pages.values() if p.get("is_html")]
    regions = finalize_regions(html_pages)
    if regions["pages_with_markup_ignored"]:
        warnings.append(f"On {regions['pages_with_markup_ignored']} pages the markup marked almost every link as "
                        "navigation; body links there were told apart by repetition across pages instead")
    if cap_reached:
        warnings.append(f"Page cap {max_pages} reached; {len(queue)} discovered URLs were not fetched")
    if html_pages:
        thin = sum(1 for p in html_pages if p.get("word_count", 0) < 50)
        start_rec = pages.get(start, {})
        body_links = sum(1 for lk in start_rec.get("links", []) if not lk["nav"])
        if thin / len(html_pages) > 0.5 or len(start_rec.get("links", [])) < 5:
            warnings.append("Most pages have very little text or the homepage has few links: the site may "
                            "render content with JavaScript, which this crawler does not run")
        if body_links == 0 and start_rec.get("links"):
            warnings.append("Every homepage link sits in a navigation region; body-link checks may be unreliable")
    langs = {}
    for p in html_pages:
        langs[p.get("lang") or "unknown"] = langs.get(p.get("lang") or "unknown", 0) + 1
    if len([k for k, v in langs.items() if v >= 5]) > 1:
        warnings.append(f"Several languages found ({', '.join(f'{k}: {v}' for k, v in sorted(langs.items()))}); "
                        "consider auditing one language at a time with --exclude")
    return {
        "meta": {
            "start_url": start, "host": host,
            "crawled_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "max_pages": max_pages, "cap_reached": cap_reached,
            "html_pages": len(html_pages), "urls_checked": len(pages),
            "sitemap_urls": len(sitemap_set), "seed_list": bool(seed_file),
            "blocked_by_robots": blocked[:200], "blocked_count": len(blocked),
            "languages": langs, "warnings": warnings,
        },
        "pages": list(pages.values()),
    }


def main(argv=None) -> int:
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("start_url")
    ap.add_argument("--run-dir", required=True, help="Run folder; crawl.json is written here")
    ap.add_argument("--max-pages", type=int, default=1000)
    ap.add_argument("--delay", type=float, default=0.3, help="Seconds between requests")
    ap.add_argument("--timeout", type=float, default=20)
    ap.add_argument("--no-sitemap", action="store_true")
    ap.add_argument("--include-params", action="store_true", help="Keep non-tracking query strings")
    ap.add_argument("--exclude", action="append", default=[], help="Regex; matching URLs are skipped (repeatable)")
    ap.add_argument("--urls", help="Crawl only the URLs in this file (one per line), no link following")
    ap.add_argument("--resume", action="store_true", help="Keep pages already in crawl.json")
    args = ap.parse_args(argv)

    run_dir = Path(args.run_dir)
    assert_outside_skill(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    out = run_dir / "crawl.json"
    existing = read_json(out) if args.resume and out.exists() else None
    if existing:
        print(f"Resuming: {sum(1 for p in existing.get('pages', []) if p.get('is_html'))} HTML pages already in crawl.json")
    data = crawl(args.start_url, args.max_pages, args.delay, args.timeout, not args.no_sitemap,
                 args.include_params, args.exclude, args.urls, existing,
                 checkpoint=lambda partial: write_json(out, partial))
    write_json(out, data)
    m = data["meta"]
    print(f"Crawled {m['html_pages']} HTML pages on {m['host']} ({m['urls_checked']} URLs checked, "
          f"{m['sitemap_urls']} in sitemap, {m['blocked_count']} blocked by robots.txt)")
    for w in m["warnings"]:
        print(f"warning: {w}")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
