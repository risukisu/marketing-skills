# Deriving the offering map

The offerings are what the site says the company sells, read from the site as a whole. They are
proposed by you, confirmed by the user, and only then used to classify pages. A wrong offering list
spoils every number after it, so this step has a gate.

## Read

1. `site_profile.md` (homepage title, H1, H2s, text, navigation labels, offering-type pages, URL
   sections, page-type counts, about-page excerpt).
2. For each candidate offering, its main page in `crawl.json` (title, H1, H2s, excerpt). Fetch the
   live page only if the excerpt is empty.
3. Approved context from Step 0 (a positioning doc, the user's marketing audit). It may name
   offerings the site does not show; note the difference, it is a finding.

## Decide

- **An offering is something a buyer can buy**: a service line, a product, a package. Not a topic,
  an industry served, or a technology used. Industries and audiences belong in `icp`, not in the list.
- **2 to 8 offerings** on most sites. Merge pages that sell the same thing under different names.
  Split only when the buyer, the problem or the purchase differ.
- **Name it the way the site does.** If the navigation says "Data platforms", use that, not a
  rewrite.
- **Write boundary rules.** `includes` and `excludes` decide the pages that could go either way
  (for example: a "forecasting accuracy" post belongs to forecasting, not to data platforms).
- **Record what the site states, verbatim**: `positioning` (the homepage claim as written) and `icp`
  (who the site says it serves). Quote; do not improve.
- **Brand terms**: the company name, product names and common misspellings, lower case. They split
  search queries into branded and non-branded demand.

## Write `taxonomy.json` (with `"confirmed": false`)

```json
{
 "company": "Example Co",
 "positioning": "verbatim homepage claim",
 "icp": "who the site says it serves, verbatim where possible",
 "brand_terms": ["example co", "exampleco"],
 "offerings": [
  {"id": "data-platform", "name": "Data platforms",
   "definition": "One sentence: what the buyer gets.",
   "includes": ["topics and page kinds that belong here"],
   "excludes": ["near-miss topics that belong elsewhere"],
   "evidence": ["/services/data-platform", "/"],
   "main_pages": ["/services/data-platform"]}
 ],
 "confirmed": false,
 "confirmed_note": ""
}
```

`id` is lower-case kebab-case and never `cross`, `brand` or `none` (reserved).

## Confirm (the gate)

Ask one question and wait. Show a compact table, then the choices:

> **Here is the offering map I read from the site. Classification starts once you confirm it.**
>
> | # | Offering | What the buyer gets | Main page | Evidence |
> |---|---|---|---|---|
> | 1 | Data platforms | … | /services/data-platform | nav label, homepage H2 |
>
> Positioning as stated: "…". ICP as stated: "…". Brand terms: …
>
> 1. Confirm as is
> 2. Edit (rename, merge, split, add or drop an offering, or change the boundaries)
> 3. Add context I missed (an offering that is sold but not on the site goes in as a gap)

Apply edits, show the changed rows once more only if the user restructured the list, then set
`"confirmed": true` and record the answer in `confirmed_note`. Run
`check_labels.py --run-dir RUN taxonomy`; it refuses an unconfirmed taxonomy.

An offering the user names that has no page on the site stays in the list with `"evidence": ["user"]`
and `"main_pages": []`. Every one of its cells will show as missing, which is the point.
