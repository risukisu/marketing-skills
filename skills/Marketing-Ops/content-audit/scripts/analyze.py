"""Compute every number in the content audit and write metrics.json.

Reads from the run folder: pages.json, labels.json, taxonomy.json, crawl.json, and when present
valueprop.json and exports.json. Rules and thresholds: references/diagnosis-rules.md.

    python analyze.py --run-dir RUN [--config thresholds.json] [--as-of 2026-01-31]
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    ICP_FIT, RESERVED_OFFERINGS, STAGES, path_key, read_json, utf8_console, write_json,
)

DEFAULTS = {
    "min_pages": {"attention": 5, "interest": 3, "desire": 2, "action": 1},
    "onward_share_min": 0.5,          # share of a cell's pages with an onward step
    "findability_ratio_min": 0.5,     # offering's impression share / its page share
    "desire_position_max": 20.0,      # weighted average position of Desire pages
    "conversion_min_sessions": 100,   # below this an offering is too small to judge conversion
    "conversion_rate_ratio_min": 0.5, # offering key-event rate / site rate
    "distribution_share_min": 0.10,   # share of sessions from social, email, referral, paid
    "paid_reliance_share": 0.6,       # ads clicks / (ads clicks + organic clicks)
    "striking_min_impressions": 100,
    "striking_position": [4, 20],
    "stale_months": 24,
    "duplicate_jaccard": 0.75,
}
LEAD_EXCLUDE_STAGES = {"subscriber", "other", "(blank)", "", "unknown"}
ORGANIC_CHANNELS = {"organic search", "direct", "(other)", "unassigned", "(not set)", "organic video"}
STAGE_ORDER = {s: i for i, s in enumerate(STAGES)}
STOP = set("a an and are as at be by for from how in is it of on or our the to vs what when why with your you "
           "we us this that guide part".split())


def _r(x, n=4):
    return round(x, n) if isinstance(x, float) else x


def _share(a, b):
    return round(a / b, 4) if b else None


def load_run(run_dir: Path) -> dict:
    need = ["pages.json", "labels.json", "taxonomy.json", "crawl.json"]
    missing = [n for n in need if not (run_dir / n).exists()]
    if missing:
        print(f"error: missing {', '.join(missing)} in {run_dir}", file=sys.stderr)
        sys.exit(2)
    data = {n.split(".")[0]: read_json(run_dir / n) for n in need}
    for opt in ("valueprop.json", "exports.json"):
        data[opt.split(".")[0]] = read_json(run_dir / opt) if (run_dir / opt).exists() else None
    return data


def build_pages(data: dict) -> tuple[list[dict], list[dict]]:
    labels = {lb["id"]: lb for lb in data["labels"]["labels"]}
    crawl = {(p.get("final_url") or p["url"]): p for p in data["crawl"]["pages"] if p.get("is_html")}
    content, excluded = [], []
    for p in data["pages"]["pages"]:
        row = dict(p)
        raw = crawl.get(p["url"], {})
        row["body_links"] = [lk["url"] for lk in raw.get("links", []) if not lk["nav"]]
        row["cta"] = raw.get("cta_links", [])
        if p["excluded"]:
            excluded.append(row)
            continue
        lb = labels.get(p["id"])
        if not lb:
            continue
        row.update({k: lb[k] for k in ("offering", "secondary_offering", "stage", "content_type", "icp_fit",
                                        "confidence", "evidence", "note")})
        content.append(row)
    return content, excluded


def attach_exports(pages: list[dict], exports: dict | None) -> dict:
    layers = {}
    src = (exports or {}).get("sources", {})
    for kind in ("gsc_pages", "gsc_queries", "ga4_landing", "hubspot_contacts", "ads_landing"):
        s = src.get(kind)
        layers[kind] = {"present": bool(s), "window": (s or {}).get("window", ""),
                        "files": (s or {}).get("files", []), "rows": (s or {}).get("rows", 0)}
    keys = {p["path"]: p for p in pages}
    for p in pages:
        p.update({"impressions": None, "clicks": None, "position": None, "sessions": None, "key_events": None,
                  "channels": None, "contacts": None, "lead_contacts": None, "ads_clicks": None, "ads_cost": None,
                  "ads_conversions": None})
    match = {}
    for kind in layers:
        layers[kind]["capped"] = bool((src.get(kind) or {}).get("capped_files"))
    if src.get("gsc_pages"):
        by = src["gsc_pages"]["by_path"]
        capped = layers["gsc_pages"]["capped"]
        for p in pages:
            d = by.get(p["path"])
            p["in_gsc_export"] = d is not None
            if d is None and capped:
                continue  # unknown, not zero: the export stopped before this page
            d = d or {}
            p["impressions"] = d.get("impressions", 0) or 0
            p["clicks"] = d.get("clicks", 0) or 0
            p["position"] = d.get("position")
        match["gsc_pages"] = _match_stats(by, keys, weight="impressions")
    if src.get("ga4_landing"):
        by = src["ga4_landing"]["by_path"]
        for p in pages:
            if p["path"] not in by and layers["ga4_landing"]["capped"]:
                continue
            d = by.get(p["path"], {})
            p["sessions"] = d.get("sessions", 0) or 0
            p["key_events"] = d.get("key_events", 0) or 0
            p["channels"] = d.get("channels")
        match["ga4_landing"] = _match_stats(by, keys, weight="sessions")
        layers["ga4_landing"]["has_channels"] = any(d.get("channels") for d in by.values())
        layers["ga4_landing"]["has_key_events"] = any((d.get("key_events") or 0) > 0 for d in by.values())
    if src.get("hubspot_contacts"):
        by = src["hubspot_contacts"]["by_path"]
        for p in pages:
            d = by.get(p["path"], {})
            p["contacts"] = d.get("contacts", 0)
            p["lead_contacts"] = sum(n for st, n in d.get("by_stage", {}).items()
                                     if st not in LEAD_EXCLUDE_STAGES) if d.get("by_stage") else None
        match["hubspot_contacts"] = _match_stats(by, keys, weight="contacts")
        layers["hubspot_contacts"]["has_lifecycle"] = any(d.get("by_stage") for d in by.values())
    if src.get("ads_landing"):
        by = src["ads_landing"]["by_path"]
        for p in pages:
            d = by.get(p["path"], {})
            p["ads_clicks"] = d.get("clicks", 0) or 0
            p["ads_cost"] = d.get("cost", 0) or 0
            p["ads_conversions"] = d.get("conversions", 0) or 0
        match["ads_landing"] = _match_stats(by, keys, weight="clicks")
    return {"layers": layers, "match": match}


def _match_stats(by_path: dict, keys: dict, weight: str | None = None) -> dict:
    total_rows = len(by_path)
    matched = [k for k in by_path if k in keys]
    out = {"rows": total_rows, "matched_rows": len(matched), "matched_share": _share(len(matched), total_rows)}
    if weight:
        tot = sum((d.get(weight) or 0) for d in by_path.values())
        got = sum((by_path[k].get(weight) or 0) for k in matched)
        out.update({f"{weight}_total": _r(float(tot), 2), f"{weight}_matched": _r(float(got), 2),
                    f"{weight}_matched_share": _share(got, tot)})
        top_unmatched = sorted(((k, d.get(weight) or 0) for k, d in by_path.items() if k not in keys),
                               key=lambda x: -x[1])[:10]
        out["top_unmatched"] = [[k, _r(float(v), 2)] for k, v in top_unmatched]
    return out


def onward(pages: list[dict]) -> None:
    by_key = {p["path"]: p for p in pages}
    for p in pages:
        lc = p["lead_capture"]
        own_capture = lc["email_form"] or lc["form_embed"] or lc["booking"] or any(
            c.get("kind") in ("booking", "mailto") for c in p["cta"])
        p["has_capture"] = bool(own_capture)
        targets = [by_key.get(path_key(u)) for u in p["body_links"]]
        targets = [t for t in targets if t and t is not p]
        fits = lambda t: t["offering"] in (p["offering"], "cross") or t.get("secondary_offering") == p["offering"]  # noqa: E731
        to_desire_action = [t for t in targets if t["stage"] in ("desire", "action") and fits(t)]
        to_action = [t for t in targets if t["stage"] == "action" and fits(t)]
        if p["stage"] in ("attention", "interest"):
            p["onward"] = bool(to_desire_action) or p["has_capture"]
        elif p["stage"] == "desire":
            p["onward"] = bool(to_action) or p["has_capture"]
        else:
            p["onward"] = None
        p["links_to_desire_action"] = len(to_desire_action)
        p["links_to_action"] = len(to_action)
    inbound = Counter()
    for p in pages:
        for u in set(p["body_links"]):
            t = by_key.get(path_key(u))
            if t and t is not p:
                inbound[t["path"]] += 1
    for p in pages:
        p["inbound_body_links"] = inbound[p["path"]]


def _sum(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return _r(float(sum(vals)), 2) if vals else None


def _wpos(rows):
    num = sum((r["position"] or 0) * (r["impressions"] or 0) for r in rows if r.get("position"))
    den = sum((r["impressions"] or 0) for r in rows if r.get("position"))
    return round(num / den, 1) if den else None


def cell_metrics(rows: list[dict]) -> dict:
    stage_rows = [r for r in rows if r.get("onward") is not None]
    return {
        "pages": len(rows),
        "pages_icp": sum(1 for r in rows if r["icp_fit"] in ("icp", "adjacent")),
        "onward_share": _share(sum(1 for r in stage_rows if r["onward"]), len(stage_rows)) if stage_rows else None,
        "with_capture": sum(1 for r in rows if r["has_capture"]),
        "impressions": _sum(rows, "impressions"), "clicks": _sum(rows, "clicks"), "position": _wpos(rows),
        "pages_with_impressions": sum(1 for r in rows if (r.get("impressions") or 0) > 0),
        "pages_in_search_export": sum(1 for r in rows if r.get("in_gsc_export")),
        "sessions": _sum(rows, "sessions"), "key_events": _sum(rows, "key_events"),
        "contacts": _sum(rows, "contacts"), "lead_contacts": _sum(rows, "lead_contacts"),
        "ads_clicks": _sum(rows, "ads_clicks"), "ads_cost": _sum(rows, "ads_cost"),
        "ads_conversions": _sum(rows, "ads_conversions"),
        "page_ids": [r["id"] for r in rows],
    }


def cell_status(stage: str, m: dict, cfg: dict, gsc: str | None, cross_action_linked: bool) -> tuple[str, list[str]]:
    """gsc is None (no export), "full", or "capped" (the export hit its row limit)."""
    flags = []
    if m["pages"] == 0:
        if stage == "action" and cross_action_linked:
            status = "shared"
        else:
            status = "missing"
    elif m["pages"] < cfg["min_pages"][stage]:
        status = "thin"
    else:
        status = "ok"
    if m["pages"] and gsc and stage != "action":
        if gsc == "capped" and m["pages_in_search_export"] == 0:
            flags.append("not-in-export")  # unknown: never read a truncated export as zero
        elif gsc == "full" and (m["impressions"] or 0) == 0:
            flags.append("invisible")
    if m["pages"] and stage != "action" and m["onward_share"] is not None and m["onward_share"] < cfg["onward_share_min"]:
        flags.append("disconnected")
    if stage == "action" and m["pages"] and m["with_capture"] == 0:
        flags.append("no-capture")
    return status, flags


def verdicts(oid: str, cells: dict, totals: dict, layers: dict, cfg: dict, off_rows: list[dict]) -> dict:
    out = {}
    weak = [s for s in STAGES if cells[s]["status"] in ("missing", "thin")]
    out["content"] = {"assessed": True, "flag": bool(weak),
                      "evidence": {s: cells[s]["status"] for s in STAGES}, "weak_stages": weak}
    disc = [s for s in ("attention", "interest", "desire") if "disconnected" in cells[s]["flags"]]
    nocap = "no-capture" in cells["action"]["flags"]
    out["conversion_path"] = {"assessed": True, "flag": bool(disc) or nocap or cells["action"]["status"] == "missing",
                              "evidence": {"disconnected_stages": disc, "action_without_capture": nocap,
                                           "action_status": cells["action"]["status"]}}
    if layers["gsc_pages"]["present"]:
        # Compared with the other offerings only: an off-ICP tutorial that draws most of the site's
        # impressions must not make every offering look unfindable (that is the ICP-fit finding).
        pages_o = len(off_rows)
        imp_o = sum((r["impressions"] or 0) for r in off_rows)
        ratio = None
        if totals["offering_pages"] and totals["offering_impressions"]:
            ratio = round((imp_o / totals["offering_impressions"]) / (pages_o / totals["offering_pages"]), 2) if pages_o else None
        dm = cells["desire"]["metrics"]
        dpos = dm["position"]
        dimp = dm["impressions"] or 0
        capped = layers["gsc_pages"].get("capped")
        desire_known = not capped or dm["pages_in_search_export"] > 0
        flag = (ratio is not None and ratio < cfg["findability_ratio_min"]) or (
            dm["pages"] > 0 and desire_known and (dimp == 0 or (dpos is not None and dpos > cfg["desire_position_max"])))
        out["findability"] = {"assessed": True, "flag": flag, "evidence": {
            "pages_not_in_export": sum(1 for r in off_rows if not r.get("in_gsc_export")) if capped else None,
            "impression_share_among_offerings": _share(imp_o, totals["offering_impressions"]),
            "page_share_among_offerings": _share(pages_o, totals["offering_pages"]),
            "ratio": ratio, "desire_impressions": dimp, "desire_position": dpos}}
    else:
        out["findability"] = {"assessed": False, "needs": "Search Console pages export"}
    ga = layers["ga4_landing"]
    sess = sum((r["sessions"] or 0) for r in off_rows) if ga["present"] else 0
    if ga["present"] and ga.get("has_channels"):
        ch = Counter()
        for r in off_rows:
            for k, v in (r.get("channels") or {}).items():
                ch[k.lower()] += v
        tot = sum(ch.values())
        dist = sum(v for k, v in ch.items() if k not in ORGANIC_CHANNELS)
        share = _share(dist, tot)
        big_enough = tot >= cfg["conversion_min_sessions"]
        out["distribution"] = {"assessed": big_enough,
                               "flag": big_enough and share is not None and share < cfg["distribution_share_min"],
                               **({} if big_enough else {"needs": f"at least {cfg['conversion_min_sessions']} sessions to judge"}),
                               "evidence": {"sessions": _r(float(tot), 0), "distributed_sessions": _r(float(dist), 0),
                                            "distributed_share": share,
                                            "channels": {k: _r(float(v), 0) for k, v in ch.most_common(8)}}}
    else:
        out["distribution"] = {"assessed": False, "needs": "GA4 landing-page export with the channel-group dimension"}
    hub = layers["hubspot_contacts"]
    if (ga["present"] and ga.get("has_key_events")) or hub["present"]:
        ev = {"sessions": _r(float(sess), 0) if ga["present"] else None}
        flag = False
        if ga["present"] and ga.get("has_key_events"):
            ke = sum((r["key_events"] or 0) for r in off_rows)
            rate = _share(ke, sess)
            site_rate = _share(totals["key_events"], totals["sessions"])
            ev.update({"key_events": _r(float(ke), 0), "key_event_rate": rate, "site_key_event_rate": site_rate})
            if sess >= cfg["conversion_min_sessions"] and site_rate:
                flag = flag or (rate or 0) < cfg["conversion_rate_ratio_min"] * site_rate
        if hub["present"]:
            contacts = sum((r["contacts"] or 0) for r in off_rows)
            leads = sum((r["lead_contacts"] or 0) for r in off_rows)
            ev.update({"first_touch_contacts": contacts, "first_touch_lead_contacts": leads if hub.get("has_lifecycle") else None})
            if ga["present"] and sess >= cfg["conversion_min_sessions"] and contacts == 0:
                flag = True
        small = ga["present"] and sess < cfg["conversion_min_sessions"]
        out["conversion"] = {"assessed": not small, "flag": flag and not small, "evidence": ev,
                             **({"needs": f"at least {cfg['conversion_min_sessions']} sessions to judge"} if small else {})}
    else:
        out["conversion"] = {"assessed": False, "needs": "GA4 key events or a HubSpot first-page-seen export"}
    if layers["ads_landing"]["present"] and layers["gsc_pages"]["present"]:
        ac = sum((r["ads_clicks"] or 0) for r in off_rows)
        oc = sum((r["clicks"] or 0) for r in off_rows)
        share = _share(ac, ac + oc)
        out["paid_reliance"] = {"assessed": True, "flag": share is not None and share > cfg["paid_reliance_share"],
                                "evidence": {"ads_clicks": _r(float(ac), 0), "organic_clicks": _r(float(oc), 0),
                                             "paid_share": share,
                                             "ads_cost": _r(float(sum((r["ads_cost"] or 0) for r in off_rows)), 2)}}
    order = ["content", "conversion_path", "findability", "conversion", "distribution"]
    primary = next((k for k in order if out.get(k, {}).get("flag")), None)
    unassessed = [k for k in order if not out[k]["assessed"]]
    out["primary"] = primary or ("working" if not unassessed else "partial")
    out["not_assessed"] = unassessed
    return out


def months_between(d: str, as_of: date) -> int | None:
    try:
        x = datetime.strptime(d[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    return (as_of.year - x.year) * 12 + as_of.month - x.month


def tokens(title: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (title or "").lower()) if t not in STOP and len(t) > 2}


def duplicates(pages: list[dict], threshold: float) -> list[dict]:
    pairs = []
    by_off = defaultdict(list)
    for p in pages:
        by_off[p["offering"]].append((p, tokens(p["h1"] or p["title"])))
    for rows in by_off.values():
        for i in range(len(rows)):
            a, ta = rows[i]
            if len(ta) < 3:
                continue
            for j in range(i + 1, len(rows)):
                b, tb = rows[j]
                if len(tb) < 3:
                    continue
                jac = len(ta & tb) / len(ta | tb)
                if jac >= threshold:
                    pairs.append({"a": a["id"], "b": b["id"], "a_url": a["path"], "b_url": b["path"],
                                  "a_title": a["h1"] or a["title"], "b_title": b["h1"] or b["title"],
                                  "offering": a["offering"], "similarity": round(jac, 2)})
    return sorted(pairs, key=lambda x: -x["similarity"])[:40]


def brand_split(exports: dict | None, brand_terms: list[str]) -> dict | None:
    q = ((exports or {}).get("sources", {}).get("gsc_queries") or {}).get("queries")
    if not q:
        return None
    terms = [t.strip().lower() for t in brand_terms if t.strip()]
    if not terms:
        return {"assessed": False, "needs": "brand terms in taxonomy.json"}
    rx = re.compile("|".join(re.escape(t) for t in terms), re.I)
    b = [x for x in q if rx.search(x[0])]
    nb = [x for x in q if not rx.search(x[0])]
    tc, ti = sum(x[1] for x in q), sum(x[2] for x in q)
    return {"assessed": True, "brand_terms": terms, "queries": len(q),
            "branded_clicks": _r(float(sum(x[1] for x in b)), 0), "branded_impressions": _r(float(sum(x[2] for x in b)), 0),
            "nonbranded_clicks": _r(float(sum(x[1] for x in nb)), 0), "nonbranded_impressions": _r(float(sum(x[2] for x in nb)), 0),
            "branded_click_share": _share(sum(x[1] for x in b), tc), "branded_impression_share": _share(sum(x[2] for x in b), ti),
            "top_nonbranded": [[x[0], x[1], x[2], x[3]] for x in sorted(nb, key=lambda x: -x[2])[:15]],
            "note": "Search Console hides anonymised queries, so query totals are lower than page totals"}


def valueprop_summary(vp: dict | None) -> dict | None:
    if not vp:
        return None
    rows, crit_tot = [], Counter()
    for s in vp.get("scopes", []):
        crit = s.get("criteria", {})
        score = sum(int(c.get("score", 0)) for c in crit.values())
        rows.append({"scope": s["scope"], "url": s.get("url", ""), "score": score, "max": 2 * len(crit),
                     "share": _share(score, 2 * len(crit)),
                     "criteria": {k: {"score": v.get("score"), "quote": v.get("quote", ""), "note": v.get("note", "")}
                                  for k, v in crit.items()}})
        for k, v in crit.items():
            crit_tot[k] += int(v.get("score", 0))
    n = len(rows) or 1
    return {"scopes": rows, "criterion_avg": {k: round(v / n, 2) for k, v in crit_tot.items()},
            "weakest": [k for k, _ in sorted(crit_tot.items(), key=lambda kv: kv[1])[:2]]}


def analyze(run_dir: Path, cfg: dict, as_of: date) -> dict:
    data = load_run(run_dir)
    tax = data["taxonomy"]
    pages, excluded = build_pages(data)
    ex = attach_exports(pages, data["exports"])
    layers = ex["layers"]
    onward(pages)
    gsc = ("capped" if layers["gsc_pages"]["capped"] else "full") if layers["gsc_pages"]["present"] else None

    offerings = [{"id": o["id"], "name": o["name"]} for o in tax["offerings"]]
    rows_all = [{"id": k, "name": v} for k, v in RESERVED_OFFERINGS.items()]
    totals = {"pages": len(pages), "impressions": sum((p["impressions"] or 0) for p in pages),
              "clicks": sum((p["clicks"] or 0) for p in pages), "sessions": sum((p["sessions"] or 0) for p in pages),
              "key_events": sum((p["key_events"] or 0) for p in pages),
              "contacts": sum((p["contacts"] or 0) for p in pages)}
    tax_ids = {o["id"] for o in tax["offerings"]}
    totals["offering_pages"] = sum(1 for p in pages if p["offering"] in tax_ids)
    totals["offering_impressions"] = sum((p["impressions"] or 0) for p in pages if p["offering"] in tax_ids)

    cross_actions = {p["path"] for p in pages if p["offering"] == "cross" and p["stage"] == "action"}
    matrix, per_offering = {}, {}
    for o in offerings + rows_all:
        oid = o["id"]
        off_rows = [p for p in pages if p["offering"] == oid]
        if oid in RESERVED_OFFERINGS and not off_rows:
            continue
        cells = {}
        desire_rows = [p for p in off_rows if p["stage"] == "desire"]
        cross_linked = any(path_key(u) in cross_actions for p in desire_rows for u in p["body_links"]) or any(
            path_key(u) in cross_actions for p in off_rows for u in p["body_links"])
        for s in STAGES:
            rows = [p for p in off_rows if p["stage"] == s]
            m = cell_metrics(rows)
            status, flags = cell_status(s, m, cfg, gsc, cross_linked)
            cells[s] = {"metrics": m, "status": status, "flags": flags}
        matrix[oid] = {"name": o["name"], "reserved": oid in RESERVED_OFFERINGS, "cells": cells,
                       "pages": len(off_rows), "secondary_pages": sum(1 for p in pages if p.get("secondary_offering") == oid)}
        if oid not in RESERVED_OFFERINGS:
            v = verdicts(oid, cells, totals, layers, cfg, off_rows)
            breaks = next((s for s in STAGES if cells[s]["status"] in ("missing", "thin")), None)
            top = sorted(off_rows, key=lambda p: -((p["impressions"] or 0) + (p["sessions"] or 0) * 10 + (p["contacts"] or 0) * 1000))[:6]
            per_offering[oid] = {"name": o["name"], "pages": len(off_rows), "journey_breaks_at": breaks,
                                 "verdicts": v, "top_pages": [p["id"] for p in top],
                                 "icp_share": _share(sum(1 for p in off_rows if p["icp_fit"] in ("icp", "adjacent")), len(off_rows))}

    def dist(key, rows, values=None):
        c = Counter(r[key] for r in rows)
        keys = values or [k for k, _ in c.most_common()]
        return {k: c.get(k, 0) for k in keys}

    icp = {}
    for fit in ICP_FIT:
        rows = [p for p in pages if p["icp_fit"] == fit]
        icp[fit] = {"pages": len(rows), "page_share": _share(len(rows), len(pages)),
                    "impressions": _sum(rows, "impressions"), "impression_share": _share(sum((r["impressions"] or 0) for r in rows), totals["impressions"]) if gsc else None,
                    "sessions": _sum(rows, "sessions"), "contacts": _sum(rows, "contacts")}

    fresh = Counter()
    stale = 0
    dated = 0
    for p in pages:
        d = p["modified"] or p["published"]
        if d:
            dated += 1
            fresh[d[:4]] += 1
            mb = months_between(d, as_of)
            if mb is not None and mb > cfg["stale_months"]:
                stale += 1
    lo, hi = cfg["striking_position"]
    striking = sorted([p for p in pages if p.get("position") and lo <= p["position"] <= hi
                       and (p["impressions"] or 0) >= cfg["striking_min_impressions"] and p["stage"] != "action"],
                      key=lambda p: -(p["impressions"] or 0))[:25]
    action_nocap = [p["id"] for p in pages if p["stage"] == "action" and not p["has_capture"]]
    low_conf = [p["id"] for p in pages if p["confidence"] == "low"]

    metrics = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "as_of": as_of.isoformat(),
        "site": {"host": data["crawl"]["meta"]["host"], "start_url": data["crawl"]["meta"]["start_url"],
                 "crawled_at": data["crawl"]["meta"]["crawled_at"], "company": tax.get("company", ""),
                 "positioning": tax.get("positioning", ""), "icp": tax.get("icp", "")},
        "config": cfg,
        "crawl": {k: data["crawl"]["meta"][k] for k in ("html_pages", "urls_checked", "sitemap_urls", "cap_reached",
                                                        "max_pages", "blocked_count", "warnings", "languages")},
        "layers": layers, "export_match": ex["match"],
        "inventory": {
            "html_pages": len(data["pages"]["pages"]), "content_pages": len(pages), "excluded": len(excluded),
            "excluded_by_reason": dict(Counter(p["excluded"] for p in excluded).most_common()),
            "by_stage": dist("stage", pages, STAGES), "by_offering": dist("offering", pages),
            "by_content_type": dist("content_type", pages), "by_confidence": dist("confidence", pages, ["high", "med", "low"]),
            "documents_linked": sum(p.get("documents", 0) for p in pages),
            "with_capture": sum(1 for p in pages if p["has_capture"]),
        },
        "totals": {k: _r(float(v), 2) for k, v in totals.items()},
        "offerings": [o["id"] for o in offerings],
        "matrix": matrix, "per_offering": per_offering, "icp_fit": icp,
        "freshness": {"dated_pages": dated, "undated_pages": len(pages) - dated, "by_year": dict(sorted(fresh.items())),
                      "stale_pages": stale, "stale_share_of_dated": _share(stale, dated), "stale_months": cfg["stale_months"]},
        "brand_split": brand_split(data["exports"], tax.get("brand_terms", [])),
        "striking_distance": [p["id"] for p in striking],
        "duplicates": duplicates(pages, cfg["duplicate_jaccard"]),
        "action_without_capture": action_nocap,
        "valueprop": valueprop_summary(data["valueprop"]),
        "low_confidence": low_conf,
        "median_words": statistics.median([p["word_count"] for p in pages]) if pages else 0,
    }
    keep = ("id", "url", "path", "title", "h1", "type_hint", "offering", "secondary_offering", "stage", "content_type",
            "icp_fit", "confidence", "evidence", "note", "word_count", "published", "modified", "noindex",
            "has_capture", "onward", "links_to_desire_action", "links_to_action", "inbound_body_links",
            "in_gsc_export", "impressions", "clicks", "position", "sessions", "key_events", "contacts", "lead_contacts",
            "ads_clicks", "ads_cost", "ads_conversions")
    metrics["pages"] = {p["id"]: {k: p.get(k) for k in keep} for p in pages}
    metrics["excluded_pages"] = [{"id": p["id"], "url": p["url"], "reason": p["excluded"], "title": p["title"]} for p in excluded]
    return metrics


def main(argv=None) -> int:
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--config", help="JSON file overriding thresholds in DEFAULTS")
    ap.add_argument("--as-of", help="Reference date for freshness (default today)")
    args = ap.parse_args(argv)
    cfg = {**DEFAULTS, **(read_json(args.config) if args.config else {})}
    as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date() if args.as_of else date.today()
    run_dir = Path(args.run_dir)
    m = analyze(run_dir, cfg, as_of)
    write_json(run_dir / "metrics.json", m)
    inv = m["inventory"]
    present = ", ".join(k for k, v in m["layers"].items() if v["present"]) or "site only"
    print(f"{inv['content_pages']} content pages analysed ({inv['excluded']} excluded); layers: {present}")
    print("\nOffering x AIDA (pages; status)")
    print("| Offering | " + " | ".join(s.title() for s in STAGES) + " | Primary verdict |")
    print("|---|" + "---|" * (len(STAGES) + 1))
    for oid, row in m["matrix"].items():
        cells = " | ".join(f"{row['cells'][s]['metrics']['pages']} {row['cells'][s]['status']}"
                           + (f" ({', '.join(row['cells'][s]['flags'])})" if row['cells'][s]['flags'] else "")
                           for s in STAGES)
        verdict = m["per_offering"].get(oid, {}).get("verdicts", {}).get("primary", "-")
        print(f"| {row['name']} | {cells} | {verdict} |")
    for kind, mm in m["export_match"].items():
        share = next((v for k, v in mm.items() if k.endswith("_matched_share")), mm.get("matched_share"))
        if share is not None and share < 0.7:
            print(f"warning: only {share:.0%} of {kind} volume matched crawled pages; check the host or crawl coverage")
    print(f"\nWrote {run_dir / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
