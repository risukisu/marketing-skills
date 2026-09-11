#!/usr/bin/env bash
# Test harness for competitor-intel scripts. Floor only: bash, sed, grep, awk.
# Usage: bash tests/run.sh [--live]    (--live also runs network tests)
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$HERE/.." && pwd)"
FIXTURES="$HERE/fixtures"
SCRIPTS="$SKILL_DIR/scripts"
LIVE=0
[ "${1:-}" = "--live" ] && LIVE=1
TAB="$(printf '\t')"

# The offline fixtures are read through `file://`, which both scripts refuse in
# production so a hand-edited competitors.md can never turn a scan into a local-file
# read. The tests opt back in explicitly.
export CI_ALLOW_FILE=1

PASS=0; FAIL=0

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    PASS=$((PASS+1)); printf '  ok   %s\n' "$label"
  else
    FAIL=$((FAIL+1)); printf '  FAIL %s\n       expected: [%s]\n       actual:   [%s]\n' "$label" "$expected" "$actual"
  fi
}

assert_contains() {
  local label="$1" needle="$2" haystack="$3"
  case "$haystack" in
    *"$needle"*) PASS=$((PASS+1)); printf '  ok   %s\n' "$label" ;;
    *) FAIL=$((FAIL+1)); printf '  FAIL %s\n       missing: [%s]\n' "$label" "$needle" ;;
  esac
}

assert_not_contains() {
  local label="$1" needle="$2" haystack="$3"
  case "$haystack" in
    *"$needle"*) FAIL=$((FAIL+1)); printf '  FAIL %s\n       should not contain: [%s]\n' "$label" "$needle" ;;
    *) PASS=$((PASS+1)); printf '  ok   %s\n' "$label" ;;
  esac
}

# classify() consumes "<source>\t<url>" records, because per-page provenance has to
# survive all the way to the briefing. The URL lists below are bare, so tag them.
# $1 = source label, $2 = max_other (optional). URLs on stdin.
classify_urls() {
  sed "s|^|$1$TAB|" | CI_CLASSIFY_ONLY=1 bash "$SCRIPTS/discover.sh" "https://example.com/" "${2:-10}"
}

run_suite() {
  for fn in $(declare -F | awk '{print $3}' | grep '^test_' | sort); do
    printf '\n%s\n' "$fn"
    "$fn"
  done
  printf '\n----\npassed: %s  failed: %s\n' "$PASS" "$FAIL"
  [ "$FAIL" -eq 0 ]
}

test_fetch_parses_simple_fixture() {
  out="$(bash "$SCRIPTS/fetch.sh" "file://$FIXTURES/simple.html")"
  assert_contains "status"   "STATUS: 200" "$out"
  assert_contains "title"    "TITLE: Acme Analytics — Data Science Consulting" "$out"
  assert_contains "meta"     "META: We build data platforms for regulated industries." "$out"
  assert_contains "h1"       "H1: Data science for regulated industries" "$out"
  assert_contains "headings" "What we do" "$out"
  assert_contains "text"     "validated analytics pipelines" "$out"
}

test_fetch_strips_script_and_style() {
  out="$(bash "$SCRIPTS/fetch.sh" "file://$FIXTURES/scripty.html")"
  assert_contains     "keeps real heading" "Real heading"       "$out"
  assert_contains     "keeps body copy"    "Visible body copy." "$out"
  assert_not_contains "drops inline js"    "INLINEJS"           "$out"
  assert_not_contains "drops json block"   "JSONBLOB"           "$out"
  assert_not_contains "drops css"          "Helvetica"          "$out"
}

test_fetch_truncates_text() {
  out="$(bash "$SCRIPTS/fetch.sh" "file://$FIXTURES/simple.html" 40)"
  body="${out#*TEXT: }"
  if [ "${#body}" -le 45 ]; then PASS=$((PASS+1)); printf '  ok   text truncated to cap\n'
  else FAIL=$((FAIL+1)); printf '  FAIL text truncated to cap (len=%s)\n' "${#body}"; fi
}

test_fetch_links_are_absolute_and_same_host() {
  out="$(bash "$SCRIPTS/fetch.sh" "file://$FIXTURES/simple.html")"
  links="$(printf '%s' "$out" | grep '^LINKS:')"
  assert_not_contains "drops offsite link" "external.example.org" "$links"
}

test_fetch_handles_dead_host() {
  out="$(bash "$SCRIPTS/fetch.sh" "https://this-host-does-not-exist.invalid/" 2>/dev/null)"; rc=$?
  assert_contains "reports error" "ERROR:" "$out"
  assert_eq       "exits zero"    "0"      "$rc"
}

test_fetch_keeps_trailing_content_after_unclosed_tag() {
  out="$(bash "$SCRIPTS/fetch.sh" "file://$FIXTURES/unclosed.html")"
  assert_contains "keeps h1 after unclosed script"   "H1: Widgets for every workflow" "$out"
  assert_contains "keeps trailing body text"         "Real trailing body copy after an unclosed script tag." "$out"
}

test_fetch_truncation_is_codepoint_safe() {
  # 16 chars lands the cap exactly on the em-dash in "Acme Analytics — ..."
  # (verify: printf '%s' "$TEXT" | LC_ALL=C.UTF-8 awk '{print index($0,"\xe2\x80\x94")}' -> 16).
  # A byte-based cut (e.g. GNU `cut -c` outside a UTF-8-aware locale) truncates
  # mid-codepoint here and emits invalid UTF-8; a codepoint-aware truncation does not.
  out="$(bash "$SCRIPTS/fetch.sh" "file://$FIXTURES/simple.html" 16)"
  body="${out#*TEXT: }"
  assert_contains "truncation includes whole em-dash char" "—" "$body"
  if command -v iconv >/dev/null 2>&1; then
    if printf '%s' "$body" | iconv -f utf-8 -t utf-8 >/dev/null 2>&1; then
      PASS=$((PASS+1)); printf '  ok   truncated text is valid utf-8\n'
    else
      FAIL=$((FAIL+1)); printf '  FAIL truncated text is valid utf-8 (iconv rejected it)\n'
    fi
  else
    printf '  skip truncated text utf-8 validity check (iconv not available)\n'
  fi
}

test_fetch_takes_the_first_title_and_h1_not_the_last() {
  # A greedy `sed -n "s/.*<title...>"` against a one-line document takes the LAST
  # match, so an inline SVG accessibility <title> became the page title and a footer
  # <h1> became the H1 — and `title` is the identity field diff-rules.md §2 matches
  # moved pages on. Both must be the first occurrence in document order.
  out="$(bash "$SCRIPTS/fetch.sh" "file://$FIXTURES/tricky-headings.html")"
  title_line="$(printf '%s\n' "$out" | grep '^TITLE:')"
  h1_line="$(printf '%s\n' "$out" | grep '^H1:')"
  assert_eq           "head title wins over svg title"  "TITLE: Beacon Analytics — Validated Pipelines" "$title_line"
  assert_not_contains "svg title is not the page title" "Beacon logo icon" "$title_line"
  assert_eq           "first h1 wins over footer h1"    "H1: Pipelines for regulated data" "$h1_line"
  assert_not_contains "footer h1 is not the h1"         "footer nav" "$h1_line"
}

test_fetch_resolves_relative_hrefs() {
  # "services/consulting", "./about-us" and "../parent-page" used to fall through the
  # link awk with no action, so a page reachable only by a relative link was invisible
  # to the scan — no error, no Data-notes trace.
  out="$(CI_BASE_URL="https://example.com/docs/page.html" bash "$SCRIPTS/fetch.sh" "file://$FIXTURES/links.html")"
  links="$(printf '%s\n' "$out" | grep '^LINKS:')"
  assert_contains "bare relative absolutized"      "https://example.com/docs/services/consulting" "$links"
  assert_contains "./ relative absolutized"        "https://example.com/docs/about-us"            "$links"
  assert_contains "../ relative absolutized"       "https://example.com/parent-page"              "$links"
  assert_contains "root-relative still absolutized" "https://example.com/root-page"               "$links"
  assert_not_contains "mailto dropped"             "mailto:"                                      "$links"
}

test_fetch_same_host_is_host_equality_not_substring() {
  # `index(tolower(url), host) > 0` kept "https://notexample.com/evil" and
  # "https://cdn.other.net/?u=example.com" as same-host; both then landed in the
  # snapshot as this competitor's pages.
  out="$(CI_BASE_URL="https://example.com/docs/page.html" bash "$SCRIPTS/fetch.sh" "file://$FIXTURES/links.html")"
  links="$(printf '%s\n' "$out" | grep '^LINKS:')"
  assert_not_contains "drops lookalike host"       "notexample.com"        "$links"
  assert_not_contains "drops host-in-query url"    "cdn.other.net"         "$links"
  assert_not_contains "drops plainly offsite host" "external.example.org"  "$links"
  assert_contains     "keeps same host"            "https://example.com/absolute-page"       "$links"
  assert_contains     "keeps subdomain"            "https://uk.example.com/subdomain-page"   "$links"
}

test_fetch_refuses_non_http_and_ungated_file_urls() {
  # competitors.md is hand-edited and shared, so it is not self-trusted input.
  out="$(CI_ALLOW_FILE=0 bash "$SCRIPTS/fetch.sh" "file://$FIXTURES/simple.html")"; rc=$?
  assert_contains "ungated file:// refused" "ERROR: refused" "$out"
  assert_not_contains "no content leaked"   "Acme Analytics" "$out"
  assert_eq       "still exits zero"        "0"              "$rc"
  out="$(bash "$SCRIPTS/fetch.sh" 'ftp://example.com/x')"
  assert_contains "non-http scheme refused" "only http:// and https://" "$out"
  out="$(bash "$SCRIPTS/fetch.sh" 'https://ex`whoami`.com/')"
  assert_contains "shell metachars in host refused" "host must match" "$out"
}

test_discover_classifies_by_url_segment() {
  out="$(classify_urls nav <<'URLS'
https://example.com/services/validation
https://example.com/about-us
https://example.com/case-studies/acme
https://example.com/privacy-policy
https://example.com/cart
https://example.com/feed.xml
URLS
)"
  assert_contains "services classified" "services${TAB}nav${TAB}https://example.com/services/validation" "$out"
  assert_contains "about classified"    "about${TAB}nav${TAB}https://example.com/about-us"               "$out"
  assert_contains "case study"          "case-study${TAB}nav${TAB}https://example.com/case-studies/acme" "$out"
  assert_not_contains "drops privacy"   "privacy-policy" "$out"
  assert_not_contains "drops cart"      "/cart"          "$out"
  assert_not_contains "drops xml"       "feed.xml"       "$out"
}

test_discover_carries_per_page_source_through() {
  # briefing-format.md filters pages on `source` twice — the "Primary services (from
  # nav)" row and the "not in nav" bullet — so provenance is per page, not one global
  # SOURCE label stamped on everything.
  out="$(classify_urls sitemap <<'URLS'
https://example.com/services/validation
https://example.com/blog/post-1
URLS
)"
  assert_contains "services carries sitemap source" "services${TAB}sitemap${TAB}https://example.com/services/validation" "$out"
  assert_contains "other carries sitemap source"    "other${TAB}sitemap${TAB}https://example.com/blog/post-1"            "$out"
  assert_not_contains "no nav label invented"       "${TAB}nav${TAB}" "$out"
}

test_discover_detects_sitemap_index() {
  out="$(bash "$SCRIPTS/discover.sh" --parse-index "file://$FIXTURES/sitemap_index.xml")"
  assert_contains "finds child sitemap 1" "https://example.com/page-sitemap.xml" "$out"
  assert_contains "finds child sitemap 2" "https://example.com/post-sitemap.xml" "$out"
}

test_discover_reads_sitemap_from_robots() {
  out="$(bash "$SCRIPTS/discover.sh" --parse-robots "file://$FIXTURES/robots.txt")"
  assert_eq "extracts sitemap url" "https://example.com/sitemap_index.xml" "$out"
}

test_discover_live_nav_fallback() {
  [ "$LIVE" -eq 1 ] || { printf '  skip live nav fallback (pass --live)\n'; return 0; }
  out="$(bash "$SCRIPTS/discover.sh" "https://example.com/" 5)"
  assert_contains "emits a SOURCE line" "SOURCE:" "$out"
}

test_discover_classify_segment_boundaries() {
  out="$(classify_urls nav <<'URLS'
https://example.com/research/
https://example.com/our-research
https://example.com/search
https://example.com/search/
https://example.com/wp-admin/about.php
https://example.com/about
https://example.com/about/
https://example.com/about-us
https://example.com/services/validation
https://example.com/careers
https://example.com/case-studies/career-mobility
URLS
)"
  assert_contains     "research/ kept, not dropped"       "${TAB}https://example.com/research/" "$out"
  assert_contains     "our-research kept, not dropped"    "${TAB}https://example.com/our-research" "$out"
  assert_not_contains "drops /search"                     "https://example.com/search"         "$out"
  assert_not_contains "drops wp-admin about, not about"   "https://example.com/wp-admin/about.php" "$out"
  assert_contains     "about (bare)"                      "about${TAB}nav${TAB}https://example.com/about" "$out"
  assert_contains     "about (slash)"                     "about${TAB}nav${TAB}https://example.com/about/" "$out"
  assert_contains     "about (hyphen)"                    "about${TAB}nav${TAB}https://example.com/about-us" "$out"
  assert_contains     "services segment"                  "services${TAB}nav${TAB}https://example.com/services/validation" "$out"
  assert_not_contains "drops /careers"                    "https://example.com/careers"        "$out"
  assert_contains     "career-mobility is case-study"     "case-study${TAB}nav${TAB}https://example.com/case-studies/career-mobility" "$out"
}

test_discover_main_flow_sitemap_index_recursion() {
  out="$(CI_SKIP_NAV=1 CI_ROBOTS_OVERRIDE="file://$FIXTURES/robots.txt" CI_LOCAL_FIXTURE_BASE="$FIXTURES" \
        bash "$SCRIPTS/discover.sh" "https://example.com/" 10)"
  assert_contains "source is sitemap"        "SOURCE: sitemap" "$out"
  assert_contains "child 1 service page"     "services${TAB}sitemap${TAB}https://example.com/services/consulting" "$out"
  assert_contains "child 1 about page"       "about${TAB}sitemap${TAB}https://example.com/about-us" "$out"
  assert_contains "child 2 case study"       "case-study${TAB}sitemap${TAB}https://example.com/case-studies/acme" "$out"
  assert_contains "child 2 other page"       "other${TAB}sitemap${TAB}https://example.com/blog/post-1" "$out"
  assert_not_contains "no CAPPED line when no cap hit" "CAPPED:" "$out"
}

test_discover_applies_caps() {
  out="$(classify_urls nav 3 <<'URLS'
https://example.com/services/one
https://example.com/services/two
https://example.com/services/three
https://example.com/services/four
https://example.com/services/five
https://example.com/services/six
https://example.com/services/seven
https://example.com/about-1
https://example.com/about-2
https://example.com/about-3
https://example.com/about-4
https://example.com/about-5
https://example.com/about-6
https://example.com/about-7
https://example.com/case-studies/1
https://example.com/case-studies/2
https://example.com/case-studies/3
https://example.com/case-studies/4
https://example.com/case-studies/5
https://example.com/case-studies/6
https://example.com/blog/1
https://example.com/blog/2
https://example.com/blog/3
https://example.com/blog/4
https://example.com/blog/5
URLS
)"
  services_count="$(printf '%s\n' "$out" | grep -c $'^services\t')"
  about_count="$(printf '%s\n' "$out" | grep -c $'^about\t')"
  case_count="$(printf '%s\n' "$out" | grep -c $'^case-study\t')"
  other_count="$(printf '%s\n' "$out" | grep -c $'^other\t')"
  assert_eq "services uncapped (7)"          "7" "$services_count"
  assert_eq "about capped at 5"              "5" "$about_count"
  assert_eq "case-study capped at 5"         "5" "$case_count"
  assert_eq "other capped at max_other (3)"  "3" "$other_count"
  # The dropped rows are gone, so the cap has to be reported as a run fact or the
  # briefing's "Pages capped" Data note can only be guessed at. N = rows dropped.
  assert_contains "reports what the caps dropped" "CAPPED: about=2 case-study=1 other=2" "$out"
}

test_discover_caps_tolerate_non_numeric_max() {
  # A hand-edited config.json can carry maxSubpages: "ten"; `head -"$mo"` errors on it.
  out="$(classify_urls nav "ten" <<'URLS'
https://example.com/blog/1
https://example.com/blog/2
URLS
)"
  assert_contains     "falls back to the default cap" "other${TAB}nav${TAB}https://example.com/blog/1" "$out"
  assert_not_contains "no head error leaked"          "invalid number"                                "$out"
}

test_discover_exclusion_keeps_prefix_matches() {
  # A segment that merely STARTS with an exclusion keyword, followed by a
  # hyphen, must be kept — these are real service pages, not utility pages.
  out="$(classify_urls nav <<'URLS'
https://example.com/contact-center-solutions
https://example.com/legal-tech-consulting
https://example.com/search-engine-optimization-services
https://example.com/cookie-cutter-analysis
https://example.com/research/
https://example.com/our-research
https://example.com/case-studies/career-mobility
URLS
)"
  assert_contains "kept: contact-center-solutions"      "https://example.com/contact-center-solutions" "$out"
  assert_contains "kept: legal-tech-consulting"          "https://example.com/legal-tech-consulting" "$out"
  assert_contains "kept: search-engine-optimization-services" "https://example.com/search-engine-optimization-services" "$out"
  assert_contains "kept: cookie-cutter-analysis"         "https://example.com/cookie-cutter-analysis" "$out"
  assert_contains "kept: research/"                      "https://example.com/research/" "$out"
  assert_contains "kept: our-research"                   "https://example.com/our-research" "$out"
  assert_contains "kept: career-mobility, as case-study" "case-study${TAB}nav${TAB}https://example.com/case-studies/career-mobility" "$out"
}

test_discover_exclusion_drops_whole_segment_and_known_compounds() {
  # Every URL below is a whole-segment exclusion match or a named compound
  # in the allow-list (or a .xml/.pdf suffix) — nothing should survive.
  out="$(classify_urls nav <<'URLS'
https://example.com/contact
https://example.com/contact/
https://example.com/contact-us
https://example.com/legal
https://example.com/search
https://example.com/search/
https://example.com/privacy-policy
https://example.com/terms-of-service
https://example.com/careers
https://example.com/wp-admin/about.php
https://example.com/brochure.pdf
https://example.com/feed.xml
URLS
)"
  assert_eq "nothing survives (all 12 excluded)" "" "$out"
}

run_suite
