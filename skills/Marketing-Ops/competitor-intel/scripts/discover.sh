#!/usr/bin/env bash
# discover.sh — build a candidate URL list for one competitor.
# Order: nav links from the homepage first, sitemap supplementary.
# Floor: bash, curl, sed, grep, awk, tr, sort.
#
# Output (stdout), in this order:
#   SOURCE: nav|sitemap|none          which path produced the primary candidate list
#   CAPPED: about=N case-study=N other=N   only when a per-kind cap actually dropped rows
#   <kind>\t<source>\t<url>           one row per candidate page
#
# `source` is per-page provenance (`nav` or `sitemap`), not the global SOURCE label:
# briefing-format.md filters pages on it twice (the "from nav" services row and the
# "not in nav" bullet), so a single global label cannot serve.
#
# Environment:
#   FETCH_UA / FETCH_TIMEOUT / FETCH_LOCALE  passed through to curl and fetch.sh.
#   CI_ALLOW_FILE  test hook: set to 1 to permit file:// reads.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UA="${FETCH_UA:-Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36}"
TIMEOUT="${FETCH_TIMEOUT:-25}"
LOCALE="${FETCH_LOCALE:-en-US}"
TAB="$(printf '\t')"

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
    # file:// is a test-only affordance, gated so a hand-edited competitors.md can
    # never turn this into a local-file read. Same rule as fetch.sh.
    file://*) [ "${CI_ALLOW_FILE:-0}" = "1" ] && cat "${url#file://}" 2>/dev/null ;;
    http://*|https://*)
      curl -sS -L --compressed --max-time "$TIMEOUT" -A "$UA" \
           -H "Accept-Language: $LOCALE" "$url" 2>/dev/null ;;
    *) : ;;   # any other scheme: nothing fetched, callers see an empty body
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
  # stdin: "<source>\t<url>", one record per line.
  # stdout: "<kind>\t<source>\t<url>", excluded lines dropped, provenance preserved.
  #
  # Two different matching disciplines, kept deliberately separate — do not
  # merge them:
  #
  # EXCLUSION is strict whole-segment matching only: "(^|\/)word(\/|$)" —
  # no hyphen continuation, ever. A hyphen-permissive exclusion rule
  # silently drops real service pages that merely start with a keyword
  # ("/contact-center-solutions", "/search-engine-optimization-services",
  # "/legal-tech-consulting", "/cookie-cutter-analysis"), and dropping a
  # real page is the worst failure mode this tool has: it never shows up in
  # the briefing and nobody can tell it went missing. Letting a genuine
  # utility page slip through just costs one visible "other" row under an
  # existing cap — a cheap, recoverable mistake. So when a segment only
  # *starts* with an exclusion keyword, it is kept, not dropped. The
  # explicit allow-list below covers the common compound utility URLs
  # (contact-us, privacy-policy, ...) that are worth excluding by name
  # rather than guessing at with a pattern.
  #
  # CLASSIFICATION (services/about/case-study) is the opposite: it
  # legitimately needs to match hyphenated compounds — "/about-us" must
  # still classify as "about", "/case-studies/acme" as "case-study" — so
  # its boundary stays permissive on the right ("/", end-of-string, or
  # "-"). Never borrow this permissive close for the exclusion clause.
  #
  # RECORDED DEVIATIONS from the spec, both deliberate:
  #
  # 1. The spec maps utility paths (privacy, terms, cart, careers, ...) "→ other".
  #    This drops them instead. Kept, they would consume the `other` cap that real
  #    pages need, and a utility page has no competitive signal in it. Dropping is
  #    the better trade, but it is a deviation, so it is written down here.
  # 2. The spec says to classify `services` by URL segment *and nav placement*. Only
  #    the URL segment is used. Per-page `source` (nav vs sitemap) is now carried
  #    through to the output, so nav placement is available to a future revision —
  #    but `kind` is deliberately not derived from it: a nav-linked utility page
  #    would become a "service" and a sitemap-only service page would stop being
  #    one, and `kind` drives the comparison table's services row.
  awk -F'\t' -v OFS='\t' '
    {
      src = $1; u = $2
      if (u == "") next
      lu = tolower(u)
      if (lu ~ /(^|\/)(privacy|terms|cookie|legal|cart|checkout|search|login|signin|jobs?|careers?|contact|wp-admin)(\/|$)/) next
      if (lu ~ /(^|\/)(contact-us|privacy-policy|terms-of-service|terms-and-conditions|cookie-policy|terms-of-use)(\/|$)/) next
      if (lu ~ /\.(xml|pdf)$/) next
      if (lu ~ /(^|\/)(services?|solutions?|what-we-do|offerings?|products?)(\/|$|-)/)               { print "services", src, u;   next }
      if (lu ~ /(^|\/)(about|team|company|who-we-are)(\/|$|-)/)                                       { print "about", src, u;      next }
      if (lu ~ /(^|\/)(case-stud[a-z]*|customers?|clients?|portfolio)(\/|$|-)/ || lu ~ /(^|\/)work\//) { print "case-study", src, u; next }
      print "other", src, u
    }'
}

apply_caps() {
  # $1 = classified "<kind>\t<source>\t<url>" records (newline-separated).
  # $2 = max_other. services uncapped; about/case-study capped at 5.
  #
  # Emits "CAPPED: about=N case-study=N other=N" BEFORE the rows whenever a cap
  # actually dropped something. N is the number of rows DROPPED, never the number
  # kept. Without this the briefing's "Pages capped" Data note is unfulfillable —
  # the dropped rows are gone and the model can only infer the cap was hit from
  # "exactly 5 about pages are present", which is a guess presented as a run fact.
  # The line is omitted entirely when nothing was dropped.
  classified="$1"
  mo="$2"
  # A hand-edited config.json can carry a non-numeric maxSubpages; `head -"$mo"`
  # would error out on it. Fall back to the documented default instead.
  case "$mo" in
    ''|*[!0-9]*) mo=10 ;;
  esac
  n_about="$(printf '%s\n' "$classified" | grep -c $'^about\t' || true)"
  n_case="$(printf '%s\n' "$classified" | grep -c $'^case-study\t' || true)"
  n_other="$(printf '%s\n' "$classified" | grep -c $'^other\t' || true)"
  d_about=$(( n_about > 5 ? n_about - 5 : 0 ))
  d_case=$(( n_case > 5 ? n_case - 5 : 0 ))
  d_other=$(( n_other > mo ? n_other - mo : 0 ))
  if [ $(( d_about + d_case + d_other )) -gt 0 ]; then
    printf 'CAPPED: about=%s case-study=%s other=%s\n' "$d_about" "$d_case" "$d_other"
  fi
  printf '%s\n' "$classified" | grep $'^services\t' || true
  printf '%s\n' "$classified" | grep $'^about\t'      | head -5 || true
  printf '%s\n' "$classified" | grep $'^case-study\t' | head -5 || true
  printf '%s\n' "$classified" | grep $'^other\t'      | head -"$mo" || true
}

# CI_CLASSIFY_ONLY=1 → read "<source>\t<url>" records on stdin, classify (+ apply
# caps using an optional $2 max_other, default 10, same as the main flow), exit.
# Test hook.
if [ "${CI_CLASSIFY_ONLY:-0}" = "1" ]; then
  mo="${2:-10}"
  classified="$(classify)"
  apply_caps "$classified" "$mo"
  exit 0
fi

[ $# -ge 1 ] || { echo "usage: discover.sh <base_url> [max_other]" >&2; exit 2; }
base="$1"
max_other="${2:-10}"

# Same input contract as fetch.sh: the base URL comes from a hand-edited,
# team-shared competitors.md, so validate it rather than trusting it.
case "$base" in
  file://*)
    [ "${CI_ALLOW_FILE:-0}" = "1" ] ||
      { echo "discover.sh: refused — file:// base URLs are not fetched" >&2; exit 2; }
    ;;
  http://*|https://*)
    vh="${base#*://}"; vh="${vh%%[/?#]*}"
    case "$vh" in
      ''|*[!A-Za-z0-9.:-]*)
        echo "discover.sh: refused — host must match [A-Za-z0-9.:-]+" >&2; exit 2 ;;
    esac
    ;;
  *) echo "discover.sh: refused — only http:// and https:// base URLs are fetched" >&2; exit 2 ;;
esac

host="$(printf '%s' "$base" | sed -e 's|^[a-zA-Z][a-zA-Z0-9+.-]*://||' -e 's|[/?#].*$||' \
        -e 's|^[^@]*@||' -e 's|:[0-9]*$||' | tr 'A-Z' 'a-z' | sed -e 's|^www\.||')"
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
    # set -f: a <loc> containing a glob character would otherwise expand against cwd.
    set -f
    for child in $(printf '%s' "$body" | tr '<' '\n' | grep '^loc>' | sed 's/^loc>//' | tr -d '\r' | head -5); do
      sm_urls="$sm_urls
$(get "$child" | tr '<' '\n' | grep '^loc>' | sed 's/^loc>//' | tr -d '\r')"
    done
    set +f
  else
    sm_urls="$(printf '%s' "$body" | tr '<' '\n' | grep '^loc>' | sed 's/^loc>//' | tr -d '\r')"
  fi
fi
# Same-host filtering goes through fetch.sh's --same-host mode: a `grep -i "$host"`
# here was an unanchored regex whose dots are wildcards, so a lookalike domain or a
# CDN URL carrying the host in a query parameter passed as same-host.
sm_urls="$(printf '%s\n' "$sm_urls" | grep -v '^$' | bash "$HERE/fetch.sh" --same-host "$host" || true)"

nav_urls="$(printf '%s\n' "$nav" | grep -v '^$' | sed 's|/$||' | sort -u)"
sm_urls="$(printf '%s\n' "$sm_urls" | grep -v '^$' | sed 's|/$||' | sort -u)"

if [ -n "$nav_urls" ]; then source_label="nav"; elif [ -n "$sm_urls" ]; then source_label="sitemap"; else source_label="none"; fi
echo "SOURCE: $source_label"

# Tag every candidate with where it came from and carry that through to the output.
# When the same URL appears in both lists, nav wins: it is the stronger provenance and
# the one briefing-format.md's "not in nav" bullet tests for.
all="$( { printf '%s\n' "$nav_urls" | sed "s|^|nav$TAB|"
          printf '%s\n' "$sm_urls"  | sed "s|^|sitemap$TAB|"
        } | awk -F'\t' '$2 != "" && !seen[$2]++' | LC_ALL=C sort -t"$TAB" -k2,2 )"
classified="$(printf '%s\n' "$all" | classify)"

apply_caps "$classified" "$max_other"
