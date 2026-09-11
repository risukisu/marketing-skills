---
name: pipeline-analysis
description: "Run a HubSpot RevOps pipeline and conversion analysis over a period (a quarter, a year, a custom or trailing range) and return a diagnosis-first report: verdict (binding constraint A–F with owner and value), reverse-funnel scorecard, New Business full diagnostic (flow plane, diagnosis plane, cohort conversion, velocity, sources), Account Management condensed, reconciliation, method note. Markdown by default; HTML on request. Use when the user says \"/pipeline-analysis\", \"run a pipeline analysis\", \"revops analysis\", \"conversion analysis for [period]\", or asks how leads, MQLs, and SQLs converted over a period. NOT the monthly board snapshot (that is marketing-monthly) and NOT a single campaign's report (that is campaign-report). Company and CRM ids come from a client context pack chosen per run; nothing client-specific lives in this skill."
---

# pipeline-analysis — RevOps funnel & conversion analysis

A deterministic engine (`compute_funnel.py`, stdlib only) plus a reporting workflow. Read
**`definitions.md`** (same folder): it is the source of truth for every metric. `campaign-report`
and `marketing-monthly` point at it rather than redefining metrics.

**Paths in this file.** `compute_funnel.py`, `definitions.md`, `references/…` are relative to
**this skill's folder**. Output paths come from the client pack, never from the current directory.

## Step 0 — Client context (every run, ask before reading)

The skill holds no company or CRM data and never uses any without the user's say-so.

1. List the candidate packs: `references/*-context.local.md` in this skill's folder (machine-local,
   never shipped), plus anything in the launch directory that looks like reporting context
   (`CLAUDE.md`, `AGENTS.md`, a `context/` folder, files named for pipeline, funnel, targets, or
   earlier `*-pipeline-conversion-analysis.md` reports). Filenames only; read nothing yet.
2. Ask one question: use this pack / point me at another file / paste the ids / start with none.
   Wait.
3. Read only what was approved. A pack supplies portal id, pipeline→funnel mapping, stage ids,
   ticket stages, AM sources, targets, reason map, output root, house style. "None" means Step 1
   must collect the ids by hand and the run stops at markdown with generic labels.
4. **No pack for this company yet?** Copy `references/context-pack.TEMPLATE.md` to
   `references/<client>-context.local.md`, fill it with the user *verifying every id against the
   live portal* (`SELECT pipeline, dealstage, COUNT(*) FROM DEAL GROUP BY pipeline, dealstage`
   is the fastest way), and create the three `.local.json` engine files it describes. Then continue.

## Critical rules
1. **No fabrication.** Every number traces to a query. Empty result → say so.
2. **MQL month = deal `createdate`**, never the stage-entry property (it re-stamps on re-entry).
3. **Two-plane model:** flow (where volume drops or slows) and diagnosis (which failure mode A–F,
   whose, how much). Always computed and reported separately.
4. **NB primary, AM condensed.** New Business gets the full diagnostic; Account Management gets
   top-line + realized revenue + its own target when provided. No goal-seek, no verdict for AM.
5. **Loss reason from the structured picklist**, mapped to A–F via the client's reason map.
   Free-text reason is context only.
6. **Two-lens conversion, never blended.** Throughput (events by month vs targets) and cohort
   (of deals born in month M, the % that ever progressed). Never divide this month's SQLs by this
   month's MQLs.
7. **Targets are versioned**, append-only, effective-dated. The resolved revision is stamped in
   the report.
8. **Reverse-funnel derives lead volume** from the revenue target and measured cohort rates. No
   external lead target exists by design.
9. **Two funnels, never blended.** NB excludes renewals; AM keeps them. Archive pipelines out.
10. **Won/Lost across all pipelines** by per-pipeline stage ids. SQL uses first entry; re-entry
    flagged, not modeled.
11. **Home currency only** (`amount_in_home_currency`).
12. **Flag, don't hide.** Renewals, sub-deal candidates, prior-period re-entries, cross-period
    leads, ticket-only MQLs surface in a reconciliation block; sub-deals get human confirmation
    before exclusion.
13. **CRM numbers are directional, not absolute.** Say so in the method note.

## Workflow

### Step 1 — Intake (always ask)
Ask, in one message: the **period** (a quarter, a year, a custom range, or trailing-to-today).
Resolve to `start`/`end` ISO dates. Both funnels are always produced.

### Step 2 — Pull data (HubSpot MCP)
Call `mcp__claude_ai_HubSpot__tool_guidance(["query_crm_data"])` once first. Substitute every id
from the pack.

**Deals created in period, both funnels' pipelines**, filtered by `createdate`. NB uses the main
pipeline's stage-entry properties; AM uses its own (`hs_v2_date_entered_<stageId>`). Normalize both
into generic `mql_entry` / `sql_entry` / `proposal_entry` / `nego_entry` / `won_entry` in Step 3.
```
SELECT hs_object_id, dealname, pipeline, dealtype, createdate,
  <stage-entry properties for this funnel>, closedate, dealstage,
  amount_in_home_currency, deal_currency_code,
  <loss-reason picklist>, <loss-reason free text>
FROM DEAL WHERE pipeline IN (<funnel pipelines>) AND createdate BETWEEN '<start>' AND '<end-of-month>'
```

> ⚠️ **Data-pull gotchas, verified on live portals:**
> 1. Raw record queries silently drop *same-day* upper-bound rows and can truncate at ~20–25 rows
>    with no pagination note. Always reconcile against
>    `SELECT DATE_TRUNC(createdate,'MONTH'), pipeline, COUNT(*) FROM DEAL ... GROUP BY ...`
>    (aggregates include same-day) and use end-of-month bounds; fetch any deal the GROUP BY shows
>    but the raw pull missed.
> 2. Won/Lost stage ids are per pipeline. Confirm with
>    `SELECT pipeline, dealstage, COUNT(*) FROM DEAL GROUP BY pipeline, dealstage`.
> 3. Some stage-entry properties (stage ids that are UUIDs) are rejected by the SQL layer. Set that
>    entry to `null` and note the gate undercount in the report; won deals still pass every gate.
> 4. The reporting API allows at most two GROUP BY dimensions.

Also pull deals whose **stage entry** is in-period but whose `createdate` is before it: prior-period
re-entries the engine flags.

**Trailing-window won deals** for avg deal size when in-period wins are sparse (n < 5): widen to
18–24 months; flag low confidence if still n < 5.

**Tickets created in period** from the lead-inbox pipeline: `hs_object_id, createdate, closed_date,
source_type, hs_pipeline_stage, subject`, `ORDER BY createdate ASC LIMIT 500` (stable, complete).
Reconcile against month×stage and source×stage GROUP BYs before trusting the enumeration. Split NB
vs AM tickets by the pack's AM sources.

**Ticket→MQL velocity** needs each deal's originating-ticket `createdate`: pull deal↔ticket links
via the cross-object query (`... FROM DEAL WHERE ... AND associations.TICKET IS NOT NULL`) and carry
the earliest ticket `createdate` onto each deal as `ticket_createdate`. AM deals usually have none;
that is legitimate.

### Step 3 — Normalize → JSON → compute
Write `pa_input.json` to the scratchpad:
- **deals:** `id` (string), `name`, `pipeline`, `createdate`, `stage`, `amount_home`, `currency`,
  `dealtype`, the five generic entry dates, `ticket_createdate` (or null), `loss_reason` (picklist
  value), `loss_desc` (free text).
- **tickets:** the reconciled enumeration (`id, createdate, closed_date, source_type, stage,
  subject`). Fallback `[]` only if it will not reconcile; the ticket-side tables then come straight
  from the GROUP BYs.
- **top level:** `period`, `generated`, `manual_excludes` (filled in Step 4). Optional:
  `targets_revision`, `avg_deal_override`, `sql_reentry`. The `crm` and `funnels` blocks may be
  inlined here or supplied with `--config`.

Run the engine with the client's files:
```
python compute_funnel.py <scratch>/pa_input.json <scratch>/pa_out.json \
  --config    references/<client>-config.local.json \
  --targets   references/<client>-targets.local.json \
  --reason-map references/<client>-reason-map.local.json
```
Output: `{period, generated, targets_revision, funnels: {nb: {...verdict}, am: {...}}}`. NB carries
`flow_gates / accept_gate / mql_cohorts / funnel / leak_events / leak_pnl / execution_flags /
conversions / throughput / throughput_vs_target / velocity / ticket_cohorts / sources / flags /
reverse_funnel / verdict`; AM the non-diagnostic subset. Tests: `python test_compute_funnel.py`
(run them if you touch the engine).

### Step 4 — Confirm candidate exclusions
Show `flags`: renewals, **sub-deal candidates**, prior-period re-entries, ticket-only MQLs.
Sub-deal exclusion is human-confirmed: ask which ids go into `manual_excludes`, re-run Step 3.

### Step 5 — Write the markdown report
Save to `<output root from pack>/<period>-pipeline-conversion-analysis.md`. Every number from
`pa_out.json` (deal side) or the Step-2 GROUP BYs (ticket side). Diagnosis-first structure:

1. **Verdict header** — on/off track for the revenue and MQL/SQL targets; the binding constraint
   (A–F) with owner and value; targets-revision label. NB only.
2. **Reverse-funnel scorecard** — required vs actual per stage + year-end projection. Low-confidence
   flag on avg deal size when n < 5. Derived requirements labeled directional.
3. **New Business (full)** — flow plane (spine with per-gate in/through/leaked, velocity,
   time-in-stage, throughput vs target); diagnosis plane (leak P&L by A–F with owner; loss-reason
   breakdown with free text as context; C-inference flags labeled hypothesis; a qualitative
   callout slot for sales-retro findings); conversion (cohort rates to maturity, immature cohorts
   flagged); velocity (median/mean/range, outliers flagged); sources (volume, accept rate, MQL
   conversion by source).
4. **Account Management (condensed)** — top-line, realized won revenue vs AM target if any. No
   verdict. Note that AM enters at Opportunity.
5. **Reconciliation & flags** — exclusions applied; ambiguous reason values; Unattributed bucket;
   SQL re-entries; cross-period leads; ticket-only MQLs; zero-amount deals; targets stamp.
6. **Method note** — deal side = engine over the full set; ticket side = GROUP BYs; stage→pipeline
   mapping verified empirically; inference caveats; CRM-is-directional statement.

De-identify to company level unless the pack's house style says otherwise.

### Step 6 — HTML (only when asked)
Render the markdown with the pack's style template. The leads→client master funnel has **two
views behind a pill toggle**, default **Conversions**, second **+ Drop-out**, never a third:
- **Conversions:** six stages (Leads → Accepted → MQL → SQL → Opportunity → Client), sequential
  bars deepening down the funnel with the won terminal in the pack's success colour, counts in ink
  beside bars (never inside coloured bars), faint ribbons between stages, per-boundary chevrons for
  next-step and cumulative rates, each header with a "?" hover tip (definition + example).
- **+ Drop-out:** same bars plus a thin secondary row splitting exits into still-live (light
  accent, can still convert) and terminally lost (red), each with an inline label. Legend in this
  view only. Still-live + lost + won must reconcile to the top-of-funnel count.
Toggle is vanilla JS on the `hidden` attribute. Reuse the block across periods; don't redesign.

## Notes
- The five calibration decisions (two funnels, all-pipeline won/lost, SQL first-entry,
  full-lifecycle cohort conversion, AM-deal handling of ticket-only captures) and the two-plane
  diagnostic model are baked into the engine and `definitions.md`.
- `marketing-monthly` stays independent; the pack owner watches definition drift by hand.
