---
name: campaign-report
description: "Generate a per-campaign marketing performance report (pipeline + content + funnel) for the board: a two-funnel (New Business / Account Management) HubSpot analysis built from a manual lead sweep reconciled three ways, destination-dated conversions (monthly counts, quarterly and YTD rates), GA4 traffic on one unified campaign page set, edition-over-edition deltas, and a board key takeaway. Markdown source + self-contained HTML; optional gated publishing step. Use when the user says \"/campaign-report\", \"campaign performance report for [campaign]\", \"build the [X] campaign report\", or wants one campaign's marketing and pipeline performance packaged for leadership. NOT the monthly board snapshot (marketing-monthly) and NOT the company-wide RevOps diagnostic (pipeline-analysis). Company, CRM ids, page sets, templates, and publishing targets come from a client context pack chosen per run; nothing client-specific lives in this skill."
---

# campaign-report — per-campaign performance report

Produces, for **one campaign** over a period (default: YTD): a **markdown source**, a self-contained
**HTML report** in the client's design system, and, when the pack defines a target and the owner
says go, **ships it**. Funnel metric definitions are `pipeline-analysis/definitions.md`; do not
redefine them here.

**Paths.** `references/…` is relative to this skill's folder. Every output, template, and
publishing path comes from the client pack, never from the current directory.

## Step 0 — Client context (every run, ask before reading)

1. List candidate packs: `references/*-context.local.md` here and in the sibling
   `pipeline-analysis/references/`, plus anything in the launch directory that looks like campaign
   context (a campaign README, a content plan, an earlier `*-performance-*.md`). Filenames only.
2. Ask one question: use this pack / point me elsewhere / paste the essentials / start with none.
   Wait.
3. Read only what was approved. "None" means Step 1 also collects portal id, funnels, GA4 property,
   and output path, and the run renders in the neutral default style.
4. No pack yet? Copy `pipeline-analysis/references/context-pack.TEMPLATE.md` to
   `references/<client>-context.local.md`, fill it with the user, verify ids live, continue.

## Critical rules

1. **No fabrication.** Every number traces to a CRM or analytics query. Empty result → say so.
2. **Attribution = the manual sweep is the source of truth.** There is no clean campaign tag on
   tickets or deals. The report owner (or Sales) provides the authoritative lead list; the skill
   cross-checks each lead against the live CRM but never invents membership. A lead whose only deal
   is a different offering is excluded with an audit note.
3. **All campaign leads are marketing-attributed.** The channel split shows *how each lead
   arrived*; it is never a subdivision of attribution. No "marketing-attributable subset".
4. **Two funnels, never blended.** New Business and Account Management per the pack. AM is
   **flagged ⚑**, kept separable, and counts in the campaign roll-up but never in NB-only counts.
5. **MQL / SQL / Won-Lost** per `definitions.md`: MQL = an associated NB deal exists, counted by
   deal `createdate`; SQL = a main-pipeline deal at the SQL stage or later; Won/Lost across all
   pipelines by per-pipeline stage ids.
6. **Home currency only** (`amount_in_home_currency`).
7. **Association pulls are incomplete — reconcile three ways.** Ticket↔deal links are patchy in
   most portals. For every lead: (a) association pull, (b) deal-name / company search for unlinked
   deals, (c) the manual sweep. Never trust associations alone. Every broken link becomes a
   CRM-hygiene follow-up item; never fix associations in the live CRM without explicit approval.
8. **Destination-dated conversions.** Count a conversion in the period it *reaches* the stage.
   Show **monthly counts** and **quarterly/YTD rates only**; monthly rates can exceed 100% and
   mislead. Flag YTD as the reliable rate.
9. **One unified page set** per campaign for every content and traffic table. Search Console's
   relative-day tools cannot hit exact month boundaries; flag GSC as a separate cut.
10. **Shipping is gated and name-aware.** The report carries client and contact names. Confirm
    with the report owner before any push; a push is an outward action even behind a password.
11. **CRM numbers are directional, not absolute.** Say so in the footer.

## Workflow

### Step 1 — Intake (always ask)
In one message: **which campaign**; **period** (default YTD to end of last full month); **the
authoritative lead list** (CRM record links; offer to draft a candidate list for confirmation if
none is ready, but membership is the owner's call); **the campaign page set** (landing pages +
posts; confirm slugs against the pack).

### Step 2 — CRM pull + three-way reconcile
For each lead: pull the **ticket** (`subject, createdate, hs_pipeline, hs_pipeline_stage,
source_type, hubspot_owner_id`); pull **associated deals** (`dealname, pipeline, dealstage,
amount_in_home_currency, deal_currency_code, createdate, closedate, hs_is_closed_won, <SQL
stage-entry property>`); for every lead with no associated deal, run a **deal-name search**
(`dealname CONTAINS_TOKEN "<company>"`); record link status (linked / unlinked-but-found /
no-deal). Confirm Won/Lost stage ids per pipeline with a `GROUP BY pipeline, dealstage` if unsure.

> ⚠️ Raw record queries drop same-day upper-bound rows and can truncate at ~20–25 rows; use
> end-of-month bounds and reconcile against `DATE_TRUNC(createdate,'MONTH'), COUNT(*)` aggregates.

### Step 3 — Compute the funnel (small N, directly from the reconciled set)
Leads by ticket `createdate` month (deal-only records by deal `createdate`) · MQL by deal
`createdate`, NB vs AM kept separate · SQL = main-pipeline deals at SQL+ (often 0 early in a
campaign; say so plainly) · Won/Lost by `closedate` · open pipeline by stage (MQL-stage NB / AM vs
SQL-stage; Closed-Lost separately) · destination-dated monthly counts + quarterly/YTD rates ·
channel split by `source_type` family (events shown as "Events · <event>" when leads are generated
onsite; inbound; outbound; cross-sell/AM; referral). Before calling anything "deal-only", name-search
tickets too; a ticket can exist and be unlinked.

### Step 4 — GA4 content and traffic (unified page set)
Per page, period + de-duped YTD (`pagePath` in-list, `activeUsers`, `sessions`); de-duped monthly
aggregate via `yearMonth` (a per-page sum double-counts); pillar benchmark vs comparable pages when
relevant. Apply the pack's exclusions.

### Step 5 — Render markdown + HTML
Markdown → the pack's campaign report path (funnel, conversion, content, methodology, audit notes:
exclusions, unlinked-deal flags, page-set definition). HTML → copy the pack's reference campaign
report and swap the data; if none exists, build the first one from the structure below in the
neutral default style and register it in the pack as the reference. Links: deals `/0-3/<id>`,
tickets `/0-5/<id>`, pages `<website>/<path>`.

### Step 6 — Board key takeaway
One or two sentences of interpretation: cause → state → next action, and **who owns which open
decision**. It surfaces, it never decides strategy. Top-of-report banner, mirrored in the markdown.
Run `/copy-deslop` if it reads generic.

### Step 7 — Ship (only if the pack defines a target and the owner says go)
Follow the pack's publishing block exactly: file location and naming, metadata entry, build step,
commit, push, deployment verification. Respect any "never do X" line in it.

## Report structure (sections, in order)
1. **Header** — logo, "Campaign Report · Confidential", kicker, H1 + italic sub (period, sources),
   link to the campaign master file, pill-link to the previous edition.
2. **Key takeaway banner.**
3. **The pipeline this campaign is building** — 4 hero stats (Leads / MQL / SQL / Open pipeline)
   with edition-over-edition delta chips, then two callouts: a dry funnel one-liner (do not
   re-narrate the hero numbers) and a compact "what generated it" list of lead-gen artifacts.
4. **Pipeline value by stage** — MQL (NB + AM ⚑) vs SQL vs Closed-Lost, home currency, plus a
   **bridge table** for any material move since the previous edition (previous total → per-deal
   deltas → new total; "confirm with Sales" where a re-scope is undocumented).
5. **Conversion** — dual view behind a toggle: monthly counts table (hover tooltips name the
   accounts per cell) + quarterly/YTD rates, and the drop-out funnel (light accent = still live,
   red = terminally lost, chevrons for stage→stage and cumulative rates).
6. **Leads by channel** — channel bars in the accent colour (a ranking, not a funnel stage), a
   stage-key legend, then a **lead roster** grouped by channel with visible dividers between groups
   (account · journey · stage pill · deal value linking to the deal; `New · <Mon>` pill on new
   entries).
7. **Collapsed by default** (`<details>`): landing pages & pillar · content performance (sortable
   table: release date ↔ YTD traffic, sum row in `<tfoot>`, titles linking to live posts, author
   name + avatar from the CMS, publish dates from the CMS field not page markup) · traffic ·
   webinars.
8. **Data quality & technical notes** — open section immediately before the footer. Standing home
   for CRM findings (unlinked deals, sync gaps), each with a one-sentence recommendation the owner
   can share verbatim. Never at the top of the report.
9. **Methodology footer** (collapsed) — definitions, two-funnel note, colour key, association
   note, page-set definition, currency, sources, source-file pointer.

## Edition-over-edition conventions
- Deltas everywhere (hero chips, roster "New" pills, bridge table).
- Summary first and DRY; corrections live in the bridge, not in a top callout.
- The takeaway names owners of open decisions; it does not recommend high-stakes moves.
- Meta remarks (coverage, cross-check dates) go in hover info-pills or the footer, never as a
  visible intro paragraph. Info pills on every non-obvious metric; canonical ⚑ tooltip: "AM ⚑ =
  Account Management, existing-client expansion. Marketing-influenced and counted in this
  campaign's MQL total; the flag keeps the NB vs AM split visible. AM is a separate funnel and is
  never mixed into NB-only counts."
- Plain headlines ("State of the revenue pipeline"), no rhetorical ones.
- **Freeze + retitle:** when a new edition ships, retitle the previous one to its period in its
  `<title>`, H1, and metadata, tag it "frozen snapshot", and never edit it again.

## Colour semantics (defaults; the pack's design system overrides the values, not the roles)
Leads = ink · MQL = accent (NB light, AM dark) · SQL = gold · Won = green · Lost = red. Channel
bars use the accent, never the funnel greens or ambers. Use the pipeline's display name in the
body; keep raw ids in the footer.

## House style (defaults; the pack's §6 overrides)
Board-appropriate, candid, interpretive. No emoji unless asked. No "From X to Y" / "Beyond the X"
titles. Round headlines, full precision in detail. Client and contact names only inside the gated
report and the private source repo; de-identify elsewhere.
