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

run_suite
