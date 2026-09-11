#!/usr/bin/env bash
# fetch.sh — fetch one URL, emit labeled plain text.
# Floor: bash, curl, sed, grep, awk, tr. No jq, no python, no node.
# Never aborts a scan: non-200 responses, transport failures and refused URLs all
# print ERROR and exit 0.
#
# Modes:
#   fetch.sh <url> [max_text_chars]   fetch one URL and emit URL/STATUS/TITLE/META/H1/
#                                     HEADINGS/LINKS/TEXT (or URL/STATUS/ERROR).
#   fetch.sh --same-host <host>       filter absolute URLs on stdin, keeping only <host>
#                                     and its subdomains. discover.sh calls this so the
#                                     same-host rule lives in exactly one place.
#
# Environment:
#   FETCH_UA       User-Agent (default: a current desktop Chrome string).
#   FETCH_TIMEOUT  curl --max-time, seconds (default 25).
#   FETCH_LOCALE   Accept-Language value (default en-US). SKILL.md sets this from
#                  competitor-intel/config.json's `locale` field.
#   CI_BASE_URL    test hook: treat this value as the document's own URL (for the
#                  same-host check and relative-href resolution) while still reading
#                  the body from the <url> argument. No effect unless set.
#   CI_ALLOW_FILE  test hook: set to 1 to permit file:// reads. Refused otherwise.
set -uo pipefail

UA="${FETCH_UA:-Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36}"
TIMEOUT="${FETCH_TIMEOUT:-25}"
LOCALE="${FETCH_LOCALE:-en-US}"

# Shared awk source: same_host(url, host) — host-component comparison, not a substring
# test. A substring test keeps "https://notexample.com/evil" and
# "https://cdn.other.net/?u=example.com" as same-host, and both then land in the
# snapshot as that competitor's pages. `host` must already be lowercased and
# www-stripped; `url` is compared case-insensitively.
SAME_HOST_FN='
function host_of(u,   x) {
  x = tolower(u)
  sub(/^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//, "", x)
  sub(/[\/?#].*$/, "", x)
  sub(/^[^@]*@/, "", x)
  sub(/:[0-9]*$/, "", x)
  sub(/^www\./, "", x)
  return x
}
function same_host(u, h,   x, s) {
  if (h == "") return 0
  x = host_of(u)
  if (x == "") return 0
  if (x == h) return 1
  s = "." h
  return (length(x) > length(s) && substr(x, length(x) - length(s) + 1) == s)
}
'

if [ "${1:-}" = "--same-host" ]; then
  [ $# -ge 2 ] || { echo "usage: fetch.sh --same-host <host>" >&2; exit 2; }
  awk -v h="$(printf '%s' "$2" | tr 'A-Z' 'a-z' | sed -e 's|^www\.||')" \
      "$SAME_HOST_FN"'{ if (same_host($0, h)) print }'
  exit 0
fi

[ $# -ge 1 ] || { echo "usage: fetch.sh <url> [max_text_chars]" >&2; exit 2; }
url="$1"
max_text="${2:-3000}"

# The document's own URL: the source of the host for the same-host check and of the
# base directory for resolving relative hrefs.
doc_url="${CI_BASE_URL:-$url}"

refuse() { echo "URL: $url"; echo "STATUS: 000"; echo "ERROR: $1"; exit 0; }

# Input validation. `competitor-intel/competitors.md` is hand-edited and meant to be
# committed and shared across a team, so a URL out of it is not self-trusted input:
# only http(s) with a plain host is fetched. The file:// branch below is a test-only
# affordance and is gated, so production input can never reach a local-file read —
# scan.mjs enforces the same ^https?:// rule on the JS side of the same contract.
case "$url" in
  file://*)
    [ "${CI_ALLOW_FILE:-0}" = "1" ] ||
      refuse "refused — file:// URLs are not fetched (set CI_ALLOW_FILE=1 for offline tests)"
    ;;
  http://*|https://*)
    vh="${url#*://}"; vh="${vh%%[/?#]*}"
    case "$vh" in
      ''|*[!A-Za-z0-9.:-]*) refuse "refused — host must match [A-Za-z0-9.:-]+" ;;
    esac
    ;;
  *) refuse "refused — only http:// and https:// URLs are fetched" ;;
esac

tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT

case "$url" in
  file://*)
    src="${url#file://}"
    if [ -f "$src" ]; then cp "$src" "$tmp"; code=200; else code=404; fi
    ;;
  *)
    code="$(curl -sS -L --compressed --max-time "$TIMEOUT" -A "$UA" \
            -H "Accept-Language: $LOCALE" \
            -o "$tmp" -w '%{http_code}' "$url" 2>/dev/null)" || code=000
    ;;
esac

echo "URL: $url"
echo "STATUS: $code"
if [ "$code" != "200" ]; then
  echo "ERROR: fetch failed with status $code"
  exit 0
fi

# Flatten newlines so sed can match across original line breaks.
flat="$(tr '\n\r\t' '   ' < "$tmp")"

# Strip script/style/noscript with an awk state machine — regex nesting is unreliable.
stripped="$(printf '%s' "$flat" | awk '
{
  s = $0; out = ""
  while (length(s) > 0) {
    lo = tolower(s)
    if (match(lo, /<(script|style|noscript)[^>]*>/) == 0) { out = out s; break }
    out = out substr(s, 1, RSTART - 1)
    tag = substr(lo, RSTART + 1, RLENGTH - 2)
    sub(/[^a-z].*$/, "", tag)
    rest = substr(s, RSTART + RLENGTH)
    if (match(tolower(rest), "</" tag "[^>]*>") == 0) { out = out rest; break }
    s = substr(rest, RSTART + RLENGTH)
  }
  print out
}')"

sq="'"

# TITLE and H1 must be the FIRST match in document order, not the last. The document is
# flattened to a single line, so a `sed -n "s/.*<title...>\(...\)<\/title>.*/\1/p"` takes
# the LAST match (the leading `.*` is greedy) and the trailing `head -1` is a no-op. That
# handed an inline SVG accessibility <title> the identity of the page, and a footer <h1>
# the identity of the H1 — and `title` is the field §2 of diff-rules.md matches moved
# pages on. `grep -o` emits matches in document order, so `head -1` is the first one.
title="$(printf '%s' "$stripped" | grep -oiE '<title[^>]*>[^<]*</title>' | head -1 \
        | sed -e 's/<[^>]*>//g' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

meta="$(printf '%s' "$stripped" | grep -io "<meta[^>]*name=[\"$sq]description[\"$sq][^>]*>" | head -1 \
        | sed -n "s/.*content=[\"$sq]\([^\"$sq]*\)[\"$sq].*/\1/Ip")"

# h1 content routinely contains nested markup (<span>, <br>, <em>), so a `[^<]*` class
# will not do: take everything between the first <h1...> and the first following </h1>,
# then strip tags.
h1="$(printf '%s' "$stripped" | awk '
  {
    if (match(tolower($0), /<h1[^>]*>/) == 0) { exit }
    rest = substr($0, RSTART + RLENGTH)
    if (match(tolower(rest), /<\/h1[^>]*>/) == 0) {
      # Unclosed <h1>: take the text up to the next tag, never the rest of the document.
      sub(/<.*$/, "", rest); print rest; exit
    }
    print substr(rest, 1, RSTART - 1)
  }' \
  | sed -e 's/<[^>]*>//g' -e 's/[[:space:]]\{2,\}/ /g' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

headings="$(printf '%s' "$stripped" \
  | grep -oiE '<h[23][^>]*>[^<]{1,120}</h[23]>' \
  | sed -e 's/<[^>]*>//g' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
  | grep -v '^$' | head -30 | paste -sd'|' -)"

# Scheme, host and base directory of the document, for link resolution.
scheme="$(printf '%s' "$doc_url" | sed -n 's|^\([a-zA-Z][a-zA-Z0-9+.-]*\)://.*|\1|p')"
[ -n "$scheme" ] || scheme="https"
host="$(printf '%s' "$doc_url" | sed -e 's|^[a-zA-Z][a-zA-Z0-9+.-]*://||' -e 's|[/?#].*$||' \
        -e 's|^[^@]*@||' -e 's|:[0-9]*$||' | tr 'A-Z' 'a-z' | sed -e 's|^www\.||')"
root="$scheme://$host"
bpath="$(printf '%s' "$doc_url" | sed -e 's|^[a-zA-Z][a-zA-Z0-9+.-]*://[^/]*||' -e 's|[?#].*$||')"
case "$bpath" in
  '') bpath="/" ;;
  */) : ;;
  *)  bpath="${bpath%/*}/" ;;
esac

links="$(printf '%s' "$stripped" \
  | grep -oiE "href=[\"$sq][^\"$sq#]{1,200}[\"$sq]" \
  | sed -e "s/^[Hh][Rr][Ee][Ff]=[\"$sq]//" -e "s/[\"$sq]$//" \
  | grep -viE '\.(png|jpe?g|gif|svg|webp|css|js|ico|pdf|zip)$' \
  | awk -v root="$root" -v bpath="$bpath" -v h="$host" "$SAME_HOST_FN"'
      {
        l = $0
        if (l == "") next
        if (l ~ /^\/\//) next                          # protocol-relative: not resolved
        if (l ~ /^https?:\/\//) { if (same_host(l, h)) print l; next }
        if (l ~ /^[a-zA-Z][a-zA-Z0-9+.-]*:/) next      # mailto:, tel:, javascript:, data:
        if (l ~ /^\//) { print root l; next }          # root-relative
        # Relative to the document directory — "x", "./x", "../x". These used to fall
        # through with no action, so a page reachable only by a relative link was
        # invisible to the scan with no error and no trace in Data notes.
        p = bpath
        sub(/^\.\//, "", l)
        while (l ~ /^\.\.\//) {
          sub(/^\.\.\//, "", l)
          if (p != "/") sub(/[^\/]+\/$/, "", p)        # clamp at the root
        }
        if (l != "" && l != "." && l != "..") print root p l
      }' \
  | sed 's|/$||' | sort -u | head -60 | paste -sd'|' -)"

text="$(printf '%s' "$stripped" | sed -e 's/<[^>]*>/ /g' \
        | sed -e 's/&nbsp;/ /g' -e 's/&amp;/\&/g' -e 's/&quot;/"/g' -e "s/&#39;/$sq/g" \
        | tr -s ' ' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' \
        | LC_ALL=C.UTF-8 awk -v n="$max_text" '{ print substr($0, 1, n) }')"

echo "TITLE: $title"
echo "META: $meta"
echo "H1: $h1"
echo "HEADINGS: $headings"
echo "LINKS: $links"
echo "TEXT: $text"
