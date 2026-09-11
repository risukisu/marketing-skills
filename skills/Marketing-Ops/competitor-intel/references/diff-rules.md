# Diff rules

These rules turn two snapshots (previous run + current run) into `changes.json`. Follow them
literally and in order. The diff step has no script — you are the diff engine — so treat this
file as an algorithm, not a suggestion.

## 0. Snapshot rigidity contract

Every snapshot you diff — and every snapshot you assemble — must already satisfy
`snapshot-schema.json`'s contract before it reaches these rules: every key in the schema is
present, no key outside the schema is present, and an empty value is written as `""`, `0`, or
`[]` — never omitted and never `null`. This is not optional formatting; the diff rules below
assume it and will misbehave on a snapshot that doesn't satisfy it. (§6 below is the runtime
check that catches a snapshot which fails this contract. This same rule is restated in
`SKILL.md` for the assembly step — that duplication is intentional.)

## 1. Normalize before comparing

Before matching or comparing anything, normalize every URL (both snapshots' `url` fields, at
the home level and inside every `pages[]` entry):

- Strip a single trailing `/` from the path (`/about-us/` → `/about-us`). Root path `/` stays `/`.
- Strip a leading `www.` from the host.
- Strip the query string (everything from `?` onward).
- Strip the fragment (everything from `#` onward).
- Lowercase the host. Do **not** lowercase the path — path case is preserved and significant.

Use the normalized URL for every comparison and match below. Report original (non-normalized)
URLs in `changes.json` and the briefing — normalization is a comparison step, not a display
transform.

## 2. Match pages in this precedence

For each competitor, match pages between the previous snapshot's `pages[]` and the current
snapshot's `pages[]`, trying each rule in order until one produces a match:

1. **Normalized URL match.** Same normalized URL in both snapshots → same page. Skip to §3 for
   this pair; do not evaluate title or h1 for it.
2. **Exact `title` match.** If no URL match, look for a previous page and a current page with
   byte-for-byte identical `title`. If **exactly one** such pair exists → same page (a
   **moved** page, since the URL already failed to match — see below). If **zero** pairs tie →
   no match at this tier, fall through to rule 3. If **more than one** pair ties (ambiguous —
   e.g. two previous pages and one current page all share the same title, or vice versa) → this
   is also "no match at this tier": fall through to rule 3, do not resolve the tie here.
3. **Exact `h1` match.** Only reached when rule 2 produced no match (zero ties or an ambiguous
   tie). Same logic as rule 2, using `h1` instead of `title`: exactly one tying pair → matched
   (moved); zero or ambiguous ties → no match at this tier.

A page matched by title or h1 (rule 2 or rule 3) with a **different** normalized URL is a
**moved** page. Never report it as a removed page plus a new page — that is the specific
failure mode this rule exists to prevent.

**Terminal state.** A previous-snapshot page reaches "unmatched" only after rule 1 found no
URL match, AND rule 2 found no match (zero or ambiguous title ties), AND rule 3 found no match
(zero or ambiguous h1 ties). Only then is it **removed**. The same terminal condition, run from
the current snapshot's side, makes a current-snapshot page **new**. An ambiguous tie at rule 2
is never the final verdict by itself — it only means "try rule 3 next." If rule 3 also ties or
misses, the page is unmatched (removed/new), and note the rule-2 ambiguity in Data notes so a
human can resolve it by hand if useful.

## 3. Emit exactly these change kinds

The diff produces exactly seven fields per competitor, no more:

- `new_pages` — normalized-unmatched current pages (report original `url`).
- `removed_pages` — normalized-unmatched previous pages (report original `url`).
- `moved_pages` — title/h1-matched pages with a changed URL: `{ "from", "to", "matchedOn" }`,
  where `matchedOn` is `"title"` or `"h1"`.
- `home_changes` — changes to `home.title`, `home.h1`, or `home.metaDescription` only, one
  entry per changed field: `{ "field", "before", "after" }`.
- `services_changes` — for pages matched (by any rule in §2) on both sides, where the
  **current-snapshot page's** `kind` is `"services"` (the previous side's `kind` is not
  consulted — `kind` itself is never diffed, per §4 — so a page recategorized into or out of
  `services` across the window is judged by where it landed), changes to that page's `title`
  or `h1` only, one entry per changed field per page: `{ "url", "field", "before", "after" }`
  (`url` = the current-snapshot normalized URL).
- `ad_count_delta` — `current.linkedinAds.count - previous.linkedinAds.count` (integer, may be
  negative).
- `new_ad_headlines` — `headline` values present in `current.linkedinAds.ads[]` whose
  `headline` does not appear in `previous.linkedinAds.ads[]`.

## 4. Report nothing else

`text` fields (home or page) are model-summarized on every run and are never diffed or
reported — a difference in `text` wording is not evidence of a real change on the competitor's
site. `headings`, `source`, `kind`, and screenshot paths are never diffed (subpages in
`pages[]` have no `metaDescription` key at all — only `home` does). If it is not one of the
seven fields in §3, it does not go in `changes.json` and it does not go in the briefing.

## 5. Baseline runs

If there is no previous snapshot for a competitor (first run, or no prior run found), do not
diff. Write `changes.json` for that competitor as `{"baseline": true}` in place of the normal
per-competitor object, and say "baseline run" in the briefing instead of listing changes.

## 6. Schema drift guard

Before diffing a competitor, confirm both the previous and current snapshot objects carry
**every key in `snapshot-schema.json`, recursively** — not just the nine top-level keys.
Concretely, check:

- Top level: `name`, `url`, `fetchedAt`, `tier`, `home`, `pages`, `linkedinAds`, `screenshots`,
  `errors`.
- `home.*`: `title`, `metaDescription`, `h1`, `headings`, `text`.
- Each entry of `pages[]`: `url`, `kind`, `source`, `title`, `h1`, `text`.
- `linkedinAds.*`: `tier`, `count`, `ads`.
- Each entry of `linkedinAds.ads[]`: `headline`, `body`, `firstSeen`.
- `screenshots.*`: `home`, `pages`.

If the previous snapshot is missing any key at any of these levels — including a missing
`firstSeen` on an ad, which is exactly the kind of drift this guard exists to catch once a
later task starts adding fields to `ads[]` entries — treat this run as a baseline for that
competitor (per §5) instead of diffing, and record the reason in Data notes (e.g. "previous
snapshot's `linkedinAds.ads[0]` missing `firstSeen` — treated as baseline"). An empty array
(`pages: []` or `linkedinAds.ads: []`) has no entries to check and is not itself drift. Never
diff against a snapshot that doesn't match the current schema shape at every level.

## `changes.json` shape

`comparedTo` names the previous run's directory/timestamp, in the run-stamp form
`YYYY-MM-DD_HH-mm` (e.g. `2026-09-01_09-00`) — not the ISO `fetchedAt` form the snapshot itself
uses. Derive it from the previous snapshot's `fetchedAt` (`2026-09-01T09:00:00Z` →
`2026-09-01_09-00`) or from the run directory name it was read from, whichever this skill's
run layout provides.

```json
{
  "baseline": false,
  "comparedTo": "2026-09-01_09-00",
  "competitors": [
    {
      "name": "",
      "new_pages": [],
      "removed_pages": [],
      "moved_pages": [{ "from": "", "to": "", "matchedOn": "title" }],
      "home_changes": [{ "field": "title", "before": "", "after": "" }],
      "services_changes": [],
      "ad_count_delta": 0,
      "new_ad_headlines": []
    }
  ]
}
```

## Worked example

Given tests/fixtures/snapshot-prev.json and snapshot-curr.json, the correct changes.json is:

  moved_pages:   /services/tech → /services/technology  (matchedOn: title)
  new_pages:     /case-studies/pharma
  removed_pages: (none)
  home_changes:  title "Acme Analytics" → "Acme Analytics — Regulated Data"

Wrong answers that indicate a rules violation:
  - /services/tech listed as removed AND /services/technology as new  (missed title match)
  - /about-us listed as changed                                        (trailing-slash normalization failed)
