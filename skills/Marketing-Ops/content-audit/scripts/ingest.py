"""Ingest folder for analytics exports: create it, then load what the user dropped in.

    python ingest.py --run-dir RUN init      # creates RUN/ingest/ with a README of exports to add
    python ingest.py --run-dir RUN load      # reads every CSV / ZIP in RUN/ingest/ -> exports.json

Recognised exports (standard UI downloads; see references/exports.md):
  gsc_pages        Search Console > Performance > Pages tab (Pages.csv, or the whole ZIP)
  gsc_queries      Search Console > Performance > Queries tab (Queries.csv, or the whole ZIP)
  ga4_landing      GA4 > Reports > Engagement > Landing page (CSV download)
  hubspot_contacts HubSpot contacts export with the "First page seen" property
  ads_landing      Google Ads > Insights and reports > Landing pages (CSV download)

Each file is identified by its columns. A file that matches nothing stops the load with exit code 3
and its columns printed; re-run with --source FILE=KIND and, if needed, --column FILE:"Their col"=field.
Contact-level data (names, emails) is never read: only page, lifecycle stage, source and date columns.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import parse_number, path_key, read_json, utf8_console, write_json  # noqa: E402

FIELDS = {
    "gsc_pages": {"page": ["top pages", "page", "pages", "url"], "clicks": ["clicks"],
                  "impressions": ["impressions"], "ctr": ["ctr"], "position": ["position", "average position"]},
    "gsc_queries": {"query": ["top queries", "query", "queries", "search query"], "clicks": ["clicks"],
                    "impressions": ["impressions"], "ctr": ["ctr"], "position": ["position", "average position"]},
    "ga4_landing": {"page": ["landing page", "landing page + query string", "landing page + query"],
                    "sessions": ["sessions"], "engaged_sessions": ["engaged sessions"],
                    "users": ["active users", "total users", "users"], "new_users": ["new users"],
                    "key_events": ["key events", "conversions", "key event count"],
                    "channel": ["session default channel group", "session primary channel group (default channel group)",
                                "session primary channel group", "default channel group",
                                "first user primary channel group (default channel group)",
                                "first user default channel group"]},
    "hubspot_contacts": {"page": ["first page seen", "first page seen url", "first url"],
                         "lifecycle": ["lifecycle stage"],
                         "source": ["original source", "original traffic source", "original source type"],
                         "created": ["create date", "created date", "createdate"]},
    "ads_landing": {"page": ["landing page", "expanded landing page", "final url", "final urls", "page"],
                    "clicks": ["clicks"], "impressions": ["impr.", "impressions"], "cost": ["cost"],
                    "conversions": ["conversions", "conv.", "all conv."]},
}
# Columns a kind must have (beyond 'page' or 'query') to be recognised.
SIGNATURE = {
    "gsc_pages": ["page", "impressions", "position"],
    "gsc_queries": ["query", "impressions", "position"],
    "ga4_landing": ["page", "sessions"],
    "hubspot_contacts": ["page"],
    "ads_landing": ["page", "cost"],
}
ORDER = ["hubspot_contacts", "gsc_queries", "gsc_pages", "ga4_landing", "ads_landing"]
# Row counts at which UI downloads usually stop (Search Console: 1,000). A file this long is
# treated as truncated: pages missing from it are "not in the export", never "zero".
ROW_CAPS = {250, 500, 1000, 5000, 10000, 25000, 50000, 100000}

README = """# Ingest folder

Drop analytics exports here, then run `/content-audit` again and pick "add exports" (or run
`ingest.py --run-dir <run folder> load`). Every file is optional; the report states which layers
it had and which verdicts it could not reach without the rest.

Use the same date window for every export where you can (the last 3 or 12 full months).

**Search Console stops at 1,000 rows.** If the site has more than about 800 pages, export the
Pages tab once per site section instead (Performance > + New > Page > "URLs containing" /blog/,
then /services/, and so on) and drop every file here; the loader merges them. A page missing from
a 1,000-row export is reported as "not in the export", not as zero impressions.

| Layer | Export | What it unlocks |
|---|---|---|
| Search Console | Performance > Search results > set dates > Export > Download CSV (keep the ZIP or drop Pages.csv and Queries.csv) | Findability: impressions, clicks, positions per offering and stage; branded vs non-branded demand |
| GA4 | Reports > Engagement > Landing page > set dates > Share this report > Download File > CSV. Optional: add the secondary dimension "Session default channel group" before downloading | Traffic per offering and stage, key events per landing page, channel mix (distribution) |
| HubSpot | Contacts > filter (for example Create date in the window) > Export > include the properties "First page seen", "Lifecycle stage", "Original source", "Create date" > CSV | First-touch leads per page, offering and stage (conversion) |
| Google Ads | Insights and reports > Landing pages > set dates > Download > CSV | Which offerings rely on paid traffic, cost per conversion by landing page |

Names and emails in a HubSpot export are never read. Keep the folder out of any public repository.
"""


def _read_text(raw: bytes) -> str:
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


GSC_AUX = {"countries.csv", "devices.csv", "dates.csv", "search appearance.csv", "filters.csv",
           "chart.csv"}


def iter_files(ingest: Path, skip: set[str] = frozenset()):
    for f in sorted(ingest.iterdir()):
        if f.name.lower() == "readme.md" or f.name.startswith(("~", ".")) or f.name in skip:
            continue
        if f.suffix.lower() == ".zip":
            with zipfile.ZipFile(f) as z:
                for name in z.namelist():
                    if name.lower().endswith((".csv", ".tsv")):
                        yield f"{f.name}/{name}", _read_text(z.read(name))
        elif f.suffix.lower() in (".csv", ".tsv", ".txt"):
            yield f.name, _read_text(f.read_bytes())
        elif f.suffix.lower() in (".xlsx", ".xls"):
            yield f.name, None


def parse_table(text: str) -> tuple[list[str], list[list[str]], list[str]]:
    """Return (header, rows, preamble lines). Skips '#' comments and title lines before the header."""
    lines = text.splitlines()
    preamble = []
    sample = "\n".join(lines[:30])
    delim = "\t" if sample.count("\t") > sample.count(",") else (";" if sample.count(";") > sample.count(",") else ",")
    known = {a for kind in FIELDS.values() for aliases in kind.values() for a in aliases}
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    header, rows, started = None, [], False
    for row in reader:
        cells = [c.strip() for c in row]
        if header is None:
            if not any(cells) or cells[0].startswith("#"):
                preamble.append(",".join(cells))
                continue
            if sum(1 for c in cells if c.lower() in known) >= 2 or any(
                    c.lower() in {"first page seen", "first page seen url"} for c in cells):
                header = cells
                continue
            preamble.append(",".join(cells))
            continue
        if not any(cells):
            if started:
                break
            continue
        if cells[0].startswith("#"):
            continue
        started = True
        rows.append(cells)
    return header or [], rows, preamble


def map_columns(header: list[str], kind: str, overrides: dict[str, str]) -> dict[str, int]:
    low = [h.lower().strip() for h in header]
    mapping = {}
    for field, aliases in FIELDS[kind].items():
        for alias in aliases:
            if alias in low:
                mapping[field] = low.index(alias)
                break
    for their, field in overrides.items():
        if their.lower() in low:
            mapping[field] = low.index(their.lower())
    return mapping


def detect(header: list[str], overrides: dict[str, str]) -> tuple[str | None, dict[str, int]]:
    low = {h.lower() for h in header}
    for kind in ORDER:
        mapping = map_columns(header, kind, overrides)
        if all(f in mapping for f in SIGNATURE[kind]):
            if kind == "ads_landing" and "sessions" in low:
                continue
            if kind == "gsc_pages" and "landing page" in low:
                continue
            return kind, mapping
    return None, {}


def window_from(preamble: list[str], kind: str) -> str:
    text = " ".join(preamble)
    s = re.search(r"Start date:\s*(\d{8})", text)
    e = re.search(r"End date:\s*(\d{8})", text)
    if s and e:
        f = lambda d: f"{d[:4]}-{d[4:6]}-{d[6:]}"  # noqa: E731
        return f"{f(s.group(1))} to {f(e.group(1))}"
    m = re.search(r"([A-Z][a-z]+ \d{1,2}, \d{4})\s*[-–]\s*([A-Z][a-z]+ \d{1,2}, \d{4})", text)
    if m:
        try:
            a, b = (datetime.strptime(x, "%B %d, %Y").strftime("%Y-%m-%d") for x in m.groups())
            return f"{a} to {b}"
        except ValueError:
            return f"{m.group(1)} to {m.group(2)}"
    return ""


def _num(row, idx):
    if idx is None or idx >= len(row):
        return None
    return parse_number(row[idx])


def aggregate(kind: str, rows: list[list[str]], m: dict[str, int], acc: dict) -> int:
    used = 0
    for r in rows:
        if not r or (r[0].lower().startswith(("total", "grand total")) and kind != "gsc_queries"):
            continue
        if kind == "gsc_queries":
            q = r[m["query"]].strip() if m["query"] < len(r) else ""
            if not q:
                continue
            acc.setdefault("queries", []).append(
                [q, _num(r, m.get("clicks")) or 0, _num(r, m.get("impressions")) or 0, _num(r, m.get("position"))])
            used += 1
            continue
        page = r[m["page"]] if m["page"] < len(r) else ""
        key = path_key(page)
        if kind == "hubspot_contacts":
            slot = acc["by_path"].setdefault(key or "(unknown)", {"contacts": 0, "by_stage": {}, "by_source": {}})
            slot["contacts"] += 1
            for fld, bucket in (("lifecycle", "by_stage"), ("source", "by_source")):
                if fld in m and m[fld] < len(r):
                    val = r[m[fld]].strip().lower() or "(blank)"
                    slot[bucket][val] = slot[bucket].get(val, 0) + 1
            if "created" in m and m["created"] < len(r):
                d = re.search(r"(\d{4}-\d{2}-\d{2})", r[m["created"]])
                if d:
                    acc["dates"].append(d.group(1))
            used += 1
            continue
        if not key:
            continue
        slot = acc["by_path"].setdefault(key, defaultdict(float))
        for fld in FIELDS[kind]:
            if fld in ("page", "channel", "ctr"):
                continue
            v = _num(r, m.get(fld))
            if v is None:
                continue
            if fld == "position":
                imp = _num(r, m.get("impressions")) or 0
                slot["_pos_weighted"] += v * imp
                slot["_pos_imp"] += imp
            else:
                slot[fld] += v
        if kind == "ga4_landing" and "channel" in m and m["channel"] < len(r):
            ch = r[m["channel"]].strip() or "(blank)"
            slot.setdefault("channels", {})
            slot["channels"][ch] = slot["channels"].get(ch, 0) + (_num(r, m.get("sessions")) or 0)
        used += 1
    return used


def finish(kind: str, acc: dict) -> dict:
    out = {k: v for k, v in acc.items() if k not in ("by_path", "dates")}
    if "by_path" in acc:
        by = {}
        for key, slot in acc["by_path"].items():
            d = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in dict(slot).items() if not k.startswith("_")}
            if kind == "gsc_pages":
                d["position"] = round(slot["_pos_weighted"] / slot["_pos_imp"], 2) if slot.get("_pos_imp") else None
            by[key] = d
        out["by_path"] = by
    if kind == "hubspot_contacts" and acc.get("dates"):
        out["window_from_data"] = f"{min(acc['dates'])} to {max(acc['dates'])}"
    if kind == "gsc_queries":
        out["queries"] = sorted(acc.get("queries", []), key=lambda q: -q[2])[:20000]
    return out


def load(run_dir: Path, source_over: dict[str, str], col_over: dict[str, dict[str, str]],
         windows: dict[str, str], skip: set[str] = frozenset()) -> int:
    ingest = run_dir / "ingest"
    if not ingest.exists():
        print("error: no ingest folder; run `ingest.py --run-dir RUN init` first", file=sys.stderr)
        return 2
    result = {"loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "sources": {}, "files": [], "problems": []}
    unknown = []
    gsc_filter_window = ""
    for name, text in iter_files(ingest, skip):
        base = name.split("/")[-1]
        if base in skip:
            continue
        if base.lower() in GSC_AUX:
            if base.lower() == "filters.csv" and text:
                for row in csv.reader(io.StringIO(text)):
                    if len(row) >= 2 and row[0].strip().lower() == "date":
                        gsc_filter_window = row[1].strip()
            result["files"].append({"file": name, "kind": "ignored (Search Console extra tab)", "rows": 0})
            continue
        if text is None:
            result["problems"].append(f"{name}: Excel files are not read; export or save it as CSV")
            continue
        header, rows, pre = parse_table(text)
        over = col_over.get(name, {})
        kind = source_over.get(name)
        mapping = map_columns(header, kind, over) if kind else {}
        if not kind:
            kind, mapping = detect(header, over)
        if not kind or not all(f in mapping for f in SIGNATURE[kind]):
            unknown.append((name, header[:25] or [ln for ln in pre[:3]]))
            continue
        src = result["sources"].setdefault(kind, {"files": [], "rows": 0, "mapping": {}, "window": "",
                                                       "capped_files": []})
        acc = src.setdefault("_acc", {"by_path": {}, "dates": []} if kind != "gsc_queries" else {})
        if kind in ("gsc_pages", "ga4_landing", "ads_landing"):
            # Exports sliced by site section may overlap: merge per path, keeping the larger row,
            # so a page exported twice is not counted twice.
            part = {"by_path": {}, "dates": []}
            used = aggregate(kind, rows, mapping, part)
            for key, slot in part["by_path"].items():
                have = acc["by_path"].get(key)
                weight = "impressions" if kind == "gsc_pages" else ("sessions" if kind == "ga4_landing" else "clicks")
                if have is None or (slot.get(weight) or 0) > (have.get(weight) or 0):
                    acc["by_path"][key] = slot
        else:
            used = aggregate(kind, rows, mapping, acc)
        if len(rows) in ROW_CAPS:
            src["capped_files"].append(name)
        src["files"].append(name)
        src["rows"] += used
        src["mapping"][name] = {field: header[i] for field, i in mapping.items()}
        src["window"] = src["window"] or window_from(pre, kind)
        result["files"].append({"file": name, "kind": kind, "rows": used})
    for kind, src in result["sources"].items():
        acc = src.pop("_acc")
        src.update(finish(kind, acc))
        if kind in windows:
            src["window"] = windows[kind]
        if not src["window"] and kind.startswith("gsc_") and gsc_filter_window:
            src["window"] = gsc_filter_window
        if not src["window"]:
            src["window"] = src.get("window_from_data", "") or "unknown"
        src["window_source"] = "user" if kind in windows else ("export" if src["window"] != "unknown" else "unknown")
    if unknown:
        for name, cols in unknown:
            print(f"unrecognised: {name}\n  columns: {cols}")
        print("Re-run with --source FILE=KIND (kinds: " + ", ".join(ORDER) + ") and, if a column name differs, "
              "--column FILE:\"Their column\"=field. Files GSC puts in its ZIP besides Pages and Queries "
              "(Countries, Devices, Dates, Filters, Search appearance) can be ignored with --skip FILE.")
        result["problems"] += [f"{n}: not recognised" for n, _ in unknown]
    write_json(run_dir / "exports.json", result)
    for f in result["files"]:
        print(f"loaded {f['file']} as {f['kind']} ({f['rows']} rows)")
    for kind, src in result["sources"].items():
        for name in src.get("capped_files", []):
            print(f"warning: {name} has exactly {src['rows'] if len(src['files']) == 1 else 'a capped number of'} rows, "
                  "the usual download limit; treated as truncated. Export it in slices by site section for full coverage.")
        print(f"  {kind}: window {src['window']} ({src['window_source']}); columns used: "
              + "; ".join(f"{k}<-'{v}'" for m in src["mapping"].values() for k, v in m.items()))
    for p in result["problems"]:
        print(f"problem: {p}")
    return 3 if unknown else 0


def main(argv=None) -> int:
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("action", choices=["init", "load"])
    ap.add_argument("--source", action="append", default=[], help="FILE=KIND, forces a file's kind")
    ap.add_argument("--column", action="append", default=[], help='FILE:"Their column"=field')
    ap.add_argument("--window", action="append", default=[], help="KIND=YYYY-MM-DD to YYYY-MM-DD")
    ap.add_argument("--skip", action="append", default=[], help="File name inside ingest/ to ignore")
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    if args.action == "init":
        ingest = run_dir / "ingest"
        ingest.mkdir(parents=True, exist_ok=True)
        (ingest / "README.md").write_text(README, encoding="utf-8")
        print(f"Created {ingest} (README.md lists the exports to drop in)")
        return 0
    src = dict(s.split("=", 1) for s in args.source if "=" in s)
    bad = [k for k in src.values() if k not in FIELDS]
    if bad:
        print(f"error: unknown kind(s) {bad}; use one of {ORDER}", file=sys.stderr)
        return 2
    cols: dict[str, dict[str, str]] = {}
    for c in args.column:
        m = re.match(r"(.+?):(.+)=(\w+)$", c)
        if m:
            cols.setdefault(m.group(1), {})[m.group(2).strip('"')] = m.group(3)
    windows = dict(w.split("=", 1) for w in args.window if "=" in w)
    return load(run_dir, src, cols, windows, set(args.skip))


if __name__ == "__main__":
    sys.exit(main())
