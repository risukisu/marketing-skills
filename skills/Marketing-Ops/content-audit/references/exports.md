# Analytics exports

Phase 1 of a run uses the website alone. It ends by creating `RUN/ingest/` with a README listing the
exports below. The user drops files there whenever ready; the next `/content-audit` run on the same
folder loads them (Phase 2). Every layer is optional.

## What to export

Use one date window for all of them where possible (the last 3 or 12 full months).

| Layer | Path in the tool | File | Unlocks |
|---|---|---|---|
| Search Console | Performance > Search results > dates > Export > Download CSV | The ZIP, or `Pages.csv` and `Queries.csv` from it | Findability, branded demand, pages close to page one |
| GA4 | Reports > Engagement > Landing page > dates > (optional: add secondary dimension "Session default channel group") > Share this report > Download File > CSV | One CSV | Sessions and key events per page; channel mix for the distribution check |
| HubSpot | Contacts > filter (for example Create date in the window) > Export > properties "First page seen", "Lifecycle stage", "Original source", "Create date" > CSV | One CSV | First-touch contacts and lead-stage contacts per page |
| Google Ads | Insights and reports > Landing pages > dates > Download > CSV | One CSV | Paid clicks, cost and conversions per landing page |

## Limits to know

- **Search Console downloads stop at 1,000 rows.** On sites with more than about 800 pages, export
  the Pages tab once per section (+ New > Page > "URLs containing" `/blog/`, then the next section)
  and drop all files in; the loader merges them and keeps the larger row when sections overlap. Any
  export whose row count sits on a typical download limit (250, 500, 1,000, 5,000 …) is treated as
  truncated: pages missing from it are "not in the export", never zero, and the report says so.
- **Search Console hides anonymised queries**, so query totals are lower than page totals. The
  branded split is a share of visible queries.
- **GA4 key events** exist only if the property has them configured. With none, the conversion check
  falls back to HubSpot or is not assessed.
- **HubSpot "First page seen"** is the first tracked page view, often before the contact converts.
  It is first-touch evidence, not attribution. Contacts with no first page are counted as unmatched.

## How the loader works

```bash
python ~/.claude/skills/content-audit/scripts/ingest.py --run-dir RUN load
```

- Reads every `.csv`, `.tsv` and `.zip` in `RUN/ingest/`. Excel files are refused: save as CSV.
- Handles UTF-8, UTF-16 (Google Ads), comma, semicolon and tab delimiters, `#` comment headers
  (GA4), title lines above the header (Google Ads), `Total` rows, thousands separators, currency
  prefixes and `--` placeholders.
- Identifies each file by its columns and prints the column mapping it used plus the date window
  (read from the file, or `unknown`). Search Console's extra tabs (Countries, Devices, Dates,
  Search appearance) are ignored; Filters.csv supplies the date window.
- **Stops on a file it does not recognise** (exit code 3) and prints its columns. Then:
  `--source "file.csv=ga4_landing"` to force a kind, `--column "file.csv:Their column=sessions"` to map
  a column, `--skip file.csv` to ignore a file, `--window "gsc_pages=2025-08-01 to 2025-10-31"` to set
  an unknown window. Never guess a mapping; ask the user what the column means.
- **Never reads contact details.** From a HubSpot export it keeps only the page, lifecycle stage,
  original source and create date, aggregated per page. `exports.json` holds counts, not people.
- Joins every export to crawled pages by path (lower case, no query string, no trailing slash, host
  ignored). `analyze.py` prints a warning when under 70% of an export's volume matches crawled pages:
  usually a different host, a language folder, or a crawl that hit its cap.

## Window mismatches

If windows differ between layers, say so in the report limits and compare shares, not totals.
