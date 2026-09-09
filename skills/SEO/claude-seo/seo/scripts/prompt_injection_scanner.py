#!/usr/bin/env python3
"""
Prompt Injection Scanner for claude-seo
Scans fetched HTML for adversarial content before Claude processes it.

Detects hidden text injection, instruction injection patterns, delimiter/boundary
attacks, meta tag abuse, and encoding obfuscation. Returns structured threat
reports so Claude can treat all page content as untrusted data.
"""

import base64
import re
import unicodedata
from html.parser import HTMLParser
from typing import Optional

from bs4 import BeautifulSoup, Comment, Tag

# ---------------------------------------------------------------------------
# Compiled regex patterns (module-level for performance)
# ---------------------------------------------------------------------------

# Instruction injection patterns
_INSTRUCTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"ignore\s+(all\s+|your\s+)?(previous\s+|prior\s+|above\s+)?instructions", re.I), "ignore instructions"),
    (re.compile(r"you\s+are\s+now\b", re.I), "role reassignment (you are now)"),
    (re.compile(r"you\s+must\s+now\b", re.I), "directive override (you must now)"),
    (re.compile(r"from\s+now\s+on\b", re.I), "persistent override (from now on)"),
    (re.compile(r"(?:^|\s)system\s*:", re.I | re.M), "system role delimiter"),
    (re.compile(r"\[SYSTEM\]", re.I), "system role tag"),
    (re.compile(r"<<SYS>>", re.I), "Llama-style system tag"),
    (re.compile(r"<\|im_start\|>system", re.I), "ChatML system tag"),
    (re.compile(r"(?:^|\s)assistant\s*:", re.I | re.M), "assistant role delimiter"),
    (re.compile(r"(?:^|\s)human\s*:", re.I | re.M), "human role delimiter"),
    (re.compile(r"(?:^|\s)user\s*:", re.I | re.M), "user role delimiter"),
    (re.compile(r"do\s+not\s+follow\b", re.I), "do not follow directive"),
    (re.compile(r"\bdisregard\b", re.I), "disregard directive"),
    (re.compile(r"\boverride\b.{0,30}\binstructions?\b", re.I), "override instructions"),
    (re.compile(r"new\s+instructions?\b", re.I), "new instructions directive"),
    (re.compile(r"pretend\s+you\s+are\b", re.I), "role pretend"),
    (re.compile(r"act\s+as\s+if\b", re.I), "role act-as-if"),
    (re.compile(r"roleplay\s+as\b", re.I), "roleplay directive"),
    (re.compile(r"forget\s+everything\b", re.I), "context wipe (forget everything)"),
    (re.compile(r"reset\s+your\b", re.I), "context wipe (reset your)"),
    (re.compile(r"clear\s+your\s+context\b", re.I), "context wipe (clear your context)"),
    (re.compile(r"output\s+the\s+(system\s+|initial\s+)?prompt\b", re.I), "prompt exfiltration"),
    (re.compile(r"repeat\s+(the\s+|your\s+)?(system\s+|initial\s+)?prompt\b", re.I), "prompt exfiltration (repeat)"),
    (re.compile(r"you\s+have\s+been\s+jailbroken\b", re.I), "jailbreak claim"),
    (re.compile(r"\[INST\]", re.I), "Llama INST tag"),
    (re.compile(r"<\|endoftext\|>", re.I), "GPT end-of-text token"),
    (re.compile(r"<\|im_end\|>", re.I), "ChatML end tag"),
]

# Looks like an instruction (used for hidden-text heuristic)
_INSTRUCTION_LIKE = re.compile(
    r"(?:ignore|disregard|override|forget|you are now|system:|"
    r"new instructions|pretend you|act as if|do not follow|"
    r"output the prompt|repeat the prompt|jailbreak|roleplay as)",
    re.I,
)

# Delimiter / boundary attack patterns
_DELIMITER_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"```(?:system|prompt)", re.I), "code fence with system/prompt label"),
    (re.compile(r"(?:^|\n)-{10,}", re.M), "excessive dash separators (10+)"),
    (re.compile(r"(?:^|\n)={10,}", re.M), "excessive equals separators (10+)"),
]

# Base64 pattern in data attributes
_BASE64_DATA_ATTR = re.compile(r"data-[a-z0-9_-]+=\s*['\"]([A-Za-z0-9+/]{40,}={0,2})['\"]", re.I)

# Zero-width characters
_ZERO_WIDTH_CHARS = {
    "\u200B": "ZERO WIDTH SPACE",
    "\u200C": "ZERO WIDTH NON-JOINER",
    "\u200D": "ZERO WIDTH JOINER",
    "\uFEFF": "ZERO WIDTH NO-BREAK SPACE (BOM)",
}

_ZERO_WIDTH_RE = re.compile(r"[\u200B\u200C\u200D\uFEFF]")

# HTML entity sequences that spell out suspicious words
_ENTITY_SPELL_RE = re.compile(r"(&#\d{2,4};){5,}")

# Standard/benign meta names — anything outside this with instruction-like
# content in its value is suspicious.
_STANDARD_META_NAMES = frozenset({
    "viewport", "description", "keywords", "author", "robots", "googlebot",
    "generator", "theme-color", "msapplication-tilecolor", "msapplication-config",
    "apple-mobile-web-app-title", "application-name", "format-detection",
    "charset", "referrer", "color-scheme",
})

_STANDARD_META_PROPERTIES = frozenset({
    "og:title", "og:description", "og:image", "og:url", "og:type", "og:site_name",
    "og:locale", "og:image:width", "og:image:height", "og:image:alt",
    "twitter:card", "twitter:title", "twitter:description", "twitter:image",
    "twitter:site", "twitter:creator", "fb:app_id", "fb:pages",
    "article:published_time", "article:modified_time", "article:author",
    "article:section", "article:tag",
})

# Off-screen coordinate pattern
_OFFSCREEN_RE = re.compile(
    r"(?:left|top|right|bottom)\s*:\s*-\d{4,}px",
    re.I,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _snippet(text: str, max_len: int = 200) -> str:
    """Return the first max_len characters of text, cleaned up."""
    text = " ".join(text.split())  # collapse whitespace
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _get_style(element: Tag) -> str:
    """Get the combined inline style string for an element."""
    return (element.get("style") or "").lower()


def _is_hidden_by_style(style: str) -> Optional[str]:
    """Check if inline style hides the element. Returns reason or None."""
    if "display" in style and re.search(r"display\s*:\s*none", style):
        return "display:none"
    if "visibility" in style and re.search(r"visibility\s*:\s*hidden", style):
        return "visibility:hidden"
    if "opacity" in style and re.search(r"opacity\s*:\s*0(?:[;\s]|$)", style):
        return "opacity:0"
    if "font-size" in style and re.search(r"font-size\s*:\s*0(?:px|em|rem|%)?(?:[;\s]|$)", style):
        return "font-size:0"
    if _OFFSCREEN_RE.search(style):
        return "position:absolute + off-screen coords"
    # height:0 or width:0 with overflow:hidden
    if re.search(r"(?:height|width)\s*:\s*0(?:px)?", style) and re.search(r"overflow\s*:\s*hidden", style):
        return "height/width:0 + overflow:hidden"
    return None


def _colors_match(style: str) -> bool:
    """Check if color and background-color are the same in an inline style."""
    color_match = re.search(r"(?<![a-z-])color\s*:\s*([^;]+)", style)
    bg_match = re.search(r"background(?:-color)?\s*:\s*([^;]+)", style)
    if color_match and bg_match:
        c = color_match.group(1).strip().lower()
        b = bg_match.group(1).strip().lower()
        return c == b and c != ""
    return False


def _decode_html_entities(text: str) -> str:
    """Decode HTML numeric entities to characters."""
    import html
    return html.unescape(text)


def _check_base64_suspicious(encoded: str) -> Optional[str]:
    """Decode base64 and check for instruction-like content."""
    try:
        decoded = base64.b64decode(encoded).decode("utf-8", errors="ignore")
        if _INSTRUCTION_LIKE.search(decoded):
            return decoded
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Main scanner
# ---------------------------------------------------------------------------

def scan_for_injection(html: str, url: str) -> dict:
    """
    Scan fetched HTML for prompt injection threats.

    Args:
        html: Raw HTML string of the fetched page
        url: The URL the HTML was fetched from (for reporting)

    Returns:
        dict with keys:
            threats_found (bool): Whether any threats were detected
            threat_count (int): Number of threats found
            threats (list[dict]): Individual threat details
            sanitized_warnings (str): Human-readable summary for Claude
    """
    threats: list[dict] = []
    soup = BeautifulSoup(html, "html.parser")

    # -----------------------------------------------------------------------
    # 1. Hidden text injection
    # -----------------------------------------------------------------------
    for element in soup.find_all(True):  # all tags
        if not isinstance(element, Tag):
            continue

        text = element.get_text(strip=True)
        if not text or len(text) < 20:
            continue

        style = _get_style(element)
        hidden_reason = None

        # Inline style checks
        if style:
            hidden_reason = _is_hidden_by_style(style)
            if not hidden_reason and _colors_match(style):
                hidden_reason = "color matches background-color"

        # aria-hidden with suspiciously long text
        if not hidden_reason and element.get("aria-hidden") == "true" and len(text) > 100:
            hidden_reason = "aria-hidden='true' with long text"

        if hidden_reason and _INSTRUCTION_LIKE.search(text):
            threats.append({
                "type": "hidden_text",
                "severity": "high",
                "location": f"CSS hidden element ({hidden_reason})",
                "snippet": _snippet(text),
                "detail": (
                    f"Hidden element ({hidden_reason}) contains text that "
                    f"resembles prompt injection instructions."
                ),
            })

    # Check <style> blocks for rules that hide elements with instruction-like content
    for style_tag in soup.find_all("style"):
        style_text = style_tag.string or ""
        # Look for selectors that set display:none, visibility:hidden, etc.
        hiding_selectors = re.findall(
            r"([^{]+)\{[^}]*(?:display\s*:\s*none|visibility\s*:\s*hidden|"
            r"opacity\s*:\s*0(?:[;\s}])|font-size\s*:\s*0(?:px)?)[^}]*\}",
            style_text, re.I,
        )
        # We can't easily match CSS selectors to elements in a fast scan,
        # so we just flag if there are suspiciously many hiding rules AND
        # the page text contains instruction-like content.
        if len(hiding_selectors) > 5 and _INSTRUCTION_LIKE.search(html):
            threats.append({
                "type": "hidden_text",
                "severity": "medium",
                "location": "CSS style block (multiple hiding rules)",
                "snippet": _snippet("; ".join(s.strip() for s in hiding_selectors[:5])),
                "detail": (
                    f"Found {len(hiding_selectors)} CSS rules that hide elements, "
                    f"and the page contains instruction-like text. Manual review advised."
                ),
            })
            break  # one warning is enough

    # -----------------------------------------------------------------------
    # 2. Instruction injection patterns (scan full text + HTML)
    # -----------------------------------------------------------------------
    # Extract visible text for scanning
    page_text = soup.get_text(separator=" ")

    for pattern, description in _INSTRUCTION_PATTERNS:
        matches = list(pattern.finditer(page_text))
        for match in matches[:3]:  # cap at 3 reports per pattern
            start = max(0, match.start() - 40)
            end = min(len(page_text), match.end() + 40)
            context = page_text[start:end]
            threats.append({
                "type": "instruction_injection",
                "severity": "high",
                "location": "page text",
                "snippet": _snippet(context),
                "detail": f"Instruction injection pattern detected: {description}",
            })

    # Also scan raw HTML for patterns that might be in attributes/comments
    for pattern, description in _INSTRUCTION_PATTERNS:
        # Only scan raw HTML for patterns NOT already found in text
        matches_in_html = list(pattern.finditer(html))
        matches_in_text = list(pattern.finditer(page_text))
        html_only_count = len(matches_in_html) - len(matches_in_text)
        if html_only_count > 0:
            for match in matches_in_html[:2]:
                start = max(0, match.start() - 40)
                end = min(len(html), match.end() + 40)
                context = html[start:end]
                threats.append({
                    "type": "instruction_injection",
                    "severity": "high",
                    "location": "raw HTML (attribute/comment/tag)",
                    "snippet": _snippet(context),
                    "detail": f"Instruction injection in HTML source: {description}",
                })
                break  # one per pattern for HTML-only matches

    # -----------------------------------------------------------------------
    # 3. Delimiter / boundary attacks
    # -----------------------------------------------------------------------
    for pattern, description in _DELIMITER_PATTERNS:
        matches = list(pattern.finditer(html))
        if matches:
            match = matches[0]
            start = max(0, match.start() - 20)
            end = min(len(html), match.end() + 60)
            threats.append({
                "type": "delimiter_attack",
                "severity": "medium",
                "location": "HTML source",
                "snippet": _snippet(html[start:end]),
                "detail": f"Delimiter/boundary attack pattern: {description}",
            })

    # HTML comments containing instruction-like text
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment_text = str(comment).strip()
        if _INSTRUCTION_LIKE.search(comment_text):
            threats.append({
                "type": "delimiter_attack",
                "severity": "high",
                "location": "HTML comment",
                "snippet": _snippet(comment_text),
                "detail": "HTML comment contains instruction-like text.",
            })

    # Base64-encoded suspicious strings in data attributes
    for match in _BASE64_DATA_ATTR.finditer(html):
        decoded = _check_base64_suspicious(match.group(1))
        if decoded:
            threats.append({
                "type": "delimiter_attack",
                "severity": "high",
                "location": "data attribute (base64 encoded)",
                "snippet": _snippet(decoded),
                "detail": "Base64-encoded content in data attribute decodes to instruction-like text.",
            })

    # Zero-width characters and unicode homoglyphs
    zwc_matches = _ZERO_WIDTH_RE.findall(html)
    if len(zwc_matches) > 10:
        char_types = set()
        for c in zwc_matches:
            name = _ZERO_WIDTH_CHARS.get(c, f"U+{ord(c):04X}")
            char_types.add(name)
        threats.append({
            "type": "encoding_obfuscation",
            "severity": "medium" if len(zwc_matches) < 50 else "high",
            "location": "throughout page",
            "snippet": f"{len(zwc_matches)} zero-width characters found",
            "detail": (
                f"Excessive zero-width characters detected ({len(zwc_matches)} instances). "
                f"Types: {', '.join(sorted(char_types))}. "
                f"May be used to obfuscate injection text."
            ),
        })

    # -----------------------------------------------------------------------
    # 4. Meta tag abuse
    # -----------------------------------------------------------------------
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or "").lower()
        prop = (meta.get("property") or "").lower()
        content = meta.get("content") or ""

        # Skip standard SEO/OG meta tags
        if name in _STANDARD_META_NAMES or prop in _STANDARD_META_PROPERTIES:
            continue

        if content and _INSTRUCTION_LIKE.search(content):
            threats.append({
                "type": "instruction_injection",
                "severity": "high",
                "location": f"meta tag (name='{name}' property='{prop}')",
                "snippet": _snippet(content),
                "detail": "Meta tag contains instruction-like content outside standard SEO tags.",
            })

    # Check JSON-LD for non-standard fields with instructions
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        ld_text = script.string or ""
        if _INSTRUCTION_LIKE.search(ld_text):
            # Only flag if the instruction-like text is NOT in a standard field
            # Quick heuristic: check if it appears outside known keys
            threats.append({
                "type": "instruction_injection",
                "severity": "medium",
                "location": "JSON-LD structured data",
                "snippet": _snippet(ld_text[:300]),
                "detail": "JSON-LD script contains instruction-like text. Review for non-standard fields.",
            })

    # -----------------------------------------------------------------------
    # 5. Encoding obfuscation
    # -----------------------------------------------------------------------
    # HTML entity sequences that could spell out injection phrases
    entity_sequences = _ENTITY_SPELL_RE.findall(html)
    if entity_sequences:
        for seq in entity_sequences[:3]:
            decoded = _decode_html_entities(seq)
            if _INSTRUCTION_LIKE.search(decoded):
                threats.append({
                    "type": "encoding_obfuscation",
                    "severity": "high",
                    "location": "HTML entity sequence",
                    "snippet": _snippet(f"Encoded: {seq[:100]} -> Decoded: {decoded}"),
                    "detail": "HTML entities decode to instruction-like text. Likely obfuscated injection.",
                })

    # Unicode escape sequences in script tags
    for script in soup.find_all("script"):
        script_text = script.string or ""
        # Look for \\u00XX sequences that might spell injection text
        unicode_escapes = re.findall(r"(?:\\u[0-9a-fA-F]{4}){5,}", script_text)
        for ue in unicode_escapes[:2]:
            try:
                decoded = ue.encode().decode("unicode_escape")
                if _INSTRUCTION_LIKE.search(decoded):
                    threats.append({
                        "type": "encoding_obfuscation",
                        "severity": "high",
                        "location": "script tag (unicode escapes)",
                        "snippet": _snippet(f"Encoded: {ue[:100]} -> Decoded: {decoded}"),
                        "detail": "Unicode escape sequence in script decodes to instruction-like text.",
                    })
            except Exception:
                pass

    # -----------------------------------------------------------------------
    # Build summary
    # -----------------------------------------------------------------------
    # Deduplicate by (type, snippet) — keep highest severity
    seen: dict[tuple[str, str], dict] = {}
    severity_rank = {"high": 3, "medium": 2, "low": 1}
    for t in threats:
        key = (t["type"], t["snippet"][:80])
        existing = seen.get(key)
        if not existing or severity_rank.get(t["severity"], 0) > severity_rank.get(existing["severity"], 0):
            seen[key] = t
    threats = list(seen.values())

    # Sort: high first, then medium, then low
    threats.sort(key=lambda t: -severity_rank.get(t["severity"], 0))

    sanitized_warnings = _build_warnings(threats, url)

    return {
        "threats_found": len(threats) > 0,
        "threat_count": len(threats),
        "threats": threats,
        "sanitized_warnings": sanitized_warnings,
    }


def _build_warnings(threats: list[dict], url: str) -> str:
    """Build a human-readable warning summary."""
    if not threats:
        return ""

    high = [t for t in threats if t["severity"] == "high"]
    medium = [t for t in threats if t["severity"] == "medium"]
    low = [t for t in threats if t["severity"] == "low"]

    lines = []
    lines.append(f"Scanned: {url}")
    lines.append(f"Threats detected: {len(threats)} "
                 f"(high: {len(high)}, medium: {len(medium)}, low: {len(low)})")
    lines.append("")

    for i, t in enumerate(threats, 1):
        sev = t["severity"].upper()
        lines.append(f"  [{sev}] #{i}: {t['type']} — {t['detail']}")
        lines.append(f"         Location: {t['location']}")
        lines.append(f"         Snippet: {t['snippet'][:120]}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI interface for standalone testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python prompt_injection_scanner.py <html_file> [url]")
        print("  Reads HTML from file and scans for prompt injection threats.")
        sys.exit(1)

    html_path = sys.argv[1]
    test_url = sys.argv[2] if len(sys.argv) > 2 else "https://example.com"

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    result = scan_for_injection(html_content, test_url)
    print(json.dumps(result, indent=2))
