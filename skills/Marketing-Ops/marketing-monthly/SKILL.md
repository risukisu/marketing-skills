---
name: marketing-monthly
description: "Generate the monthly marketing board snapshot for a company: headline metrics (pipeline value, MQL, leads, web traffic) vs the prior month, quarter progress vs targets with YTD sparklines, traffic by campaign, what-we're-learning insights, and a per-lead journey section, as a self-contained HTML report plus a markdown companion. Use when the user says \"/marketing-monthly\", \"monthly board report\", \"marketing monthly\", \"marketing snapshot for [month]\", or asks for the next edition of the board-prep marketing report. NOT a single campaign's report (campaign-report) and NOT the RevOps diagnostic (pipeline-analysis). Company, CRM ids, GA4 property, templates, and output paths come from a client context pack chosen per run; nothing client-specific lives in this skill."
---

# /marketing-monthly — monthly board snapshot

You are producing the marketing page of a board pack. Within a company, the format, queries,
definitions, and exclusions are **locked** across editions: only the narrative and the lead journeys
change month to month. Metric definitions come from `pipeline-analysis/definitions.md` (sibling
skill in this library); do not redefine them here.

**Paths.** `references/…` is relative to this skill's folder. Output and template paths come from
the client pack, resolved from the pack — never from the current directory (the skill is often
launched from a workspace root, not from the reporting repo).

## Step 0 — Client context (every run, ask before reading)

1. List candidate packs: `references/*-context.local.md` here and in the sibling
   `pipeline-analysis/references/` (one pack serves all three reporting skills), plus anything in
   the launch directory that looks like reporting context or an earlier
   `*-monthly-marketing-snapshot.md`. Filenames only.
2. Ask one question: use this pack / point me elsewhere / paste the essentials / start with none.
   Wait.
3. Read only what was approved. "None" means the run collects portal id, pipelines, GA4 property,
   and output path by hand and renders a first edition in the default style (below).
4. No pack yet? Copy `pipeline-analysis/references/context-pack.TEMPLATE.md` to
   `references/<client>-context.local.md`, fill it with the user, verify ids live, continue.

## Critical rules

1. **Don't fabricate.** Every number cites a CRM or analytics query. Empty query → say so.
2. **Home currency only** — HubSpot `amount_in_home_currency`. Never hardcode FX.
3. **SQL and MQL follow the pack's funnel definitions**: SQL = main New Business pipeline at the
   SQL stage or later; MQL = any New Business deal (main + parked pipelines) by deal `createdate`.
   Account Management is never summed into the board's MQL/SQL.
4. **Standing exclusions from the pack** (reseller pass-through deals, renewals) come out of the
   totals and go into a callout below the headline table, tagged `Excluded` in lead paths.
5. **Format is locked within a style.** Pick the style in Step 1; never redesign the template ad
   hoc. Month-over-month consistency is the point of a board series.
6. **Leads are described by channel, never as a "marketing-attributable" subset.** Marketing
   influences nearly every channel (outbound works off content, expansions follow campaign
   assets). Name marketing's contribution per lead in the journey notes; never total it.

## Workflow

### Step 1 — Style, then period
- **Style:** if the pack lists templates, ask which one (AskUserQuestion). If none exist, this
  run builds the first template from the section spec below in a neutral editorial style (paper
  background, one serif display face, one humanist sans, single accent colour) and saves it to
  the pack's template path for every later edition.
- **Period:** the "Current" month (default: current calendar month, truncated to today if
  mid-month); comparison = prior full month. Confirm the quarter's MQL and SQL targets from the
  pack; ask if they changed.

### Step 2 — Pull data
Substitute every id from the pack.

**Deals, New Business pipelines, current + prior month**, by `createdate`:
`search_crm_objects(objectType="deals", filters: pipeline EQ <id>, createdate GTE/LT <epoch ms>;
properties: dealname, dealstage, amount, deal_currency_code, amount_in_home_currency, createdate,
hubspot_owner_id)`. Repeat per NB pipeline and per month.

**Tickets, all pipelines, current + prior month**: `subject, createdate, source_type,
hs_pipeline_stage, content`.

**YTD per month** (sparklines): ticket counts per month; NB deals per month with MQL = all created,
SQL = subset at SQL stage or later.

**GA4 site-wide traffic**: `run_report(property_id=<pack>, date_ranges=[current, prior],
metrics=[sessions, totalUsers, engagedSessions, screenPageViews],
dimensions=[sessionDefaultChannelGroup])` plus a `month` breakdown Jan→today for the sparkline.
Apply the pack's site-wide exclusions.

**Per-campaign traffic**: for each campaign page set in the pack, `pagePath` in-list filter, same
two date ranges. One unified set per campaign; never split a campaign the pack defines as one.

### Step 3 — Describe leads by channel

| Channel | Definition |
|---|---|
| **Form inbound** | `source_type` = Inbound or form. The cleanest signal; headline sub-metric for # Leads ("X form inbound") |
| **LLM self-attributed** | Sales noted the lead found the company via an AI assistant; name the assistant |
| **Reply to a campaign send** | Ticket originated from a launch nurture or blast; name the touch |
| **Outbound** | `source_type` = Outbound; surface content or assets referenced in the body |
| **Client referral** | `source_type` = referral |
| **Account continuation** | Cross-sell with no campaign trigger |

Never write "N marketing-attributable vs M other" or "only inbound counts as a marketing win".

### Step 4 — Build the report
Copy the chosen template to `<output root>/YYYY-MM-monthly-marketing-snapshot.html`. Replace data
only; keep CSS, DOM, and section order.

Sections, in order:
1. **H1** "Marketing Monthly — <Month YYYY>" + italic sub "<period> vs <comparison>".
2. **Headline table** — 4 rows × 5 cols (Metric · Current · Last · M/M · Notes): SQL value in home
   currency · # MQL · # Leads (sub-metric "X form inbound") · Website traffic (sessions, users,
   engaged).
3. **Exclusions callout** if a standing exclusion landed this period.
4. **Quarter progress table** — month columns · quarter-to-date · target · % to target · YTD
   sparkline · status. Rows: MQL, SQL, Leads.
5. **Sparklines** — inline SVG 140×38, smooth Bézier (Catmull-Rom → cubic), current quarter
   shaded, accent dot on the current month, tiny Q1–Q4 labels at the base, no month letters.
6. **Traffic by campaign** — compact table, page paths as links to `<website>/<path>`.
7. **What we're learning** — 4–6 numbered insights, each opening with a bold name-the-pattern
   phrase. No self-deprecation; unconverted leads are described, not framed as failure.
8. **Lead paths — <Month>** — every ticket and every NB deal of the current month, grouped by
   channel: account link, role/context, journey narrative, stage tag. Current month only.
9. **Methodology footer** — definitions, currency note, exclusions, comparison basis, sparkline
   source values, generated date.

### Step 5 — Hyperlink everything
Deals → `<record URL pattern>/0-3/<id>`; tickets → `/0-5/<id>`; campaign pages → `<website>/<path>`.
Links in the template's ink colour with a dotted underline, never browser blue; wrap in
`<a target="_blank">`.

### Step 6 — Companion markdown
Same content as `.md` at the same path. Frontmatter: title, period, comparison, data sources,
generated, purpose, sql-definition, mql-definition, excluded, portal id, UI domain.

### Step 7 — Verify before declaring done
Spot-check 2–3 deal amounts in the CRM UI; verify sparkline values against the YTD query; confirm
exclusions applied; click every campaign link; open the HTML in a browser. Then hand to the pack's
report owner for narrative review.

## House style (defaults; the pack's §6 overrides)
Editorial, board-appropriate, candid. Round headline numbers (166K), full precision in callouts.
No emoji unless asked. No "From X to Y" or "Beyond the X" titles. Run `/copy-deslop` on the
narrative if it reads generic.

## Open questions to raise at the start of every run
Have the quarter targets changed? Is there a Leads target or a Lead→MQL rate target yet? Any
attribution only Sales knows about (an LLM referral, a conference conversation) to fold into the
lead paths before drafting?
