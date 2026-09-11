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

run_suite
