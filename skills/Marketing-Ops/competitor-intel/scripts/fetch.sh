#!/usr/bin/env bash
# fetch.sh — fetch one URL, emit labeled plain text.
# Floor: bash, curl, sed, grep, awk, tr. No jq, no python, no node.
# Never aborts a scan: non-200 and transport failures print ERROR and exit 0.
set -uo pipefail

UA="${FETCH_UA:-Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36}"
TIMEOUT="${FETCH_TIMEOUT:-25}"

[ $# -ge 1 ] || { echo "usage: fetch.sh <url> [max_text_chars]" >&2; exit 2; }
url="$1"
max_text="${2:-3000}"

tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT

case "$url" in
  file://*)
    src="${url#file://}"
    if [ -f "$src" ]; then cp "$src" "$tmp"; code=200; else code=404; fi
    ;;
  *)
    code="$(curl -sS -L --compressed --max-time "$TIMEOUT" -A "$UA" \
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
# the identity of the H1 — and `title` is the field diff-rules.md §2 matches moved pages
# on. `grep -o` emits matches in document order, so `head -1` is the first one.
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

host="$(printf '%s' "$url" | sed -e 's|^[a-zA-Z]*://||' -e 's|/.*$||' -e 's|^www\.||')"

links="$(printf '%s' "$stripped" \
  | grep -oiE "href=[\"$sq][^\"$sq#]{1,200}[\"$sq]" \
  | sed -e "s/^[Hh][Rr][Ee][Ff]=[\"$sq]//" -e "s/[\"$sq]$//" \
  | grep -viE '\.(png|jpe?g|gif|svg|webp|css|js|ico|pdf|zip)$' \
  | awk -v h="$host" '
      {
        l = $0
        if (l ~ /^\/\//) next
        if (l ~ /^\//) { printf "https://%s%s\n", h, l; next }
        if (l ~ /^https?:\/\//) { if (h != "" && index(tolower(l), h) > 0) print l; next }
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
