# <Client> — RevOps reporting context pack

> Copy this file to `references/<client>-context.local.md` (the `.local.md` suffix keeps it out of
> git) and fill every `<...>`. One pack per client. `/pipeline-analysis`, `/marketing-monthly`, and
> `/campaign-report` all read this same pack, so a CRM id is defined once. Values marked *verify*
> must be confirmed against the live portal before the first run — pipeline and stage ids differ
> per HubSpot portal and are not guessable.

## 1. Identity

| Item | Value |
|---|---|
| Company | `<name>` |
| Website | `<https://...>` (used for campaign-page links) |
| Report owner / reviewer | `<role, e.g. Head of Marketing>` — the person who signs off before anything is shared |
| Board / audience register | `<who reads the reports and how candid the tone should be>` |
| Home currency | `<EUR / USD / ...>` — always HubSpot `amount_in_home_currency`, never a hardcoded FX rate |

## 2. HubSpot

| Item | Value |
|---|---|
| Portal id | `<digits>` |
| UI domain | `app.hubspot.com` or `app-eu1.hubspot.com` |
| Record URL pattern | `https://<ui-domain>/contacts/<portal>/record/0-3/<dealId>` (deals) · `/record/0-5/<ticketId>` (tickets) |
| Lead inbox = ticket pipeline id | `<hs_pipeline>` *verify* |
| Ticket stages | new `<id>` · waiting-on-them `<id>` · waiting-on-us `<id>` · qualified-MQL `<id>` · qualified-prospect `<id>` · closed-no-potential `<id>` *verify* |
| Ticket sources that mean existing-client work (AM) | `<source_type values, e.g. Cross-sell, client_referral>` |
| Loss-reason fields | picklist `closed_lost_reason_select` (drives classification) · free text `closed_lost_reason` (context only) — *verify the field names in this portal* |

### Deal pipelines → funnels (*verify all ids*)

| Funnel | Pipeline ids | MQL stage | SQL+ stages | Won | Lost | Renewals |
|---|---|---|---|---|---|---|
| New Business (full diagnostic) | `<id>`, `<parked/prospects id>` | `<stage>` (= deal `createdate`) | `<stage ids from qualified onward>` | `<per pipeline>` | `<per pipeline>` | excluded |
| Account Management (condensed) | `<id>`, `<id>` | `<stage>` | `<stage ids>` | `<per pipeline>` | `<per pipeline>` | kept |
| Excluded entirely | `<archive id>` | | | | | |

Stage-entry property names for the AM pipeline (HubSpot names them `hs_v2_date_entered_<stageId>`): MQL `<...>` · SQL `<...>` · Won `<...>`.

Known quirks to carry into every report: `<e.g. a stage-entry property the SQL layer rejects; a pipeline whose captures should count as MQL; a reseller pass-through deal type to exclude>`.

### Engine config (paste into `pa_input.json` or keep as `references/<client>-config.local.json`)

```json
{
  "crm": {
    "ticket_stage_mql": "<id>",
    "ticket_stage_prospect": "<id>",
    "ticket_stage_closed": "<id>",
    "ticket_stages_open": ["<id>", "<id>", "<id>"],
    "am_sources": ["<source_type>", "<source_type>"]
  },
  "funnels": [
    {"key": "nb", "name": "New Business", "pipelines": ["<id>", "<id>"],
     "sql_plus": ["<stage>", "<stage>", "<stage>", "<won stage>"],
     "won": ["<stage per pipeline>"], "lost": ["<stage per pipeline>"], "exclude_renewals": true,
     "gates": [{"name": "Opportunity", "entry": "createdate"}, {"name": "SQL", "entry": "sql_entry"},
               {"name": "Proposal", "entry": "proposal_entry"}, {"name": "Negotiation", "entry": "nego_entry"},
               {"name": "Close", "entry": "won_entry"}]},
    {"key": "am", "name": "Account Management", "pipelines": ["<id>", "<id>"],
     "sql_plus": ["<stage>", "<stage>"], "won": ["<stage>"], "lost": ["<stage>"], "exclude_renewals": false}
  ]
}
```

Companion files, same folder, same `.local.json` suffix: `<client>-targets.local.json` (append-only revisions, see `targets.json` for the shape) and `<client>-reason-map.local.json` (this portal's closed-lost picklist values → failure mode, see `reason_map.json`).

## 3. Analytics

| Item | Value |
|---|---|
| GA4 property id | `<digits>` — name it, and name any property that must NOT be used |
| Search Console property | `sc-domain:<domain>` |
| Site-wide exclusions | `<e.g. bot-traffic countries, internal IPs — with the reason>` |

### Campaign page sets (one unified set per campaign, used for every traffic table)

| Campaign | Landing pages | Blog posts / pillar | Notes |
|---|---|---|---|
| `<name>` | `/services/<...>` | `/post/<slug>`, ... | `<treat A + B as one campaign, etc.>` |

## 4. Reporting

| Item | Value |
|---|---|
| Output root for reports | `<absolute or repo path, e.g. <repo>/analytics/>` — resolved from the pack, not from the current directory |
| Campaign report path pattern | `<e.g. Campaign-<X>/research/<campaign>-performance-<period>.md>` |
| Style templates | `<path>/marketing-monthly-<style>.html` — one per board style; name the styles. If none exist yet, the first run builds one and saves it here |
| Reference reports (copy structure, swap data) | `<paths to the last shipped monthly and campaign reports>` |
| Publishing target (optional) | `<repo, branch, folder, space id; the verification step; anything that must never be added, e.g. a build script>` |
| Targets in force | `<MQL / SQL per quarter, revenue target, who set them and when>` |

## 5. Definitions that override the defaults

Write only what differs from `definitions.md`. Typical entries: which pipelines' deals count as MQL, whether parked-pipeline deals are SQL-eligible, standing exclusions (reseller pass-through, renewals), how event captures are identified, whether the two funnels may ever be summed (default: never).

## 6. House style

Voice register, number formatting, hyperlink colour rule, emoji policy, banned title formulas, the de-identification rule for client names in files versus in gated reports. Whatever the reviewer has corrected before goes here so it is not corrected twice.
