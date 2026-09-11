# Pipeline metric definitions — source of truth

These rules are the single source of truth for `/pipeline-analysis`; `/campaign-report` and
`/marketing-monthly` point here instead of redefining metrics. The **rules** are generic and live
in this file. The **ids** (pipelines, stages, ticket stages, fields, targets, loss reasons) are
client configuration and live in the client's context pack (`references/<client>-context.local.md`
+ the `.local.json` engine files; template: `references/context-pack.TEMPLATE.md`). Keep the
engine (`compute_funnel.py`) and this file in sync when a rule changes.

---

## 1. Objects

- **Tickets** = the lead inbox. One ticket = one commercial-intent lead (an inquiry or a positive
  outreach response). Passive signals (ebook download, newsletter signup) are **not** tickets.
  Stages, per the pack: New · Waiting on them · Waiting on us · Qualified as MQL · Qualified as
  Prospect · Closed – no sales potential.
- **Deals** live in pipelines the pack assigns to funnels: New Business (net-new; one main pipeline
  plus, often, a parked/prospects pipeline) and Account Management (existing clients; renewals
  kept). Any archive pipeline is excluded entirely.
- **Loss reason:** a structured picklist field drives failure-mode classification; a free-text
  field is displayed as context only. Field names per the pack (HubSpot default names:
  `closed_lost_reason_select` and `closed_lost_reason`, but verify — portals rename them).
- **Currency:** always the CRM's home-currency amount (HubSpot `amount_in_home_currency`). Never
  hardcode an FX rate.

---

## 2. Two-plane model

The engine operates on two non-overlapping planes. **Lifecycle position and qualification outcome
are never conflated.**

**Flow plane** — *where* flow drops or slows. The lifecycle spine from Lead through Close, measured
at each gate: volume in → volume through → volume leaked, velocity, time-in-stage, throughput vs
target. Answers: "how many made it past each gate, and how fast?"

**Diagnosis plane** — *what kind of problem*, *whose*, and *how much money*. Every leak is a typed
exit event (gate, reason code, failure mode A–F, owner, value), rolled up into a leak P&L.
Answers: "what is breaking the funnel and who is accountable?"

Both planes are always computed and reported separately.

---

## 3. Failure-mode taxonomy

Every pipeline leak resolves to exactly one of these.

| # | Failure mode | Owner | Signal that reveals it |
|---|---|---|---|
| **A** | Marketing — volume | Marketing | Leads/month below the run-rate the revenue target needs |
| **B** | Marketing — quality/fit | Marketing | High lead volume, low Sales-Accept rate; leads rejected as not-ICP or no intent |
| **C** | Sales — execution/process | Sales | Accepted leads stall or die: slow response, no next step, weak presentation |
| **D** | Offer / market fit | Product/Strategy | Qualify fast, then lose at proposal for capability gap, wrong tool, competitor win |
| **E** | Commercial terms | Sales/Leadership | Lose at negotiation for price or budget resistance |
| **F** | Buying process / timing | external — track, don't blame | Real fit, stalls on the buyer's side (reorg, freeze, compliance, timeline) |

---

## 4. Sales-Accept gate (Gate 1)

The marketing→sales handoff, inferred from ticket stage. First gate in the New Business spine.

- **Accepted** = ticket reached Qualified-as-MQL or Qualified-as-Prospect.
- **Rejected** = ticket reached Closed–no potential. Reject rate is the primary **B** signal, sliced by lead source.
- **Pending** = ticket still in an open stage.

**NB only.** Account Management enters the funnel at Opportunity; AM has no Lead or Accept gate.

---

## 5. Reason map

The engine loads a JSON map of picklist **values** → failure mode + owner (`reason_map.json` ships
as a starter; the client's real map is `references/<client>-reason-map.local.json`, passed with
`--reason-map`). Adding rows needs no engine change.

- **Blank / "Other reason" / unknown value → Unattributed.** Never dropped; reported as its own row
  in the leak P&L. A post-acceptance Unattributed loss also feeds the C inference (§6).
- Ambiguous values carry `reclassifiable_to` and are flagged every run (the classic case: "Budget
  too small" defaults to F but is E when qualitative evidence shows price resistance).
- Retired picklist values stay in the map so they classify correctly if reactivated.

---

## 6. B and C are inferred (directional)

**B (marketing quality)** is inferred from the Gate-1 reject rate, sliced by source.

**C (sales execution)** is inferred from `execution_flags()`: open deals idle past a benchmark
window since their deepest stage entry (went-silent); post-acceptance losses coded blank or Other
(unexplained loss); accepted leads with no opportunity opened within the window (needs ticket↔deal
linkage; deferred when not pulled). Label every B and C figure "directional inference" until a
structured signal exists (a "Not responsive" loss reason in active use, a ticket reason picklist,
a sales retro).

---

## 7. Two-lens conversion

MQL→SQL velocity spans weeks to months. Monthly event counts and cohort conversion rates answer
different questions on the same deals. The engine computes both; **they are never blended**.

**Throughput view (vs target):** events by the month they happened — MQLs *created* in month M vs
MQL-target[M]; SQLs *converted* (first SQL entry) in month M vs SQL-target[M].

**Cohort view (true conversion rate):** of MQLs *born* in month M, the % that *ever* reached SQL,
tracked forward. Recent cohorts are flagged immature.

**Explicit ban:** never compute `SQLs-this-month ÷ MQLs-this-month`. Different cohorts, meaningless
rate.

---

## 8. Targets

`targets.json` shape: `{ "revisions": [ { "label", "effective_from", "set_by", "mql"[12], "sql"[12],
"leads": null, "won_eur_nb", "won_eur_am" } ] }`. The shipped file is empty; the client's targets
live in `references/<client>-targets.local.json` (`--targets`).

**Append-only.** A mid-year revision = append a new block; never edit old ones, so past reports
stay valid and any period can be re-run against any named revision (`--targets-revision`).

**Resolution:** the revision whose `effective_from` is the latest on or before the period end. The
resolved label is stamped into the report. No applicable revision → target lines are omitted.
`leads` is null by design: derived by the reverse-funnel (§9), not an input.

---

## 9. Reverse-funnel goal-seek

Back-solves the volume required at each stage to hit the NB revenue target, using measured
**cohort (matured) rates**, never throughput ratios:

```
revenue target ÷ avg won-deal size → required Won
               ÷ SQL→Won rate      → required SQLs
               ÷ MQL→SQL rate      → required MQLs
               ÷ accept→MQL rate   → required accepted leads
               ÷ Sales-Accept rate → required Leads
```

Avg won-deal size comes from a trailing window of NB won deals; flag low confidence when n < 5
(widen the window first). `avg_deal_override` in the input JSON overrides it. Derived volumes are
the reference the **A** diagnosis measures against until explicit volume targets exist. **NB only.**

---

## 10. Scope

**New Business — primary, full diagnostic:** flow plane, diagnosis plane, cohort conversions,
throughput vs target, velocity, sources, reverse-funnel, verdict (binding constraint + owner + value).

**Account Management — condensed secondary:** top-line volume, realized won revenue, its own target
when provided. No goal-seek, no verdict. Enters at Opportunity.

Both appear in one report and are **never blended**: NB and AM are never summed into a single
MQL/SQL/revenue figure. Different teams own each funnel.

---

## 11. Data quality

CRM numbers are **directional, not absolute**: manual deal entry, attribution gaps, and field
quality mean the engine's outputs are diagnostic signals, not accounting figures. Never present as
exact; every figure traces to a query or is labeled inferred. Cross-reference the report owner
when precision matters.

---

## Supplementary definitions

### Lead (ticket)
Count by `createdate` month. Cohort outcome = terminal ticket stage: → MQL / → Prospect
(qualified-but-parked, **not** a loss) / → Closed–no potential / still open.

### MQL (deal-based)
A **New Business deal**, counted in the month of its **deal `createdate`** (when first logged as
qualified). Includes the parked/prospects pipeline when the pack says so.
- **Use `createdate`, not the stage-entry property.** Stage-entry re-stamps on every re-entry, so a
  revived deal gets a false recent date. `createdate` is stable across pipeline moves. *(The single
  most important rule.)*
- **Exclude:** renewals / existing business (`dealtype = existingbusiness` or "renewal" in the
  name); sub-deals of an already-counted opportunity (human-confirmed); deals created before the
  period.
- **Plus:** qualified-as-MQL tickets with no NB deal — surfaced as a flagged reconciliation line,
  attributed by the ticket's qualification month.
- **Revival rule:** a deal MQL'd in a prior year, parked, and revived keeps its original
  `createdate` and stays a prior-year MQL. First-MQL date always beats revival date.

### SQL (deal-based)
A deal that entered the SQL stage or beyond in the **main** NB pipeline (parked-pipeline deals
carry their own stages; a parked MQL that gets serious is moved into the main pipeline). Use the
**first** SQL entry for "reached SQL" and for velocity; re-entries count once and are flagged.

### Won / Lost / Revenue
Won = the signed stage; Lost = the closed-lost stage, **classified across all pipelines by
per-pipeline stage ids** (a Closed-Lost in a secondary pipeline is a loss, not in-flight).
Attributed by `closedate` month. Revenue = home-currency amount of won deals. Open pipeline value =
open deal amounts by stage, per funnel.

### Time-to-convert
Ticket→MQL = ticket `createdate` → deal `createdate`. MQL→SQL = deal `createdate` → first SQL entry.
SQL→Won = first SQL entry → won date. Report median + mean + range; flag >90-day dormant or
reactivated outliers separately.

### Sources
Ticket `source_type`, grouped per the pack (inbound · outbound family · event · referral · AM).
Volume + conversion-to-MQL per source; accept rate by source is the B signal.
