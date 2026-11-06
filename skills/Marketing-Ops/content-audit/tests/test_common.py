from common import normalize_url, parse_number, path_key


def test_normalize_url_drops_fragment_tracking_and_trailing_slash():
    assert normalize_url("HTTPS://Example.com:443/a//b/?utm_source=x#top") == "https://example.com/a/b"
    assert normalize_url("https://example.com/") == "https://example.com/"
    assert normalize_url("https://example.com/p?b=2&a=1&gclid=z", keep_query=True) == "https://example.com/p?a=1&b=2"


def test_path_key_joins_full_urls_paths_and_hostless_values():
    assert path_key("https://www.example.com/Blog/Post/?utm=1") == "/blog/post"
    assert path_key("/blog/post") == "/blog/post"
    assert path_key("www.example.com/blog/post") == "/blog/post"
    assert path_key("/blog/za%C5%BC%C3%B3%C5%82%C4%87") == "/blog/zażółć"
    assert path_key("(not set)") == ""
    assert path_key("https://example.com") == "/"


def test_parse_number_handles_export_formats():
    assert parse_number("1,234") == 1234
    assert parse_number("1 234") == 1234
    assert parse_number("12,5") == 12.5
    assert parse_number("PLN 2,340.50") == 2340.5
    assert abs(parse_number("1.33%") - 0.0133) < 1e-9
    assert parse_number("--") is None
    assert parse_number("") is None
