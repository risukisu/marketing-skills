"""URL normalization and HTML parsing in scripts/crawl_links.py."""
from __future__ import annotations

from crawl_links import PageParser, host_key, normalize_url

HOST = "www.example.com"


def test_host_key_ignores_www_port_and_case():
    assert host_key("WWW.Example.com:443") == "example.com"
    assert host_key("example.com") == "example.com"


def test_normalize_resolves_relative_and_strips_fragment_and_query():
    base = "https://www.example.com/blog/post.html"
    assert normalize_url("../about.html#team?x=1", base, HOST) == "https://www.example.com/about.html"
    assert normalize_url("/pricing.html?utm=1", base, HOST) == "https://www.example.com/pricing.html"
    assert normalize_url("/pricing.html?page=2", base, HOST, include_params=True) == "https://www.example.com/pricing.html?page=2"


def test_normalize_collapses_www_variants_onto_start_netloc():
    assert normalize_url("https://example.com/a", "https://www.example.com/", HOST) == "https://www.example.com/a"
    assert normalize_url("http://EXAMPLE.com/a", "https://www.example.com/", HOST) == "http://www.example.com/a"


def test_normalize_rejects_external_and_non_http():
    base = "https://www.example.com/"
    assert normalize_url("https://other.com/x", base, HOST) is None
    assert normalize_url("mailto:a@example.com", base, HOST) is None
    assert normalize_url("tel:+1000", base, HOST) is None
    assert normalize_url("javascript:void(0)", base, HOST) is None
    assert normalize_url("#top", base, HOST) is None
    assert normalize_url("", base, HOST) is None


def test_normalize_keeps_trailing_slash_as_served():
    assert normalize_url("/blog/", "https://www.example.com/", HOST) == "https://www.example.com/blog/"
    assert normalize_url("/blog", "https://www.example.com/", HOST) == "https://www.example.com/blog"
    assert normalize_url("https://www.example.com", "https://www.example.com/", HOST) == "https://www.example.com/"


HTML = """<!doctype html><html><head><title> My  Page </title><base href="/blog/">
<link rel="canonical" href="/blog/my-page.html"><meta name="robots" content="noindex, follow">
<script>var links = ['<a href="/js-only">'];</script></head>
<body>
<header><a href="/">Home</a></header>
<nav><a href="/about.html">About</a></nav>
<main><h1>Main <em>title</em></h1><h2>First</h2><p>Body text with <a href="post-b.html" rel="nofollow noopener">a relative link</a>.</p>
<h2>Second</h2><p><a href="/services.html"><img src="x.png" alt="Service image"></a> <a href="#top">top</a></p>
<svg><title>icon</title><a href="/svg-link">x</a></svg>
<aside><a href="/side">Side</a></aside></main>
<footer><a href="/pricing.html">Pricing</a></footer>
</body></html>"""


def parse(html: str) -> PageParser:
    p = PageParser()
    p.feed(html)
    p.close()
    return p


def test_parser_collects_metadata():
    p = parse(HTML)
    assert p.title == "My Page"
    assert p.h1 == "Main title"
    assert p.h2 == ["First", "Second"]
    assert p.canonical == "/blog/my-page.html"
    assert p.meta_robots == "noindex, follow"
    assert p.base_href == "/blog/"
    assert p.script_tags == 1
    assert p.words > 5


def test_parser_assigns_positions_and_flags():
    p = parse(HTML)
    by_href = {l["href"]: l for l in p.links}
    assert set(by_href) == {"/", "/about.html", "post-b.html", "/services.html", "#top", "/side", "/pricing.html"}
    assert by_href["/"]["position"] == "header"
    assert by_href["/about.html"]["position"] == "nav"
    assert by_href["post-b.html"]["position"] == "main"
    assert by_href["post-b.html"]["nofollow"] is True
    assert by_href["post-b.html"]["anchor"] == "a relative link"
    assert by_href["/services.html"]["is_image"] is True
    assert by_href["/services.html"]["anchor"] == "Service image"
    assert by_href["/side"]["position"] == "aside"
    assert by_href["/pricing.html"]["position"] == "footer"
    assert "/js-only" not in by_href and "/svg-link" not in by_href


def test_parser_links_outside_landmarks_are_body():
    p = parse('<html><body><p><a href="/x">X</a></p></body></html>')
    assert p.links[0]["position"] == "body"


def test_parser_tolerates_unclosed_anchor():
    p = parse('<html><body><main><a href="/a">A <a href="/b">B</a></main></body></html>')
    assert [l["href"] for l in p.links] == ["/a", "/b"]
