# Diff rules

These rules turn two snapshots (previous run + current run) into `changes.json`. Follow them
literally and in order. The diff step has no script — you are the diff engine — so treat this
file as an algorithm, not a suggestion.

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

1. **Normalized URL match.** Same normalized URL in both snapshots → same page.
2. **Exact `title` match.** If no URL match, look for a previous page and a current page with
   byte-for-byte identical `title`. If exactly one such pair exists → same page.
3. **Exact `h1` match.** If no URL or title match, same rule using `h1` instead.

A page matched by title or h1 with a **different** normalized URL is a **moved** page. Never
report it as a removed page plus a new page — that is the specific failure mode this rule
exists to prevent.

Any previous-snapshot page left unmatched after all three rules is **removed**. Any
current-snapshot page left unmatched after all three rules is **new**.

If a title or h1 match is ambiguous (more than one candidate pair ties), do not guess: fall
through and treat the pages involved as unmatched (removed / new) rather than moved, and note
the ambiguity in Data notes.

## 3. Emit exactly these change kinds

The diff produces exactly seven fields per competitor, no more:

- `new_pages` — normalized-unmatched current pages (report original `url`).
- `removed_pages` — normalized-unmatched previous pages (report original `url`).
- `moved_pages` — title/h1-matched pages with a changed URL: `{ "from", "to", "matchedOn" }`,
  where `matchedOn` is `"title"` or `"h1"`.
- `home_changes` — changes to `home.title`, `home.h1`, or `home.metaDescription` only, one
  entry per changed field: `{ "field", "before", "after" }`.
- `services_changes` — for pages matched (by any rule in §2) on both sides with `kind:
  "services"`, changes to that page's `title` or `h1` only, one entry per changed field per
  page: `{ "url", "field", "before", "after" }` (`url` = the current-snapshot normalized URL).
- `ad_count_delta` — `current.linkedinAds.count - previous.linkedinAds.count` (integer, may be
  negative).
- `new_ad_headlines` — `headline` values present in `current.linkedinAds.ads[]` whose
  `headline` does not appear in `previous.linkedinAds.ads[]`.

## 4. Report nothing else

`text` fields (home or page) are model-summarized on every run and are never diffed or
reported — a difference in `text` wording is not evidence of a real change on the competitor's
site. `headings`, `metaDescription` on subpages, `source`, `kind`, and screenshot paths are
never diffed. If it is not one of the seven fields in §3, it does not go in `changes.json` and
it does not go in the briefing.

## 5. Baseline runs

If there is no previous snapshot for a competitor (first run, or no prior run found), do not
diff. Write `changes.json` for that competitor as `{"baseline": true}` in place of the normal
per-competitor object, and say "baseline run" in the briefing instead of listing changes.

## 6. Schema drift guard

Before diffing a competitor, confirm both the previous and current snapshot objects carry every
top-level key listed in `snapshot-schema.json` (`name`, `url`, `fetchedAt`, `tier`, `home`,
`pages`, `linkedinAds`, `screenshots`, `errors`). If the previous snapshot is missing any of
these keys, treat this run as a baseline for that competitor (per §5) instead of diffing, and
record the reason in Data notes (e.g. "previous snapshot missing `linkedinAds` — treated as
baseline"). Never diff against a snapshot that doesn't match the current schema shape.

## `changes.json` shape

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
