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
    if (match(tolower(rest), "</" tag "[^>]*>") == 0) break
    s = substr(rest, RSTART + RLENGTH)
  }
  print out
}')"

sq="'"

title="$(printf '%s' "$stripped" | sed -n "s/.*<title[^>]*>\([^<]*\)<\/title>.*/\1/Ip" | head -1 \
        | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

meta="$(printf '%s' "$stripped" | grep -io "<meta[^>]*name=[\"$sq]description[\"$sq][^>]*>" | head -1 \
        | sed -n "s/.*content=[\"$sq]\([^\"$sq]*\)[\"$sq].*/\1/Ip")"

h1="$(printf '%s' "$stripped" | sed -n "s/.*<h1[^>]*>\(.*\)<\/h1>.*/\1/Ip" | head -1 \
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
        | tr -s ' ' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | cut -c1-"$max_text")"

echo "TITLE: $title"
echo "META: $meta"
echo "H1: $h1"
echo "HEADINGS: $headings"
echo "LINKS: $links"
echo "TEXT: $text"
