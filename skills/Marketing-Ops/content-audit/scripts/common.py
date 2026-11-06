"""Shared helpers for the content-audit scripts. Standard library only (Python 3.9+)."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

STAGES = ["attention", "interest", "desire", "action"]
STAGE_LABELS = {"attention": "Attention", "interest": "Interest", "desire": "Desire", "action": "Action"}
RESERVED_OFFERINGS = {
    "cross": "Cross-offering",
    "brand": "Company and brand",
    "none": "No offering",
}
ICP_FIT = ["icp", "adjacent", "off", "unclear"]
CONFIDENCE = ["high", "med", "low"]
CONTENT_TYPES = [
    "homepage", "service", "product", "solution", "industry", "pricing", "case-study",
    "testimonial", "comparison", "blog", "guide", "whitepaper-ebook", "webinar-event",
    "video-podcast", "research-report", "glossary", "docs", "tool-calculator", "landing",
    "contact-demo", "newsletter", "about-team", "news-pr", "careers", "partner", "other",
]

TRACKING_PARAMS = re.compile(r"^(utm_|gclid$|fbclid$|msclkid$|hsa_|_hs|mc_|ref$|source$)", re.I)


def utf8_console() -> None:
    """Make print() safe on Windows consoles with non-UTF-8 code pages."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def normalize_url(url: str, base_host: str | None = None, keep_query: bool = False) -> str:
    """Canonical form used for crawling and de-duplication.

    Lower-cases scheme and host, drops fragments, default ports and tracking parameters,
    collapses duplicate slashes, strips a trailing slash except on the root path.
    """
    url = url.strip()
    parts = urlsplit(url)
    scheme = (parts.scheme or "https").lower()
    host = (parts.hostname or base_host or "").lower()
    port = parts.port
    netloc = host
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/") or "/"
    query = ""
    if keep_query and parts.query:
        kept = [q for q in parts.query.split("&") if q and not TRACKING_PARAMS.match(q.split("=")[0])]
        query = "&".join(sorted(kept))
    return urlunsplit((scheme, netloc, path, query, ""))


def path_key(url: str) -> str:
    """Join key across crawl and exports: decoded, lower-cased path without query or slash.

    GA4 reports paths, GSC and HubSpot report full URLs; all of them meet on this key.
    The host is ignored on purpose (www and bare domain, http and https collapse together).
    """
    url = (url or "").strip()
    if not url or url.lower() in {"(not set)", "(other)", "not set", "--"}:
        return ""
    if url.startswith("/"):
        path = url
    elif "://" in url:
        path = urlsplit(url).path
    elif "/" in url and "." in url.split("/")[0]:
        # "www.example.com/path" with no scheme
        path = "/" + url.split("/", 1)[1]
    else:
        path = "/" + url
    path = path.split("?")[0].split("#")[0]
    path = unquote(path).lower()
    path = re.sub(r"/{2,}", "/", path)
    if len(path) > 1:
        path = path.rstrip("/")
    return path or "/"


def same_site(host_a: str, host_b: str) -> bool:
    strip = lambda h: (h or "").lower().removeprefix("www.")  # noqa: E731
    return strip(host_a) == strip(host_b)


def host_slug(host: str) -> str:
    return re.sub(r"[^a-z0-9.\-]", "-", host.lower().removeprefix("www."))


_NUM_CLEAN = re.compile(r"[^\d,.\-]")


def parse_number(value) -> float | None:
    """Parse numbers from analytics exports: '1,234', '1 234', '12.5%', 'PLN 1,234.00', '--'.

    A lone comma followed by one or two digits is read as a decimal comma ('12,5' -> 12.5);
    otherwise commas are thousands separators. Returns None for empty or dash values.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s or s in {"--", "-", "—", "n/a", "N/A", "(not set)"}:
        return None
    pct = s.endswith("%")
    s = _NUM_CLEAN.sub("", s.replace(" ", "").replace(" ", ""))
    if not s or s in {"-", ".", ","}:
        return None
    if "," in s and "." not in s and re.fullmatch(r"-?\d+,\d{1,2}", s):
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        n = float(s)
    except ValueError:
        return None
    return n / 100.0 if pct else n


def read_json(path: str | os.PathLike):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | os.PathLike, data) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def assert_outside_skill(run_dir: Path) -> None:
    """Refuse to write run output inside the skill folder (a checkout of a public repo)."""
    skill_dir = Path(__file__).resolve().parent.parent
    try:
        run_dir.resolve().relative_to(skill_dir)
    except ValueError:
        return
    print(f"error: run folder {run_dir} is inside the skill folder; run from your workspace", file=sys.stderr)
    sys.exit(2)
