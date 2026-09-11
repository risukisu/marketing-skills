#!/usr/bin/env bash
# discover.sh — build a candidate URL list for one competitor.
# Order: nav links from the homepage first, sitemap supplementary.
# Floor: bash, curl, sed, grep, awk, tr, sort.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UA="${FETCH_UA:-Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36}"
TIMEOUT="${FETCH_TIMEOUT:-25}"

get() {
  url="$1"
  # Test-only rewrite: when CI_LOCAL_FIXTURE_BASE is set, redirect
  # https://example.com/* reads to a local fixture file by basename, so the
  # sitemap-index recursion can be exercised offline against committed
  # fixtures instead of the real network. No effect unless the var is set.
  if [ -n "${CI_LOCAL_FIXTURE_BASE:-}" ]; then
    case "$url" in
      https://example.com/*) url="file://$CI_LOCAL_FIXTURE_BASE/$(basename "$url")" ;;
    esac
  fi
  case "$url" in
    file://*) cat "${url#file://}" 2>/dev/null ;;
    *) curl -sS -L --compressed --max-time "$TIMEOUT" -A "$UA" "$url" 2>/dev/null ;;
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
  # Segment-anchored matching: a keyword must start right at a path-segment
  # boundary — the string start or immediately after "/" — via "(^|\/)".
  # This stops it matching inside an unrelated word (e.g. "search" must not
  # fire on "research"; "career" must not fire on "career-mobility", which
  # is a distinct, legitimate case-study page, not a jobs page).
  # Exclusion terms use a permissive close (/, end-of-string, ".", or "-")
  # so hyphenated compounds like "privacy-policy" still drop — except
  # "career(s)", which must NOT swallow a hyphenated continuation, so it
  # gets a strict close (/, end-of-string, or ".") in its own clause.
  awk '
    {
      u = $0; lu = tolower(u)
      if (lu ~ /(^|\/)(privacy|terms|cookie|legal|carts?|checkouts?|search|logins?|signins?|jobs?|contact|wp-admin)(\/|$|\.|-)/) next
      if (lu ~ /(^|\/)careers?(\/|$|\.)/) next
      if (lu ~ /\.(xml|pdf)$/) next
      if (lu ~ /(^|\/)(services?|solutions?|what-we-do|offerings?|products?)(\/|$|-)/)               { print "services\t" u;    next }
      if (lu ~ /(^|\/)(about|team|company|who-we-are)(\/|$|-)/)                                       { print "about\t" u;       next }
      if (lu ~ /(^|\/)(case-stud[a-z]*|customers?|clients?|portfolio)(\/|$|-)/ || lu ~ /(^|\/)work\//) { print "case-study\t" u;  next }
      print "other\t" u
    }'
}

apply_caps() {
  # $1 = classified "<kind>\t<url>" records (newline-separated).
  # $2 = max_other. services uncapped; about/case-study capped at 5.
  classified="$1"
  mo="$2"
  printf '%s\n' "$classified" | grep $'^services\t' || true
  printf '%s\n' "$classified" | grep $'^about\t'      | head -5 || true
  printf '%s\n' "$classified" | grep $'^case-study\t' | head -5 || true
  printf '%s\n' "$classified" | grep $'^other\t'      | head -"$mo" || true
}

# CI_CLASSIFY_ONLY=1 → read URLs on stdin, classify (+ apply caps using an
# optional $2 max_other, default 10, same as the main flow), exit. Test hook.
if [ "${CI_CLASSIFY_ONLY:-0}" = "1" ]; then
  mo="${2:-10}"
  classified="$(classify)"
  apply_caps "$classified" "$mo"
  exit 0
fi

[ $# -ge 1 ] || { echo "usage: discover.sh <base_url> [max_other]" >&2; exit 2; }
base="$1"
max_other="${2:-10}"
host="$(printf '%s' "$base" | sed -e 's|^[a-zA-Z]*://||' -e 's|/.*$||' -e 's|^www\.||')"
root="$(printf '%s' "$base" | sed -e 's|\(^[a-zA-Z]*://[^/]*\).*|\1|')"

# 1. Nav links come from fetch.sh so extraction rules stay in one place.
# CI_SKIP_NAV=1 skips this (test hook) so a sitemap-only offline test isn't
# forced to make a real fetch of $base just to get an empty/irrelevant nav.
if [ "${CI_SKIP_NAV:-0}" = "1" ]; then
  nav=""
else
  nav="$(bash "$HERE/fetch.sh" "$base" 1 | grep '^LINKS:' | sed 's/^LINKS: //' | tr '|' '\n' | grep -v '^$')"
fi

# 2. Sitemap: robots.txt first, then the conventional path. Recurse one level into an index.
# CI_ROBOTS_OVERRIDE lets a test point at a fixture robots.txt directly
# (test hook) instead of deriving the location from $base.
robots_url="${CI_ROBOTS_OVERRIDE:-$root/robots.txt}"
sm="$(bash "$HERE/discover.sh" --parse-robots "$robots_url")"
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

apply_caps "$classified" "$max_other"
