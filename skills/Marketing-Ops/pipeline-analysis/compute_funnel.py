"""Deterministic RevOps funnel engine for the pipeline-analysis skill.

Stdlib only (no installs). Reads a normalized JSON (see DESIGN.md / definitions.md
data model) and emits, for EACH configured funnel independently, computed cohorts /
funnel / velocity / sources / flags / conversions. Rules mirror definitions.md —
keep the two in sync.

Funnels are computed in parallel and NEVER blended — typically:
  - New Business       (net-new pipelines; renewals excluded)
  - Account Management (existing-client pipelines; renewals kept — AM by nature)

Which pipelines and stage ids belong to which funnel is CLIENT CONFIGURATION, not code:
it comes from the `funnels` and `crm` blocks of the input JSON (or a --config file — see
references/context-pack.TEMPLATE.md). FUNNELS_DEFAULT below only covers a stock HubSpot
"default" pipeline and exists so the engine runs with zero config.

Won/Lost are classified by per-pipeline stage semantics across ALL pipelines, not
just the first one (a Closed-Lost in a secondary pipeline is a loss, not in-flight). Conversions
are full-lifecycle, cohort-anchored; cross-period transitions are surfaced, not
truncated. SQL uses first-entry; re-entry is flagged as an exception.

The funnel definitions live in the input JSON under `funnels` so the rules stay
data-driven and testable. Ticket stage ids and AM source classification live under `crm`.
"""
import json
import os
import sys
import statistics
from datetime import date

REASON_MAP_PATH = os.path.join(os.path.dirname(__file__), "reason_map.json")
TARGETS_PATH = os.path.join(os.path.dirname(__file__), "targets.json")


def load_targets(path=TARGETS_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_targets(targets_obj, period_end, revision_label=None):
    """Pick the applicable target revision. Default: latest with effective_from <= period end.
    Named override selects that revision (ValueError if absent). None if nothing applies yet."""
    revs = (targets_obj or {}).get("revisions", [])
    if revision_label:
        for r in revs:
            if r.get("label") == revision_label:
                return r
        raise ValueError(f"unknown targets revision: {revision_label!r}")
    pe = _d(period_end)
    applicable = [r for r in revs if _d(r["effective_from"]) <= pe]
    return max(applicable, key=lambda r: _d(r["effective_from"])) if applicable else None


def load_reason_map(path=REASON_MAP_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


REASON_MAP = load_reason_map() if os.path.exists(REASON_MAP_PATH) else {"map": {}, "owners": {}}


def map_reason(reason_value, reason_map=None):
    rm = reason_map if reason_map is not None else REASON_MAP
    entry = rm["map"].get(reason_value) if reason_value else None
    if not entry:
        return ("Unattributed", None)
    return (entry["mode"], entry.get("owner"))

# --- ticket (lead inbox pipeline) stages + AM source classification ---
# Stock HubSpot ticket pipeline ships stages 1..4 with no "qualified" stage, so the
# MQL / Prospect ids are empty until the client's `crm` block sets them.
CRM_DEFAULT = {
    "ticket_stage_mql": "",
    "ticket_stage_prospect": "",
    "ticket_stage_closed": "4",
    "ticket_stages_open": ["1", "2", "3"],
    "am_sources": [],
}
TICKET_MQL, TICKET_PROSPECT, TICKET_CLOSED = "", "", "4"
TICKET_OPEN = {"1", "2", "3"}
AM_SOURCES = set()


def configure(crm):
    """Apply a client's `crm` block (ticket stage ids, AM ticket sources, optional
    reason-map path) to the module. Called by load() and analyze(); idempotent."""
    global TICKET_MQL, TICKET_PROSPECT, TICKET_CLOSED, TICKET_OPEN, AM_SOURCES, REASON_MAP
    c = dict(CRM_DEFAULT)
    c.update(crm or {})
    TICKET_MQL = c["ticket_stage_mql"]
    TICKET_PROSPECT = c["ticket_stage_prospect"]
    TICKET_CLOSED = c["ticket_stage_closed"]
    TICKET_OPEN = set(c["ticket_stages_open"])
    AM_SOURCES = set(c["am_sources"])
    if c.get("reason_map_path"):
        REASON_MAP = load_reason_map(c["reason_map_path"])
    return c

# --- default funnel configs (mirror definitions.md; can be overridden in input JSON) ---
FUNNELS_DEFAULT = [
    {
        # Stock HubSpot sales pipeline. Real clients override this via `funnels` in the
        # input JSON / --config (see references/context-pack.TEMPLATE.md).
        "key": "nb", "name": "New Business",
        "pipelines": ["default"],
        "sql_plus": ["qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin",
                     "contractsent", "closedwon"],
        "won": ["closedwon"],
        "lost": ["closedlost"],
        "exclude_renewals": True,
        "gates": [
            {"name": "Opportunity", "entry": "createdate"},
            {"name": "SQL", "entry": "sql_entry"},
            {"name": "Proposal", "entry": "proposal_entry"},
            {"name": "Negotiation", "entry": "nego_entry"},
            {"name": "Close", "entry": "won_entry"},
        ],
    },
]


# --- date / io helpers ---
def _d(iso):
    if not iso:
        return None
    s = iso[:10]
    return date(int(s[:4]), int(s[5:7]), int(s[8:10]))


def ym(iso):
    d = _d(iso)
    return f"{d.year:04d}-{d.month:02d}" if d else None


def days(a, b):
    da, db = _d(a), _d(b)
    return (db - da).days if da and db else None


def in_period(iso, period):
    d = _d(iso)
    return bool(d and _d(period["start"]) <= d <= _d(period["end"]))


def load(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "crm" in data:
        configure(data["crm"])
    return data


def is_renewal(deal):
    name = (deal.get("name") or "").lower()
    return deal.get("dealtype") == "existingbusiness" or "renewal" in name


def classify_deal(deal, funnel, period, manual_excludes):
    """(counts_as_mql, exclude_reason). Reasons reused verbatim by flags()."""
    if deal.get("pipeline") not in funnel["pipelines"]:
        return (False, "other funnel")
    if funnel.get("exclude_renewals") and is_renewal(deal):
        return (False, "renewal/existing-business")
    if deal.get("id") in (manual_excludes or []):
        return (False, "sub-deal (manual)")
    if not in_period(deal.get("createdate"), period):
        return (False, "createdate outside period")
    return (True, None)


def reached_sql(deal, funnel):
    """A deal reached SQL if it ever entered the SQL stage (first-entry date present)
    or currently sits at/past an SQL+ stage. Boolean per deal — re-entry never inflates."""
    return bool(deal.get("sql_entry")) or deal.get("stage") in set(funnel["sql_plus"])


# --- per-funnel cohorts ---
def mql_cohorts(data, funnel):
    period, mx = data["period"], data.get("manual_excludes", [])
    by_month, included, excluded = {}, [], []
    for d in data["deals"]:
        if d.get("pipeline") not in funnel["pipelines"]:
            continue
        ok, reason = classify_deal(d, funnel, period, mx)
        if ok:
            included.append(d)
            k = ym(d["createdate"])
            by_month[k] = by_month.get(k, 0) + 1
        else:
            excluded.append((d["id"], reason))
    # known deal-less qualified MQL tickets (explicit, not auto-detected — needs full
    # association data we may not have). Only NB carries these per definitions.md.
    ticket_only = []
    for t in data["tickets"]:
        if t.get("id") in (funnel.get("known_ticket_only") or []) and in_period(t.get("closed_date"), period):
            ticket_only.append(t)
            k = ym(t["closed_date"])
            by_month[k] = by_month.get(k, 0) + 1
    return {"by_month": dict(sorted(by_month.items())),
            "included": included, "excluded": excluded, "ticket_only": ticket_only}


def funnel_outcomes(data, funnel):
    deals = mql_cohorts(data, funnel)["included"]
    won_set, lost_set = set(funnel["won"]), set(funnel["lost"])
    n_sql = won = lost = 0
    rev_won = rev_lost = open_pipe = 0.0
    for d in deals:
        amt = d.get("amount_home") or 0
        if reached_sql(d, funnel):
            n_sql += 1
        st = d.get("stage")
        if st in won_set:
            won += 1
            rev_won += amt
        elif st in lost_set:
            lost += 1
            rev_lost += amt
        else:
            open_pipe += amt
    closed = won + lost
    return {"mql": len(deals), "reached_sql": n_sql, "won": won, "lost": lost,
            "in_flight": len(deals) - closed,
            "win_rate": (won / closed) if closed else None,
            "revenue_won": round(rev_won, 2), "revenue_lost": round(rev_lost, 2),
            "open_pipeline": round(open_pipe, 2)}


def leak_events(data, funnel, reason_map=None):
    """Typed exit events for LOST deals in this funnel's cohort (diagnosis plane)."""
    coh = mql_cohorts(data, funnel)["included"]
    lost_set = set(funnel["lost"])
    events = []
    for d in coh:
        if d.get("stage") in lost_set:
            mode, owner = map_reason(d.get("loss_reason"), reason_map)
            events.append({
                "id": d["id"], "name": d.get("name"),
                "gate": "sql+" if reached_sql(d, funnel) else "mql",
                "reason": d.get("loss_reason") or "(blank)",
                "mode": mode, "owner": owner,
                "amount": d.get("amount_home") or 0,
            })
    return events


def deepest_gate(deal, funnel):
    """Furthest gate the deal reached, by entry-date presence (Opportunity if only created)."""
    reached = "Opportunity"
    for g in funnel.get("gates", []):
        if g["entry"] == "createdate":
            continue
        if deal.get(g["entry"]):
            reached = g["name"]
    return reached


def _furthest_gate_index(deal, funnel, won_set):
    """Index of the furthest gate the deal reached. Won deals reach the last gate
    (Close) regardless of sparse intermediate stage-entry stamps; others use the
    deepest entry-stamped gate."""
    gates = funnel.get("gates", [])
    if deal.get("stage") in won_set:
        return len(gates) - 1
    idx = 0  # Opportunity (createdate always present)
    for i, g in enumerate(gates):
        if g["entry"] != "createdate" and deal.get(g["entry"]):
            idx = i
    return idx


def flow_gates(data, funnel):
    """Per-gate flow (NB), monotonic by construction: reached[i] counts deals whose
    furthest point is at or beyond gate i; leaked_here attributes losses to the
    deepest gate reached. NOTE: reached is directional — an open deal whose current
    stage is beyond its last stamped stage-entry date can undercount (HubSpot stamps
    entry dates sparsely); won deals are always counted through every gate."""
    coh = mql_cohorts(data, funnel)["included"]
    won_set, lost_set = set(funnel["won"]), set(funnel["lost"])
    gates = funnel.get("gates", [])
    rows = []
    for i, g in enumerate(gates):
        reached = sum(1 for d in coh if _furthest_gate_index(d, funnel, won_set) >= i)
        leaked = sum(1 for d in coh
                     if d.get("stage") in lost_set and deepest_gate(d, funnel) == g["name"])
        rows.append({"gate": g["name"], "reached": reached, "leaked_here": leaked})
    return rows


def leak_pnl(data, funnel, reason_map=None):
    """Roll leak events up by failure mode: count + € + owner."""
    pnl = {}
    for e in leak_events(data, funnel, reason_map):
        row = pnl.setdefault(e["mode"], {"count": 0, "eur": 0.0, "owner": e["owner"]})
        row["count"] += 1
        row["eur"] += e["amount"]
    for m in pnl:
        pnl[m]["eur"] = round(pnl[m]["eur"], 2)
    return pnl


# --- velocity ---
def _stats(vals):
    vals = [x for x in vals if x is not None]
    if not vals:
        return {"n": 0, "median": None, "mean": None, "min": None, "max": None, "outliers": []}
    return {"n": len(vals), "median": statistics.median(vals),
            "mean": round(statistics.mean(vals), 1), "min": min(vals), "max": max(vals),
            "outliers": sorted(x for x in vals if x > 90)}


def velocity(data, funnel):
    coh = mql_cohorts(data, funnel)
    t2m, m2s, s2w = [], [], []
    for d in coh["included"]:
        # ticket -> MQL: prefer the originating ticket createdate carried on the deal
        # (resolved from association; may be a prior-period ticket — surfaced, not dropped)
        tc = d.get("ticket_createdate")
        if tc:
            t2m.append(days(tc, d.get("createdate")))
        if d.get("sql_entry"):
            m2s.append(days(d.get("createdate"), d.get("sql_entry")))
        if d.get("won_entry"):
            s2w.append(days(d.get("sql_entry") or d.get("createdate"), d.get("won_entry")))
    return {"ticket_to_mql": _stats(t2m), "mql_to_sql": _stats(m2s), "sql_to_won": _stats(s2w)}


# --- ticket cohorts + sources (per funnel, by ticket source classification) ---
def ticket_funnel_key(t):
    """Classify a ticket to NB vs AM by source (matches the calibrated report)."""
    return "am" if t.get("source_type") in AM_SOURCES else "nb"


def ticket_cohorts(data, funnel):
    out = {}
    for t in data["tickets"]:
        if ticket_funnel_key(t) != funnel["key"]:
            continue
        if not in_period(t.get("createdate"), data["period"]):
            continue
        row = out.setdefault(ym(t["createdate"]),
                             {"created": 0, "mql": 0, "prospect": 0, "closed": 0, "open": 0})
        row["created"] += 1
        st = t.get("stage")
        if st == TICKET_MQL:
            row["mql"] += 1
        elif st == TICKET_PROSPECT:
            row["prospect"] += 1
        elif st == TICKET_CLOSED:
            row["closed"] += 1
        elif st in TICKET_OPEN:
            row["open"] += 1
    return dict(sorted(out.items()))


def sources(data, funnel):
    out = {}
    for t in data["tickets"]:
        if ticket_funnel_key(t) != funnel["key"]:
            continue
        if not in_period(t.get("createdate"), data["period"]):
            continue
        key = t.get("source_type") or "Unassigned"
        row = out.setdefault(key, {"tickets": 0, "mql": 0, "qualified": 0})
        row["tickets"] += 1
        if t.get("stage") == TICKET_MQL:
            row["mql"] += 1
        if t.get("stage") in (TICKET_MQL, TICKET_PROSPECT):
            row["qualified"] += 1
    return out


# --- flags + conversions ---
def flags(data, funnel):
    period, mx = data["period"], data.get("manual_excludes", [])
    out = []
    for d in data["deals"]:
        if d.get("pipeline") not in funnel["pipelines"]:
            continue
        _, reason = classify_deal(d, funnel, period, mx)
        if reason == "renewal/existing-business":
            out.append({"type": "renewal_excluded", "id": d["id"], "detail": d.get("name")})
        elif reason == "sub-deal (manual)":
            out.append({"type": "manual_subdeal", "id": d["id"], "detail": d.get("name")})
        # prior-period re-entry: createdate before period but a stage-entry inside it
        if (not in_period(d.get("createdate"), period)
                and (in_period(d.get("mql_entry"), period) or in_period(d.get("sql_entry"), period))):
            out.append({"type": "prior_period_reentry", "id": d["id"],
                        "detail": f"{d.get('name')}: created {d.get('createdate','?')[:10]}"})
        # SQL re-entry exception: explicit list in input (history not pulled by default)
        if d.get("id") in (data.get("sql_reentry") or []):
            out.append({"type": "sql_reentry", "id": d["id"], "detail": d.get("name")})
        # cross-period lead: MQL in-period but originating ticket before the period
        tc = d.get("ticket_createdate")
        if (tc and in_period(d.get("createdate"), period) and not in_period(tc, period)
                and classify_deal(d, funnel, period, mx)[0]):
            out.append({"type": "cross_period_lead", "id": d["id"],
                        "detail": f"{d.get('name')}: lead {tc[:10]} → MQL {d.get('createdate','?')[:10]}"})
    for t in mql_cohorts(data, funnel)["ticket_only"]:
        out.append({"type": "ticket_only_mql", "id": t["id"], "detail": t.get("subject")})
    return out


def _rate(num, den):
    return round(num / den, 4) if den else None


def accept_gate(data, funnel):
    """Gate 1 (NB only): the marketing->sales handoff, inferred from ticket stage.
    Accepted = MQL/Prospect stage; Rejected = Closed-no-potential; Pending = open.
    Reject rate is the B (marketing quality) signal; None for AM (enters at Opportunity)."""
    if funnel["key"] != "nb":
        return None
    leads = accepted = rejected = pending = 0
    by_source = {}
    for t in data["tickets"]:
        if ticket_funnel_key(t) != "nb" or not in_period(t.get("createdate"), data["period"]):
            continue
        leads += 1
        s = by_source.setdefault(t.get("source_type") or "Unassigned",
                                 {"leads": 0, "accepted": 0, "rejected": 0})
        s["leads"] += 1
        st = t.get("stage")
        if st in (TICKET_MQL, TICKET_PROSPECT):
            accepted += 1
            s["accepted"] += 1
        elif st == TICKET_CLOSED:
            rejected += 1
            s["rejected"] += 1
        else:
            pending += 1
    return {"leads": leads, "accepted": accepted, "rejected": rejected, "pending": pending,
            "accept_rate": _rate(accepted, leads), "reject_rate": _rate(rejected, leads),
            "by_source": by_source}


def conversions(data, funnel):
    """Cohort-anchored, full-lifecycle.
    - ticket->MQL: of in-period tickets for this funnel, share that reached ticket MQL stage.
    - MQL->SQL:    of in-period deal-MQLs, share that reached SQL+ (tracked forward).
    - SQL->Won:    of those that reached SQL, share Won (tracked forward)."""
    coh = mql_cohorts(data, funnel)
    fo = funnel_outcomes(data, funnel)
    tix = [t for t in data["tickets"]
           if ticket_funnel_key(t) == funnel["key"] and in_period(t.get("createdate"), data["period"])]
    tix_mql = sum(1 for t in tix if t.get("stage") == TICKET_MQL)
    return {"ticket_to_mql": _rate(tix_mql, len(tix)),
            "ticket_to_mql_n": (tix_mql, len(tix)),
            "mql_to_sql": _rate(fo["reached_sql"], fo["mql"]),
            "mql_to_sql_n": (fo["reached_sql"], fo["mql"]),
            "sql_to_won": _rate(fo["won"], fo["reached_sql"]),
            "sql_to_won_n": (fo["won"], fo["reached_sql"])}


def throughput(data, funnel):
    """Event-time monthly counts (throughput lens), distinct from cohort conversion.
    MQL by createdate month; SQL by first sql_entry month; Won by won_entry month.
    NEVER divide sql_converted[M] by mql_created[M] — different cohorts (see definitions.md)."""
    coh = mql_cohorts(data, funnel)["included"]
    mql_m, sql_m, won_m = {}, {}, {}
    for d in coh:
        mql_m[ym(d["createdate"])] = mql_m.get(ym(d["createdate"]), 0) + 1
        if d.get("sql_entry"):
            k = ym(d["sql_entry"]); sql_m[k] = sql_m.get(k, 0) + 1
        if d.get("won_entry"):
            k = ym(d["won_entry"]); won_m[k] = won_m.get(k, 0) + 1
    return {"mql_created": dict(sorted(mql_m.items())),
            "sql_converted": dict(sorted(sql_m.items())),
            "won_closed": dict(sorted(won_m.items()))}


def throughput_vs_target(tp, target_rev):
    """Monthly actual vs target: MQL by created-month, SQL by converted-month.
    Year taken from the revision's effective_from (targets are 12-cell Jan..Dec vectors)."""
    if not target_rev:
        return None
    year = _d(target_rev["effective_from"]).year

    def _cmp(actual_by_month, target_list):
        if not target_list:
            return []
        return [{"month": f"{year:04d}-{i + 1:02d}", "target": tgt,
                 "actual": actual_by_month.get(f"{year:04d}-{i + 1:02d}", 0)}
                for i, tgt in enumerate(target_list)]

    return {"mql": _cmp(tp["mql_created"], target_rev.get("mql")),
            "sql": _cmp(tp["sql_converted"], target_rev.get("sql"))}


def execution_flags(data, funnel, silent_days=45):
    """Directional sales-execution (C) signals — hypotheses, not verdicts.
    (1) went-silent: open deal idle past `silent_days` since its deepest entry.
    (2) unexplained loss: a lost deal with blank/Other reason (feeds C after acceptance).
    Accept->no-opportunity needs ticket<->deal linkage not pulled by default (documented gap)."""
    if funnel["key"] != "nb":
        return None
    coh = mql_cohorts(data, funnel)["included"]
    won_set, lost_set = set(funnel["won"]), set(funnel["lost"])
    period_end = data["period"]["end"]
    went_silent, unexplained = [], []
    for d in coh:
        st = d.get("stage")
        if st not in lost_set and st not in won_set:
            last = (d.get("nego_entry") or d.get("proposal_entry") or d.get("sql_entry")
                    or d.get("mql_entry") or d.get("createdate"))
            dd = days(last, period_end)
            if dd is not None and dd > silent_days:
                went_silent.append({"id": d["id"], "name": d.get("name"), "days": dd})
        elif st in lost_set:
            mode, _ = map_reason(d.get("loss_reason"))
            if mode == "Unattributed":
                unexplained.append({"id": d["id"], "name": d.get("name"),
                                    "amount": d.get("amount_home") or 0})
    return {"went_silent": sorted(went_silent, key=lambda x: -x["days"]),
            "unexplained_losses": unexplained,
            "note": "directional inference; hardens after sales retro + reactivated 'Not responsive' reason. Accept->no-opportunity signal deferred (needs ticket-deal linkage)."}


def avg_won_deal_size(deals, funnel):
    """Mean amount of won deals in this funnel's pipelines. low_confidence if n < 5."""
    won_set = set(funnel["won"])
    amts = [d.get("amount_home") for d in deals
            if d.get("pipeline") in funnel["pipelines"]
            and d.get("stage") in won_set and d.get("amount_home")]
    if not amts:
        return {"avg": None, "n": 0, "low_confidence": True}
    return {"avg": round(statistics.mean(amts), 2), "n": len(amts), "low_confidence": len(amts) < 5}


def reverse_funnel(data, funnel, target_rev, avg_override=None):
    """Back-solve required volume for the NB revenue target, using measured cohort rates.
       required_won = target / avg_deal
       required_sql = required_won / sql_to_won
       required_mql = required_sql / mql_to_sql
       required_leads = required_mql / ticket_to_mql
    NB-only; None if no NB revenue target."""
    if funnel["key"] != "nb" or not target_rev or not target_rev.get("won_eur_nb"):
        return None
    conv = conversions(data, funnel)
    avinfo = avg_won_deal_size(data["deals"], funnel)
    avg = avg_override if avg_override is not None else avinfo["avg"]
    won_target = target_rev["won_eur_nb"]
    if not avg:
        return {"error": "no avg deal size available", "avg_deal_info": avinfo}

    def _div(a, b):
        return (a / b) if (a is not None and b) else None

    def _r(x):
        return round(x, 1) if x is not None else None

    r_won = _r(won_target / avg)
    r_sql = _r(_div(r_won, conv.get("sql_to_won")))
    r_mql = _r(_div(r_sql, conv.get("mql_to_sql")))
    r_leads = _r(_div(r_mql, conv.get("ticket_to_mql")))
    return {"won_target": won_target, "avg_deal": avg, "avg_deal_info": avinfo,
            "required": {"won": r_won, "sql": r_sql, "mql": r_mql, "leads": r_leads},
            "rates_used": {"sql_to_won": conv.get("sql_to_won"),
                           "mql_to_sql": conv.get("mql_to_sql"),
                           "ticket_to_mql": conv.get("ticket_to_mql")},
            "confidence": "low" if avinfo["low_confidence"] else "ok"}


def verdict(data, funnel, target_rev, rev_funnel):
    """Diagnosis-first topper (NB only). Heuristic binding-constraint pick (directional):
    A if MQL volume < 70% of required run-rate; else B if reject-rate > 30%;
    else the largest lost-€ failure-mode cluster. Claude adds projection nuance in prose."""
    if funnel["key"] != "nb":
        return None
    fo = funnel_outcomes(data, funnel)
    pnl = leak_pnl(data, funnel)
    acc = accept_gate(data, funnel)
    won_target = (target_rev or {}).get("won_eur_nb")
    on_track = (fo["revenue_won"] >= won_target) if won_target else None
    req = (rev_funnel or {}).get("required", {})
    constraint = None
    if req.get("mql") and fo["mql"] < 0.7 * req["mql"]:
        constraint = {"mode": "A", "why": "MQL volume below the run-rate required for target"}
    elif acc and acc["reject_rate"] and acc["reject_rate"] > 0.3:
        constraint = {"mode": "B", "why": f"lead reject rate {acc['reject_rate']:.0%}"}
    else:
        biggest = max(pnl.items(), key=lambda kv: kv[1]["eur"], default=None)
        if biggest:
            constraint = {"mode": biggest[0], "why": f"largest lost-EUR cluster (EUR {biggest[1]['eur']:,.0f})"}
    return {"on_track_revenue": on_track, "won_so_far": fo["revenue_won"],
            "won_target": won_target, "primary_constraint": constraint, "leak_pnl": pnl}


def analyze(data, targets_obj=None, targets_revision=None, avg_override=None):
    configure(data.get("crm"))
    funnels = data.get("funnels") or FUNNELS_DEFAULT
    target_rev = (resolve_targets(targets_obj, data["period"]["end"], targets_revision)
                  if targets_obj else None)
    out = {"period": data["period"], "generated": data.get("generated"),
           "targets_revision": (target_rev or {}).get("label"), "funnels": {}}
    for f in funnels:
        block = {
            "name": f["name"], "config": f,
            "mql_cohorts": mql_cohorts(data, f),
            "funnel": funnel_outcomes(data, f),
            "velocity": velocity(data, f),
            "ticket_cohorts": ticket_cohorts(data, f),
            "sources": sources(data, f),
            "flags": flags(data, f),
            "conversions": conversions(data, f),
            "throughput": throughput(data, f),
        }
        if f["key"] == "nb":
            block["flow_gates"] = flow_gates(data, f)
            block["accept_gate"] = accept_gate(data, f)
            block["leak_events"] = leak_events(data, f)
            block["leak_pnl"] = leak_pnl(data, f)
            block["execution_flags"] = execution_flags(data, f)
            block["throughput_vs_target"] = throughput_vs_target(block["throughput"], target_rev)
            block["reverse_funnel"] = reverse_funnel(data, f, target_rev, avg_override)
            block["verdict"] = verdict(data, f, target_rev, block["reverse_funnel"])
        out["funnels"][f["key"]] = block
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser(description="pipeline-analysis funnel engine (stdlib only)")
    ap.add_argument("input", help="normalized input JSON (deals, tickets, period, ...)")
    ap.add_argument("output", help="where to write the computed JSON")
    ap.add_argument("--config", help="client pack JSON with `funnels` and/or `crm` blocks; "
                                     "fills whatever the input JSON does not carry")
    ap.add_argument("--targets", help="client targets JSON (append-only revisions); "
                                      "default: targets.json next to this script")
    ap.add_argument("--reason-map", help="client loss-reason map JSON; "
                                         "default: reason_map.json next to this script")
    ap.add_argument("--targets-revision", help="pin a named targets revision")
    a = ap.parse_args()

    data = load(a.input)
    if a.config:
        cfg = load(a.config)
        for k in ("funnels", "crm"):
            if k in cfg and k not in data:
                data[k] = cfg[k]
    if a.reason_map:
        global REASON_MAP
        REASON_MAP = load_reason_map(a.reason_map)
    targets_path = a.targets or TARGETS_PATH
    targets_obj = load_targets(targets_path) if os.path.exists(targets_path) else None
    rev = a.targets_revision or data.get("targets_revision")
    with open(a.output, "w", encoding="utf-8") as f:
        json.dump(analyze(data, targets_obj=targets_obj, targets_revision=rev,
                          avg_override=data.get("avg_deal_override")), f, indent=2)
    print(f"wrote {a.output}")


if __name__ == "__main__":
    main()
