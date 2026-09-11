#!/usr/bin/env bash
# discover.sh — build a candidate URL list for one competitor.
# Order: nav links from the homepage first, sitemap supplementary.
# Floor: bash, curl, sed, grep, awk, tr, sort.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UA="${FETCH_UA:-Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36}"
TIMEOUT="${FETCH_TIMEOUT:-25}"

get() {
  case "$1" in
    file://*) cat "${1#file://}" 2>/dev/null ;;
    *) curl -sS -L --compressed --max-time "$TIMEOUT" -A "$UA" "$1" 2>/dev/null ;;
  esac
}

# --parse-robots <url>  → print the first Sitemap: URL, if any
if [ "${1:-}" = "--parse-robots" ]; then
  get "$2" | grep -i '^[[:space:]]*sitemap:' | head -1 \
    | sed -e 's/^[[:space:]]*[Ss][Ii][Tt][Ee][Mm][Aa][Pp]:[[:space:]]*//' | tr -d '\r'
  exit 0
fi

# --parse-index <url>   → print child <loc> entries when the doc is a sitemapindex
if [ "${1:-}" = "--parse-index" ]; then
  body="$(get "$2")"
  printf '%s' "$body" | grep -q '<sitemapindex' || exit 0
  printf '%s' "$body" | tr '<' '\n' | grep '^loc>' | sed 's/^loc>//' | tr -d '\r'
  exit 0
fi

classify() {
  # stdin: one URL per line. stdout: "<kind>\t<url>", excluded lines dropped.
  awk '
    {
      u = $0; lu = tolower(u)
      if (lu ~ /(privacy|terms|cookie|legal|cart|checkout|search|login|signin|career|jobs|contact|\.xml$|\.pdf$)/) next
      if (lu ~ /(\/services|\/solutions|\/what-we-do|\/offerings|\/products?\/)/) { print "services\t" u; next }
      if (lu ~ /(\/about|\/team|\/company|\/who-we-are)/)                         { print "about\t" u;    next }
      if (lu ~ /(\/case-stud|\/customers|\/clients|\/work\/|\/portfolio)/)        { print "case-study\t" u; next }
      print "other\t" u
    }'
}

# CI_CLASSIFY_ONLY=1 → read URLs on stdin, classify, exit (test hook)
if [ "${CI_CLASSIFY_ONLY:-0}" = "1" ]; then
  classify
  exit 0
fi

[ $# -ge 1 ] || { echo "usage: discover.sh <base_url> [max_other]" >&2; exit 2; }
base="$1"
max_other="${2:-10}"
host="$(printf '%s' "$base" | sed -e 's|^[a-zA-Z]*://||' -e 's|/.*$||' -e 's|^www\.||')"
root="$(printf '%s' "$base" | sed -e 's|\(^[a-zA-Z]*://[^/]*\).*|\1|')"

# 1. Nav links come from fetch.sh so extraction rules stay in one place.
nav="$(bash "$HERE/fetch.sh" "$base" 1 | grep '^LINKS:' | sed 's/^LINKS: //' | tr '|' '\n' | grep -v '^$')"

# 2. Sitemap: robots.txt first, then the conventional path. Recurse one level into an index.
sm="$(bash "$HERE/discover.sh" --parse-robots "$root/robots.txt")"
[ -n "$sm" ] || sm="$root/sitemap.xml"
sm_urls=""
if [ -n "$sm" ]; then
  body="$(get "$sm")"
  if printf '%s' "$body" | grep -q '<sitemapindex'; then
    for child in $(printf '%s' "$body" | tr '<' '\n' | grep '^loc>' | sed 's/^loc>//' | tr -d '\r' | head -5); do
      sm_urls="$sm_urls
$(get "$child" | tr '<' '\n' | grep '^loc>' | sed 's/^loc>//' | tr -d '\r')"
    done
  else
    sm_urls="$(printf '%s' "$body" | tr '<' '\n' | grep '^loc>' | sed 's/^loc>//' | tr -d '\r')"
  fi
fi
sm_urls="$(printf '%s' "$sm_urls" | grep -i "$host" | grep -v '^$' || true)"

if [ -n "$nav" ]; then source_label="nav"; elif [ -n "$sm_urls" ]; then source_label="sitemap"; else source_label="none"; fi
echo "SOURCE: $source_label"

all="$(printf '%s\n%s\n' "$nav" "$sm_urls" | grep -v '^$' | sed 's|/$||' | sort -u)"
classified="$(printf '%s' "$all" | classify)"

# services uncapped; about/case-study capped at 5; other capped at max_other
printf '%s\n' "$classified" | grep $'^services\t' || true
printf '%s\n' "$classified" | grep $'^about\t'      | head -5 || true
printf '%s\n' "$classified" | grep $'^case-study\t' | head -5 || true
printf '%s\n' "$classified" | grep $'^other\t'      | head -"$max_other" || true
