"""Build the report: one self-contained HTML page, a markdown source and pages.csv.

Reads metrics.json (numbers, from analyze.py) and narrative.json (words, written by the model)
from the run folder. Every number in narrative.json must exist in metrics.json; the build stops
and lists the ones that do not (exit code 1), unless --allow-unverified is passed.

    python build_report.py --run-dir RUN [--out-name content-audit-example.com-2026-01-31]
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import STAGE_LABELS, STAGES, read_json, utf8_console  # noqa: E402

SKILL_DIR = Path(__file__).resolve().parent.parent
GAP_LABELS = {"content": "Content gap", "conversion_path": "Conversion path gap", "findability": "Findability gap",
              "conversion": "Conversion gap", "distribution": "Distribution gap", "paid_reliance": "Paid reliance",
              "working": "Working", "partial": "Partial read", "valueprop": "Value proposition gap"}
GAP_BADGE = {"content": "bad", "conversion_path": "bad", "findability": "warn", "conversion": "bad",
             "distribution": "warn", "paid_reliance": "warn", "working": "ok", "partial": "neutral", "valueprop": "warn"}
VP_LABELS = {"category": "What it is", "audience": "Who it is for", "outcome": "Outcome", "differentiation":
             "Why this company", "proof": "Proof", "next_step": "Next step"}
STATUS_TEXT = {"ok": "covered", "thin": "thin", "missing": "missing", "shared": "shared"}
FLAG_TEXT = {"invisible": "not found in search", "disconnected": "no onward step", "no-capture": "no capture",
             "not-in-export": "not in the search export"}
TELLS = re.compile(r"\b(delve|leverag\w*|robust|seamless\w*|unlock\w*|landscape|game[- ]changer|holistic|"
                   r"synerg\w*|cutting[- ]edge|in today'?s|tapestry|testament|elevate\w*|empower\w*|"
                   r"navigat\w* the|it'?s not just|beyond the)\b", re.I)
NUM = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?")


# ---------------------------------------------------------------- number check
def flatten(obj, out: list[float]) -> None:
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        out.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            flatten(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            flatten(v, out)
    elif isinstance(obj, str):
        for m in NUM.findall(obj):
            try:
                out.append(float(m.rstrip("%").replace(",", "")))
            except ValueError:
                pass


def unverified_numbers(narrative: dict, metrics: dict) -> list[str]:
    values: list[float] = []
    flatten(metrics, values)
    pool = set()
    for v in values:
        pool.add(round(v, 2))
        if -1.0 <= v <= 1.0:
            pool.add(round(v * 100, 2))
    # derived values the narrative may reasonably state: counts of offerings, ranks
    texts: list[str] = []

    def walk(o, key=""):
        if isinstance(o, str):
            if key not in ("rank", "handoff", "url", "offering", "stage", "gap"):
                texts.append(o)
        elif isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)

    walk(narrative)
    bad = []
    for t in texts:
        for raw in NUM.findall(t):
            s = raw.rstrip("%").replace(",", "")
            try:
                n = float(s)
            except ValueError:
                continue
            if raw.endswith("%") is False and n.is_integer() and 0 <= n <= 12:
                continue
            if 1990 <= n <= 2100 and n.is_integer():
                continue
            dec = len(s.split(".")[1]) if "." in s else 0
            tol = 0.5 * 10 ** -dec + 1e-9
            if not any(abs(n - v) <= tol for v in pool):
                bad.append(f"{raw}  in: \"{t[:90]}\"")
    return bad


def style_warnings(narrative: dict) -> list[str]:
    out = []

    def walk(o, key=""):
        if isinstance(o, str):
            for m in TELLS.findall(o):
                out.append(f"'{m}' in {key or 'text'}")
            if key in ("title", "heading") and o.rstrip().endswith("."):
                out.append(f"heading ends with a period: {o}")
            if key == "title" and re.match(r"(?i)from .+ to ", o):
                out.append(f"'From X to Y' title: {o}")
        elif isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)

    walk(narrative)
    return out


# ---------------------------------------------------------------- formatting
def e(x) -> str:
    return html.escape("" if x is None else str(x))


def fmt(n, pct=False, money=False) -> str:
    if n is None:
        return "–"
    if pct:
        return f"{n * 100:.0f}%"
    if isinstance(n, float) and not n.is_integer():
        return f"{n:,.1f}" if not money else f"{n:,.0f}"
    return f"{int(n):,}"


def heading(text: str) -> str:
    return text.rstrip().rstrip(".")


def para(text: str | None) -> str:
    if not text:
        return ""
    parts = [p.strip() for p in str(text).split("\n\n") if p.strip()]
    return "".join(f"<p>{e(p)}</p>" for p in parts)


def bar_rows(items: list[tuple[str, float, str]], maxv: float | None = None, alt=False) -> str:
    maxv = maxv or max([v for _, v, _ in items] + [1])
    rows = []
    for label, v, shown in items:
        w = 0 if not maxv else max(0.0, min(100.0, 100 * v / maxv))
        rows.append(f'<span>{e(label)}</span><span class="track"><span class="fill{" alt" if alt else ""}" '
                    f'style="width:{w:.1f}%"></span></span><span class="v">{e(shown)}</span>')
    return f'<div class="bars">{"".join(rows)}</div>'


def table(head: list[str], rows: list[list[str]], num_cols: set[int] = frozenset(), cls="") -> str:
    th = "".join(f'<th{" class=num" if i in num_cols else ""}>{h}</th>' for i, h in enumerate(head))
    body = "".join("<tr>" + "".join(f'<td{" class=num" if i in num_cols else ""}>{c}</td>' for i, c in enumerate(r))
                   + "</tr>" for r in rows)
    return f'<div class="table-wrap {cls}"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


# ---------------------------------------------------------------- sections
def journey_map(m: dict) -> str:
    L = m["layers"]
    rows = []
    for oid, row in m["matrix"].items():
        cells = []
        for s in STAGES:
            c = row["cells"][s]
            mm = c["metrics"]
            sub = []
            if mm["pages"]:
                if L["gsc_pages"]["present"] and s != "action" and mm["impressions"] is not None:
                    sub.append(f"{fmt(mm['impressions'])} impr.")
                if L["ga4_landing"]["present"] and mm["sessions"] is not None:
                    sub.append(f"{fmt(mm['sessions'])} sessions")
                if L["hubspot_contacts"]["present"] and mm["contacts"] is not None:
                    sub.append(f"{fmt(mm['contacts'])} contact{'' if mm['contacts'] == 1 else 's'}")
                if mm["onward_share"] is not None:
                    sub.append(f"{fmt(mm['onward_share'], pct=True)} with an onward step")
            flags = "" if row["reserved"] else ", ".join(FLAG_TEXT.get(f, f) for f in c["flags"])
            status = "" if row["reserved"] else STATUS_TEXT[c["status"]]
            cells.append(
                f'<td class="cell st-{"reserved" if row["reserved"] else c["status"]}"><button type="button" data-offering="{e(oid)}" data-stage="{s}" '
                f'aria-label="{e(row["name"])}, {STAGE_LABELS[s]}: {mm["pages"]} pages{", " + status if status else ""}">'
                f'<span class="count">{mm["pages"]}</span>' + (f'<span class="status">{status}</span>' if status else "")
                + (f'<span class="flags">{e(flags)}</span>' if flags else "")
                + (f'<span class="sub">{e(" · ".join(sub))}</span>' if sub else "") + "</button></td>")
        v = m["per_offering"].get(oid, {}).get("verdicts", {}).get("primary")
        badge = (f'<span class="badge {GAP_BADGE.get(v, "neutral")}">{e(GAP_LABELS.get(v, v))}</span>' if v
                 else '<span class="muted">context row, not diagnosed</span>')
        rows.append(f'<tr class="{"reserved" if row["reserved"] else ""}"><td><strong>{e(row["name"])}</strong>'
                    f'<br><span class="muted">{row["pages"]} page{"" if row["pages"] == 1 else "s"}</span></td>'
                    f'{"".join(cells)}<td>{badge}</td></tr>')
    head = "<th>Offering</th>" + "".join(f"<th>{STAGE_LABELS[s]}</th>" for s in STAGES) + "<th>Primary gap</th>"
    legend = ('<div class="legend"><span><span class="badge ok">covered</span> enough pages</span>'
              '<span><span class="badge warn">thin</span> below the minimum</span>'
              '<span><span class="badge bad">missing</span> no page at this stage</span>'
              '<span><span class="badge accent">shared</span> a cross-offering page covers it</span>'
              '<span>Select a cell to list its pages</span></div>')
    return (f'<div class="table-wrap"><table class="journey"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>{legend}')


def verdict_table(v: dict) -> str:
    rows = []
    for k in ("content", "conversion_path", "findability", "conversion", "distribution", "paid_reliance"):
        if k not in v:
            continue
        d = v[k]
        if not d["assessed"]:
            read = '<span class="badge neutral">not assessed</span>'
            ev = e(d.get("needs", ""))
        else:
            read = f'<span class="badge {"bad" if d["flag"] else "ok"}">{"gap" if d["flag"] else "no gap"}</span>'
            ev = e("; ".join(f"{a.replace('_', ' ')}: {fmt_ev(b)}" for a, b in d.get("evidence", {}).items()
                             if b not in (None, [], {})))
        rows.append([e(GAP_LABELS[k]), read, ev])
    return table(["Check", "Read", "Evidence"], rows)


def fmt_ev(b) -> str:
    if isinstance(b, float):
        return f"{b * 100:.0f}%" if 0 <= b <= 1 else f"{b:,.1f}"
    if isinstance(b, dict):
        return ", ".join(f"{k} {fmt_ev(v)}" for k, v in b.items())
    if isinstance(b, list):
        return ", ".join(str(x) for x in b)
    if isinstance(b, int):
        return f"{b:,}"
    return str(b)


def page_link(p: dict) -> str:
    return f'<a href="{e(p["url"])}">{e(p["path"])}</a>'


def offerings_section(m: dict, n: dict) -> str:
    out = []
    for oid, po in m["per_offering"].items():
        v = po["verdicts"]
        prim = v["primary"]
        breaks = po["journey_breaks_at"]
        tops = [m["pages"][pid] for pid in po["top_pages"]]
        top_rows = [[page_link(p), STAGE_LABELS[p["stage"]], e(p["content_type"]), fmt(p.get("impressions")),
                     fmt(p.get("sessions")), fmt(p.get("contacts"))] for p in tops]
        note = n.get("offering_notes", {}).get(oid, "")
        out.append(
            f'<details{" open" if prim not in ("working",) else ""}><summary><strong>{e(po["name"])}</strong>'
            f'<span class="badge {GAP_BADGE.get(prim, "neutral")}">{e(GAP_LABELS.get(prim, prim))}</span>'
            f'<span class="muted">{po["pages"]} pages · '
            f'{"journey breaks at " + STAGE_LABELS[breaks] if breaks else "every stage covered"}</span></summary>'
            f'<div class="body stack">{para(note)}{verdict_table(v)}'
            f'<h4>Pages carrying the most demand</h4>'
            + table(["Page", "Stage", "Type", "Impr.", "Sessions", "Contacts"], top_rows, {3, 4, 5})
            + "</div></details>")
    return "".join(out)


def valueprop_section(m: dict, n: dict) -> str:
    vp = m.get("valueprop")
    if not vp:
        return '<p class="note">Value proposition not scored in this run.</p>'
    names = {oid: r["name"] for oid, r in m["matrix"].items()}
    names["homepage"] = "Homepage"
    head = ["Scope"] + list(VP_LABELS.values()) + ["Total"]
    rows, quotes = [], []
    for s in vp["scopes"]:
        cells = [f"<strong>{e(names.get(s['scope'], s['scope']))}</strong>"]
        for k in VP_LABELS:
            sc = s["criteria"].get(k, {}).get("score") or 0
            word, tone = {2: ("clear", "ok"), 1: ("partial", "warn"), 0: ("missing", "bad")}[sc]
            cells.append(f'<span class="badge {tone}" title="{sc} of 2">{word}</span>')
        cells.append(f"{s['score']} / {s['max']}")
        rows.append(cells)
        items = "".join(
            f'<div class="finding"><span class="k">{VP_LABELS[k]} · {c.get("score", 0)}/2</span><span>'
            + (f"<blockquote>{e(c['quote'])}</blockquote>" if c.get("quote") else "")
            + (f"<span>{e(c['note'])}</span>" if c.get("note") else "") + "</span></div>"
            for k, c in s["criteria"].items())
        quotes.append(f'<details><summary><strong>{e(names.get(s["scope"], s["scope"]))}</strong>'
                      f'<span class="muted">{s["score"]} of {s["max"]} · {e(s["url"])}</span></summary>'
                      f'<div class="body">{items}</div></details>')
    return (para(n.get("valueprop_read")) + table(head, rows, {7}) +
            '<p class="muted">Scored 0 to 2 per criterion from the page itself; every point above 0 has a quote.</p>'
            + "".join(quotes))


def findability_section(m: dict, n: dict) -> str:
    if not m["layers"]["gsc_pages"]["present"]:
        return ('<p class="note">Not measured. Add a Search Console export to the ingest folder and run the '
                'skill again to see impressions, positions and branded demand per offering and stage.</p>')
    parts = [para(n.get("findability_read"))]
    bs = m.get("brand_split")
    if bs and bs.get("assessed"):
        parts.append('<h3>Branded and non-branded search</h3>' + bar_rows([
            ("Branded clicks", bs["branded_clicks"], fmt(bs["branded_clicks"])),
            ("Non-branded clicks", bs["nonbranded_clicks"], fmt(bs["nonbranded_clicks"]))]) +
            f'<p class="muted">Brand terms: {e(", ".join(bs["brand_terms"]))}. {e(bs["note"])}.</p>')
        if bs["top_nonbranded"]:
            parts.append(table(["Top non-branded query", "Clicks", "Impr.", "Position"],
                               [[e(q[0]), fmt(q[1]), fmt(q[2]), fmt(q[3])] for q in bs["top_nonbranded"]], {1, 2, 3}))
    items = []
    for oid, row in m["matrix"].items():
        for s in ("attention", "interest", "desire"):
            imp = row["cells"][s]["metrics"]["impressions"] or 0
            items.append((f"{row['name']} · {STAGE_LABELS[s]}", imp, fmt(imp)))
    parts.append("<h3>Search impressions by offering and stage</h3>" + bar_rows(items))
    sd = [m["pages"][pid] for pid in m["striking_distance"]]
    if sd:
        parts.append(f"<h3>Pages close to page one</h3><p class=\"muted\">Position {m['config']['striking_position'][0]} "
                     f"to {m['config']['striking_position'][1]} with at least {m['config']['striking_min_impressions']} impressions.</p>"
                     + table(["Page", "Offering", "Stage", "Impr.", "Clicks", "Position"],
                             [[page_link(p), e(m["matrix"].get(p["offering"], {}).get("name", p["offering"])),
                               STAGE_LABELS[p["stage"]], fmt(p["impressions"]), fmt(p["clicks"]), fmt(p["position"])]
                              for p in sd], {3, 4, 5}))
    return "".join(parts)


def traffic_section(m: dict, n: dict) -> str:
    L = m["layers"]
    if not (L["ga4_landing"]["present"] or L["hubspot_contacts"]["present"] or L["ads_landing"]["present"]):
        return ('<p class="note">Not measured. Add GA4, HubSpot or Google Ads exports to the ingest folder to see '
                'which offerings and stages bring traffic and leads.</p>')
    head, rows = ["Offering"], []
    if L["ga4_landing"]["present"]:
        head += ["Sessions", "Key events", "Rate"]
    if L["hubspot_contacts"]["present"]:
        head += ["First-touch contacts", "Lead-stage"]
    if L["ads_landing"]["present"]:
        head += ["Ads clicks", "Ads cost"]
    for oid, po in m["per_offering"].items():
        cells = [e(po["name"])]
        tot = {k: sum((m["matrix"][oid]["cells"][s]["metrics"][k] or 0) for s in STAGES)
               for k in ("sessions", "key_events", "contacts", "lead_contacts", "ads_clicks", "ads_cost")}
        if L["ga4_landing"]["present"]:
            cells += [fmt(tot["sessions"]), fmt(tot["key_events"]),
                      fmt(tot["key_events"] / tot["sessions"], pct=True) if tot["sessions"] else "–"]
        if L["hubspot_contacts"]["present"]:
            cells += [fmt(tot["contacts"]), fmt(tot["lead_contacts"]) if L["hubspot_contacts"].get("has_lifecycle") else "–"]
        if L["ads_landing"]["present"]:
            cells += [fmt(tot["ads_clicks"]), fmt(tot["ads_cost"], money=True)]
        rows.append(cells)
    parts = [para(n.get("traffic_read")), table(head, rows, set(range(1, len(head))))]
    items = []
    for oid, row in m["matrix"].items():
        for s in STAGES:
            c = row["cells"][s]["metrics"]["contacts"]
            if c:
                items.append((f"{row['name']} · {STAGE_LABELS[s]}", c, fmt(c)))
    if items:
        parts.append("<h3>Where first-touch contacts entered</h3>" + bar_rows(items))
    return "".join(parts)


def content_state_section(m: dict, n: dict) -> str:
    inv = m["inventory"]
    parts = [para(n.get("content_state_read"))]
    parts.append("<h3>Pages by AIDA stage</h3>" + bar_rows(
        [(STAGE_LABELS[s], inv["by_stage"][s], fmt(inv["by_stage"][s])) for s in STAGES]))
    parts.append("<h3>Pages by content type</h3>" + bar_rows(
        [(k, v, fmt(v)) for k, v in sorted(inv["by_content_type"].items(), key=lambda kv: -kv[1]) if v], alt=True))
    icp_rows = []
    for fit, d in m["icp_fit"].items():
        icp_rows.append([e({"icp": "Written for the ICP", "adjacent": "Adjacent audience", "off": "Off-ICP audience",
                            "unclear": "Unclear"}[fit]), fmt(d["pages"]), fmt(d["page_share"], pct=True),
                         fmt(d["impression_share"], pct=True) if d["impression_share"] is not None else "–",
                         fmt(d["sessions"]), fmt(d["contacts"])])
    parts.append("<h3>Who the content is written for</h3>" + table(
        ["Audience", "Pages", "Share of pages", "Share of impressions", "Sessions", "Contacts"], icp_rows, {1, 2, 3, 4, 5}))
    fr = m["freshness"]
    if fr["by_year"]:
        parts.append(f"<h3>Last published or updated</h3>" + bar_rows([(y, c, fmt(c)) for y, c in fr["by_year"].items()], alt=True)
                     + f'<p class="muted">{fr["stale_pages"]} of {fr["dated_pages"]} dated pages are older than '
                       f'{fr["stale_months"]} months; {fr["undated_pages"]} pages carry no date.</p>')
    if m["duplicates"]:
        parts.append("<h3>Possible duplicates to consolidate</h3>" + table(
            ["Page A", "Page B", "Title overlap"],
            [[e(d["a_url"]), e(d["b_url"]), fmt(d["similarity"], pct=True)] for d in m["duplicates"][:20]], {2}))
    if m["action_without_capture"]:
        parts.append("<h3>Action pages with no form, booking link or email link</h3><ul>" + "".join(
            f"<li>{page_link(m['pages'][pid])}</li>" for pid in m["action_without_capture"][:30]) + "</ul>")
    return "".join(parts)


def explorer(m: dict) -> str:
    names = {oid: r["name"] for oid, r in m["matrix"].items()}
    rows = []
    for p in m["pages"].values():
        rows.append(
            f'<tr data-offering="{e(p["offering"])}" data-stage="{p["stage"]}" data-icp="{p["icp_fit"]}" '
            f'data-conf="{p["confidence"]}" data-text="{e((p["path"] + " " + (p["h1"] or p["title"])).lower())}">'
            f'<td>{page_link(p)}<br>{e(p["h1"] or p["title"])}<br><span class="muted">{e(p["evidence"])}</span></td>'
            f'<td>{e(names.get(p["offering"], p["offering"]))}</td><td>{STAGE_LABELS[p["stage"]]}</td>'
            f'<td>{e(p["content_type"])}</td><td>{e(p["icp_fit"])}</td><td>{e(p["confidence"])}</td>'
            f'<td>{"yes" if p["onward"] else ("–" if p["onward"] is None else "no")}</td>'
            f'<td class="num">{fmt(p.get("impressions"))}</td><td class="num">{fmt(p.get("sessions"))}</td>'
            f'<td class="num">{fmt(p.get("contacts"))}</td></tr>')
    opt = lambda vals: "".join(f'<option value="{e(k)}">{e(v)}</option>' for k, v in vals)  # noqa: E731
    controls = (
        '<div class="explorer-controls">'
        f'<select data-f="offering" aria-label="Offering"><option value="">All offerings</option>{opt(names.items())}</select>'
        f'<select data-f="stage" aria-label="Stage"><option value="">All stages</option>{opt(STAGE_LABELS.items())}</select>'
        f'<select data-f="icp" aria-label="Audience"><option value="">All audiences</option>{opt([(x, x) for x in ("icp", "adjacent", "off", "unclear")])}</select>'
        f'<select data-f="conf" aria-label="Confidence"><option value="">All confidence</option>{opt([(x, x) for x in ("high", "med", "low")])}</select>'
        '<input type="search" data-f="text" placeholder="Search URL or title" aria-label="Search">'
        '<span class="count" id="explorer-count"></span></div>')
    head = "".join(f"<th{' class=num' if h in ('Impr.', 'Sessions', 'Contacts') else ''}>{h}</th>" for h in
                   ["Page and evidence", "Offering", "Stage", "Type", "Audience", "Conf.", "Onward", "Impr.", "Sessions", "Contacts"])
    return (controls + f'<div class="table-wrap tall"><table id="explorer"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def method_section(m: dict, n: dict) -> str:
    L, mt = m["layers"], m["export_match"]
    label = {"gsc_pages": "Search Console pages", "gsc_queries": "Search Console queries", "ga4_landing": "GA4 landing pages",
             "hubspot_contacts": "HubSpot contacts", "ads_landing": "Google Ads landing pages"}
    rows = [["Website crawl", '<span class="badge ok">present</span>', e(m["site"]["crawled_at"][:10]),
             f'{m["crawl"]["html_pages"]} HTML pages', "–"]]
    for k, v in L.items():
        match = mt.get(k, {})
        share = next((vv for kk, vv in match.items() if kk.endswith("_matched_share")), match.get("matched_share"))
        status = ("truncated", "warn") if v.get("capped") else (("present", "ok") if v["present"] else ("absent", "neutral"))
        rows.append([label[k], f'<span class="badge {status[1]}">{status[0]}</span>',
                     e(v["window"] or "–"), fmt(v["rows"]) + " rows" if v["present"] else "–",
                     fmt(share, pct=True) if share is not None else "–"])
    parts = ["<h3>Data layers</h3>", table(["Source", "Status", "Window", "Volume", "Matched to crawled pages"], rows)]
    warns = list(m["crawl"]["warnings"])
    for k, v in L.items():
        if v.get("capped"):
            warns.append(f"{label[k]} export stopped at its download row limit. Pages missing from it show as "
                         "no data, not zero; export it in slices by site section for full coverage.")
    if warns:
        parts.append("<h3>Crawl warnings</h3><ul>" + "".join(f"<li>{e(w)}</li>" for w in warns) + "</ul>")
    inv = m["inventory"]
    parts.append("<h3>Scope</h3>" + table(["Measure", "Value"], [
        ["HTML pages crawled", fmt(inv["html_pages"])], ["Content pages classified", fmt(inv["content_pages"])],
        ["Excluded (" + e(", ".join(f"{k} {v}" for k, v in inv["excluded_by_reason"].items())) + ")", fmt(inv["excluded"])],
        ["Classification confidence high / med / low", " / ".join(fmt(inv["by_confidence"][k]) for k in ("high", "med", "low"))],
        ["Page cap", f'{m["crawl"]["max_pages"]}{" (reached)" if m["crawl"]["cap_reached"] else ""}'],
    ], {1}))
    cfg = m["config"]
    parts.append("<h3>How the grid is read</h3><ul>"
                 "<li>Attention: the page explains a problem or topic, vendor-neutral. Interest: it explores ways to solve it. "
                 "Desire: it argues for this company (services, proof, pricing, comparisons). Action: its main job is a hand-raise "
                 "(contact, demo, quote, gated download, sign-up).</li>"
                 f"<li>Thin means fewer pages than the minimum per stage: {e(json.dumps(cfg['min_pages']))}.</li>"
                 f"<li>No onward step means under {fmt(cfg['onward_share_min'], pct=True)} of the cell's pages link in the body to a "
                 "Desire or Action page of the same offering (or a cross-offering one), or carry a form or booking link themselves. "
                 "Navigation and footer links do not count.</li>"
                 "<li>Each page counts once, under its primary offering.</li></ul>")
    if n.get("limits"):
        parts.append("<h3>Limits of this read</h3><ul>" + "".join(f"<li>{e(x)}</li>" for x in n["limits"]) + "</ul>")
    low = [m["pages"][pid] for pid in m["low_confidence"]]
    if low:
        parts.append(f"<details><summary><strong>Low-confidence classifications</strong><span class=\"muted\">{len(low)} pages "
                     "worth a human check</span></summary><div class=\"body\">" + table(
                         ["Page", "Offering", "Stage", "Note"],
                         [[page_link(p), e(p["offering"]), STAGE_LABELS[p["stage"]], e(p["note"] or p["evidence"])] for p in low[:80]])
                     + "</div></details>")
    return "".join(parts)


SCRIPT = """
<script>
(function () {
  var t = document.getElementById('explorer'); if (!t) return;
  var ctl = document.querySelectorAll('.explorer-controls [data-f]');
  var count = document.getElementById('explorer-count');
  function apply() {
    var f = {}; ctl.forEach(function (c) { f[c.dataset.f] = c.value.trim().toLowerCase(); });
    var n = 0;
    t.querySelectorAll('tbody tr').forEach(function (r) {
      var ok = (!f.offering || r.dataset.offering === f.offering) && (!f.stage || r.dataset.stage === f.stage) &&
               (!f.icp || r.dataset.icp === f.icp) && (!f.conf || r.dataset.conf === f.conf) &&
               (!f.text || r.dataset.text.indexOf(f.text) !== -1);
      r.classList.toggle('hidden', !ok); if (ok) n++;
    });
    count.textContent = n + ' pages';
  }
  ctl.forEach(function (c) { c.addEventListener('input', apply); });
  document.querySelectorAll('table.journey button[data-offering]').forEach(function (b) {
    b.addEventListener('click', function () {
      ctl.forEach(function (c) {
        if (c.dataset.f === 'offering') c.value = b.dataset.offering;
        else if (c.dataset.f === 'stage') c.value = b.dataset.stage;
        else c.value = '';
      });
      apply(); document.getElementById('explorer-section').scrollIntoView({behavior: 'smooth', block: 'start'});
    });
  });
  apply();
})();
</script>"""


def render_html(m: dict, n: dict, paths: dict) -> str:
    css = (SKILL_DIR / "assets" / "report.css").read_text(encoding="utf-8")
    site = m["site"]
    L = m["layers"]
    title = heading(n.get("title") or f"Content audit of {site['host']}")
    layer_names = [("Site", True), ("Search Console", L["gsc_pages"]["present"]), ("GA4", L["ga4_landing"]["present"]),
                   ("HubSpot", L["hubspot_contacts"]["present"]), ("Google Ads", L["ads_landing"]["present"])]
    layers = "".join(f'<span class="badge {"ok" if on else "neutral"}">{e(nm)}{"" if on else " · absent"}</span>'
                     for nm, on in layer_names)
    inv = m["inventory"]
    cells = [c for oid, r in m["matrix"].items() if not r["reserved"] for c in r["cells"].values()]
    covered = sum(1 for c in cells if c["status"] in ("ok", "shared"))
    stats = [(fmt(inv["content_pages"]), "content pages"), (str(len(m["offerings"])), "offerings"),
             (f"{covered} of {len(cells)}", "journey stages covered")]
    vp = m.get("valueprop")
    if vp and vp["scopes"]:
        avg = sum(s["share"] or 0 for s in vp["scopes"]) / len(vp["scopes"])
        stats.append((f"{avg * 100:.0f}%", "value proposition clarity"))
    if m.get("brand_split") and m["brand_split"].get("assessed"):
        stats.append((fmt(1 - (m["brand_split"]["branded_click_share"] or 0), pct=True), "non-branded clicks"))
    if L["hubspot_contacts"]["present"]:
        stats.append((fmt(m["totals"]["contacts"]), "first-touch contacts on these pages"))
    stats_html = "".join(f'<div class="stat"><span class="n">{e(a)}</span><span class="l">{e(b)}</span></div>' for a, b in stats)

    works = "".join(f"<li>{e(x)}</li>" for x in n.get("works", []))
    doesnt = "".join(f"<li>{e(x)}</li>" for x in n.get("doesnt", []))
    verdict = (f'<div class="note stack"><p class="lede"><strong>{e(n.get("verdict", ""))}</strong></p></div>'
               + (f'<div class="two-col"><div><h3>What works</h3><ul>{works}</ul></div>'
                  f'<div><h3>What does not</h3><ul>{doesnt}</ul></div></div>' if works or doesnt else ""))
    pri = n.get("priorities", [])
    names = {oid: r["name"] for oid, r in m["matrix"].items()}
    pri_rows = [[str(p.get("rank", i + 1)),
                 f'<span class="badge {GAP_BADGE.get(p.get("gap"), "neutral")}">{e(GAP_LABELS.get(p.get("gap"), p.get("gap")))}</span>',
                 e(names.get(p.get("offering"), p.get("offering") or "Site-wide")) + (f" · {STAGE_LABELS.get(p.get('stage'), '')}" if p.get("stage") else ""),
                 e(p.get("action", "")), e(p.get("evidence", "")), f'<code>{e(p.get("handoff", ""))}</code>' if p.get("handoff") else "–"]
                for i, p in enumerate(pri)]
    confidential = L["hubspot_contacts"]["present"] or L["ads_landing"]["present"]
    sections = [
        ("verdict", "The honest read", verdict),
        ("invest", "Where to invest", para(n.get("channel_read"))),
        ("priorities", "Priorities", table(["#", "Gap", "Where", "Action", "Evidence", "Next skill"], pri_rows) if pri_rows else ""),
        ("journey", "Offering journey map", para(n.get("journey_read")) + journey_map(m)),
        ("offerings", "Diagnosis by offering", offerings_section(m, n)),
        ("valueprop", "Value proposition clarity", valueprop_section(m, n)),
        ("findability", "Findability", findability_section(m, n)),
        ("traffic", "Traffic and leads", traffic_section(m, n)),
        ("content", "Content state", content_state_section(m, n)),
        ("explorer-section", "Every page", explorer(m)),
        ("method", "Method and data quality", method_section(m, n)),
    ]
    body = "".join(f'<section class="stack" id="{sid}"><h2>{e(heading(h))}</h2>{c}</section>' for sid, h, c in sections if c)
    footer = (f"<p>Built by /content-audit on {e(m['generated'])}. Markdown source: <code>{e(paths['md'])}</code>. "
              f"Page data: <code>{e(paths['csv'])}</code>. Run folder: <code>{e(paths['run'])}</code>.</p>"
              + ("<p><strong>Confidential.</strong> Built from CRM and ad-account data; share the findings, not this file, "
                 "outside the company.</p>" if confidential else ""))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{e(title)}</title>
<meta name="description" content="{e((n.get('verdict') or '')[:300])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
{css}
</style>
</head>
<body>
<main class="page">
<header class="report-head stack">
<p class="eyebrow">Content audit · {e(site['host'])} · {e(m['as_of'])}</p>
<h1>{e(title)}</h1>
<p class="meta">{e(site.get('company') or site['host'])} · crawled {e(site['crawled_at'][:10])} · {fmt(inv['content_pages'])} content pages classified</p>
<div class="layers">{layers}</div>
</header>
<section class="stack" aria-label="Summary"><div class="stats">{stats_html}</div></section>
{body}
<footer class="stack">{footer}</footer>
</main>
{SCRIPT}
</body>
</html>
"""


# ---------------------------------------------------------------- markdown + csv
def render_md(m: dict, n: dict, paths: dict) -> str:
    site, L = m["site"], m["layers"]
    title = heading(n.get("title") or f"Content audit of {site['host']}")
    names = {oid: r["name"] for oid, r in m["matrix"].items()}
    out = ["---", f"title: {title}", "type: content-audit", f"site: {site['host']}", f"date: {m['as_of']}",
           "layers: [" + ", ".join(k for k, v in L.items() if v["present"]) + "]", f"html: {paths['html']}", "---", "",
           f"# {title}", "", "## The honest read", "", n.get("verdict", ""), ""]
    if n.get("works"):
        out += ["**What works**", ""] + [f"- {x}" for x in n["works"]] + [""]
    if n.get("doesnt"):
        out += ["**What does not**", ""] + [f"- {x}" for x in n["doesnt"]] + [""]
    if n.get("channel_read"):
        out += ["## Where to invest", "", n["channel_read"], ""]
    if n.get("priorities"):
        out += ["## Priorities", "", "| # | Gap | Where | Action | Evidence | Next skill |", "|---:|---|---|---|---|---|"]
        for i, p in enumerate(n["priorities"]):
            where = names.get(p.get("offering"), p.get("offering") or "Site-wide") + (f" · {STAGE_LABELS.get(p.get('stage'), '')}" if p.get("stage") else "")
            out.append(f"| {p.get('rank', i + 1)} | {GAP_LABELS.get(p.get('gap'), p.get('gap'))} | {where} | {p.get('action', '')} | "
                       f"{p.get('evidence', '')} | {p.get('handoff', '')} |")
        out.append("")
    out += ["## Offering journey map", "", "Pages per stage, with status and flags.", "",
            "| Offering | " + " | ".join(STAGE_LABELS[s] for s in STAGES) + " | Primary gap |", "|---|" + "---:|" * len(STAGES) + "---|"]
    for oid, row in m["matrix"].items():
        cells = []
        for s in STAGES:
            c = row["cells"][s]
            cells.append(f"{c['metrics']['pages']} {STATUS_TEXT[c['status']]}" + (f" ({', '.join(FLAG_TEXT.get(f, f) for f in c['flags'])})" if c["flags"] else ""))
        v = m["per_offering"].get(oid, {}).get("verdicts", {}).get("primary")
        out.append(f"| {row['name']} | " + " | ".join(cells) + f" | {GAP_LABELS.get(v, v) if v else '–'} |")
    out.append("")
    out += ["## Diagnosis by offering", ""]
    for oid, po in m["per_offering"].items():
        v = po["verdicts"]
        out += [f"### {po['name']}", "", f"Primary gap: {GAP_LABELS.get(v['primary'], v['primary'])}. "
                f"Journey breaks at: {STAGE_LABELS[po['journey_breaks_at']] if po['journey_breaks_at'] else 'nowhere'}.", ""]
        if n.get("offering_notes", {}).get(oid):
            out += [n["offering_notes"][oid], ""]
        for k in ("content", "conversion_path", "findability", "conversion", "distribution", "paid_reliance"):
            if k in v:
                d = v[k]
                read = "not assessed (" + d.get("needs", "") + ")" if not d["assessed"] else ("gap" if d["flag"] else "no gap")
                ev = "; ".join(f"{a.replace('_', ' ')}: {fmt_ev(b)}" for a, b in d.get("evidence", {}).items() if b not in (None, [], {}))
                out.append(f"- {GAP_LABELS[k]}: {read}" + (f". {ev}" if d["assessed"] and ev else ""))
        out.append("")
    vp = m.get("valueprop")
    if vp:
        out += ["## Value proposition clarity", "", n.get("valueprop_read", ""), "",
                "| Scope | " + " | ".join(VP_LABELS.values()) + " | Total |", "|---|" + "---:|" * (len(VP_LABELS) + 1)]
        for s in vp["scopes"]:
            out.append(f"| {names.get(s['scope'], 'Homepage' if s['scope'] == 'homepage' else s['scope'])} | "
                       + " | ".join(str(s["criteria"].get(k, {}).get("score", 0)) for k in VP_LABELS) + f" | {s['score']}/{s['max']} |")
        out.append("")
    for key, head in (("findability_read", "Findability"), ("traffic_read", "Traffic and leads"), ("content_state_read", "Content state")):
        if n.get(key):
            out += [f"## {head}", "", n[key], ""]
    out += ["## Method and data quality", "", "| Source | Status | Window | Rows |", "|---|---|---|---:|",
            f"| Website crawl | present | {site['crawled_at'][:10]} | {m['crawl']['html_pages']} |"]
    for k, v in L.items():
        out.append(f"| {k} | {'present' if v['present'] else 'absent'} | {v['window'] or '–'} | {v['rows'] if v['present'] else '–'} |")
    out.append("")
    for w in m["crawl"]["warnings"]:
        out.append(f"- Crawl warning: {w}")
    for k, v in L.items():
        if v.get("capped"):
            out.append(f"- {k} export hit its download row limit: pages missing from it are no data, not zero.")
    for x in n.get("limits", []):
        out.append(f"- Limit: {x}")
    out += ["", f"Page-level data: `{paths['csv']}`", ""]
    return "\n".join(out)


def write_csv(m: dict, path: Path) -> None:
    cols = ["id", "url", "title", "h1", "offering", "secondary_offering", "stage", "content_type", "icp_fit", "confidence",
            "evidence", "note", "onward", "has_capture", "links_to_desire_action", "links_to_action", "inbound_body_links",
            "word_count", "published", "modified", "noindex", "impressions", "clicks", "position", "sessions", "key_events",
            "contacts", "lead_contacts", "ads_clicks", "ads_cost", "ads_conversions", "type_hint", "excluded"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for p in m["pages"].values():
            w.writerow({**p, "excluded": ""})
        for p in m["excluded_pages"]:
            w.writerow({"id": p["id"], "url": p["url"], "title": p["title"], "excluded": p["reason"]})


def main(argv=None) -> int:
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out-name", help="Base name for the three files (default: the run folder name)")
    ap.add_argument("--allow-unverified", action="store_true", help="Build even if the narrative has unmatched numbers")
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    m = read_json(run_dir / "metrics.json")
    npath = run_dir / "narrative.json"
    if not npath.exists():
        print("error: narrative.json missing; write it from references/report-rules.md first", file=sys.stderr)
        return 2
    n = read_json(npath)
    bad = unverified_numbers(n, m)
    for w in style_warnings(n):
        print(f"style: {w}")
    if bad:
        print("Numbers in narrative.json that are not in metrics.json:")
        for b in bad:
            print(f"  {b}")
        if not args.allow_unverified:
            print("Fix the narrative (use the metric's value, or drop the number) and build again.")
            return 1
    base = args.out_name or run_dir.name
    paths = {"html": str(run_dir / f"{base}.html"), "md": str(run_dir / f"{base}.md"),
             "csv": str(run_dir / f"{base}-pages.csv"), "run": str(run_dir)}
    Path(paths["html"]).write_text(render_html(m, n, paths), encoding="utf-8")
    Path(paths["md"]).write_text(render_md(m, n, paths), encoding="utf-8")
    write_csv(m, Path(paths["csv"]))
    for k in ("html", "md", "csv"):
        print(f"wrote {paths[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
