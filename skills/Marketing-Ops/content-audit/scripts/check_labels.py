"""Validate the model-written files of a run and merge the classification labels.

    python check_labels.py --run-dir RUN taxonomy     # taxonomy.json is well-formed and confirmed
    python check_labels.py --run-dir RUN labels       # every batch labelled, every value legal -> labels.json
    python check_labels.py --run-dir RUN valueprop    # valueprop.json scores and quotes are complete

Exit code 0 = valid. Exit code 1 = problems, listed one per line with the file they are in;
for labels, the batches to re-run are printed last as `rerun: 3 7 12`.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    CONFIDENCE, CONTENT_TYPES, ICP_FIT, RESERVED_OFFERINGS, STAGES, read_json, utf8_console, write_json,
)

VP_CRITERIA = ["category", "audience", "outcome", "differentiation", "proof", "next_step"]
STAGE_ALIASES = {"awareness": "attention", "consideration": "interest", "decision": "desire",
                 "conversion": "action", "a": None}


def check_taxonomy(run_dir: Path) -> tuple[list[str], dict | None]:
    path = run_dir / "taxonomy.json"
    if not path.exists():
        return [f"{path.name}: missing"], None
    try:
        tax = read_json(path)
    except ValueError as exc:
        return [f"{path.name}: not valid JSON ({exc})"], None
    errs = []
    offerings = tax.get("offerings")
    if not isinstance(offerings, list) or not 1 <= len(offerings) <= 12:
        errs.append(f"{path.name}: 'offerings' must list 1 to 12 offerings")
        offerings = []
    seen = set()
    for i, o in enumerate(offerings):
        oid = str(o.get("id", ""))
        if not re.fullmatch(r"[a-z0-9][a-z0-9\-]{0,40}", oid):
            errs.append(f"{path.name}: offering {i} id '{oid}' must be lower-case kebab-case")
        if oid in RESERVED_OFFERINGS:
            errs.append(f"{path.name}: offering id '{oid}' is reserved")
        if oid in seen:
            errs.append(f"{path.name}: duplicate offering id '{oid}'")
        seen.add(oid)
        for key in ("name", "definition"):
            if not str(o.get(key, "")).strip():
                errs.append(f"{path.name}: offering '{oid}' needs a '{key}'")
        if not o.get("evidence"):
            errs.append(f"{path.name}: offering '{oid}' needs at least one evidence URL")
    if not isinstance(tax.get("brand_terms", []), list):
        errs.append(f"{path.name}: 'brand_terms' must be a list")
    if tax.get("confirmed") is not True:
        errs.append(f"{path.name}: not confirmed by the user yet (set \"confirmed\": true only after they approve it)")
    return errs, tax


def _norm(value) -> str:
    return re.sub(r"\s+", "-", str(value or "").strip().lower())


def check_labels(run_dir: Path) -> int:
    errs, tax = check_taxonomy(run_dir)
    if tax is None:
        print("\n".join(errs))
        return 1
    tax_errs = [e for e in errs if "not confirmed" in e]
    if tax_errs:
        print("\n".join(tax_errs))
        return 1
    allowed_off = {o["id"] for o in tax["offerings"]} | set(RESERVED_OFFERINGS)
    meta = read_json(run_dir / "pages.json")
    problems, rerun, merged, warnings = [], [], [], []
    for b in range(meta["batches"]):
        batch = read_json(run_dir / "batches" / f"batch_{b:02d}.json")
        expected = {r["id"]: r["url"] for r in batch}
        out = run_dir / "labels" / f"batch_{b:02d}.json"
        if not out.exists():
            problems.append(f"labels/{out.name}: missing")
            rerun.append(b)
            continue
        try:
            rows = read_json(out)
        except ValueError as exc:
            problems.append(f"labels/{out.name}: not valid JSON ({exc})")
            rerun.append(b)
            continue
        if isinstance(rows, dict):
            rows = rows.get("labels", [])
        bad = False
        got = set()
        for r in rows:
            rid = r.get("id")
            where = f"labels/{out.name} {rid}"
            if rid not in expected:
                problems.append(f"{where}: id not in batch {b}")
                bad = True
                continue
            if rid in got:
                problems.append(f"{where}: labelled twice")
                bad = True
            got.add(rid)
            stage = _norm(r.get("stage"))
            stage = STAGE_ALIASES.get(stage, stage) or stage
            off = _norm(r.get("offering"))
            sec = _norm(r.get("secondary_offering")) if r.get("secondary_offering") else ""
            icp = _norm(r.get("icp_fit"))
            conf = _norm(r.get("confidence"))
            ctype = _norm(r.get("content_type"))
            if conf == "medium":
                conf = "med"
            if stage not in STAGES:
                problems.append(f"{where}: stage '{r.get('stage')}' not one of {STAGES}")
                bad = True
            if off not in allowed_off:
                problems.append(f"{where}: offering '{r.get('offering')}' not in taxonomy or {sorted(RESERVED_OFFERINGS)}")
                bad = True
            if sec and (sec not in allowed_off or sec == off):
                problems.append(f"{where}: secondary_offering '{r.get('secondary_offering')}' invalid")
                bad = True
            if icp not in ICP_FIT:
                problems.append(f"{where}: icp_fit '{r.get('icp_fit')}' not one of {ICP_FIT}")
                bad = True
            if conf not in CONFIDENCE:
                problems.append(f"{where}: confidence '{r.get('confidence')}' not one of {CONFIDENCE}")
                bad = True
            if ctype not in CONTENT_TYPES:
                warnings.append(f"{where}: content_type '{r.get('content_type')}' unknown, stored as 'other'")
                ctype = "other"
            if not str(r.get("evidence", "")).strip():
                problems.append(f"{where}: evidence is empty")
                bad = True
            merged.append({"id": rid, "url": expected[rid], "offering": off, "secondary_offering": sec or None,
                           "stage": stage, "content_type": ctype, "icp_fit": icp, "confidence": conf,
                           "evidence": str(r.get("evidence", "")).strip()[:300],
                           "note": str(r.get("note", "") or "").strip()[:300]})
        missing = set(expected) - got
        if missing:
            problems.append(f"labels/{out.name}: {len(missing)} pages not labelled ({', '.join(sorted(missing)[:5])}...)")
            bad = True
        if bad:
            rerun.append(b)
    for w in warnings:
        print(f"warning: {w}")
    if problems:
        print("\n".join(problems))
        print("rerun: " + " ".join(str(b) for b in sorted(set(rerun))))
        return 1
    write_json(run_dir / "labels.json", {
        "validated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "batches": meta["batches"], "labels": merged})
    print(f"OK: {len(merged)} pages labelled across {meta['batches']} batches -> labels.json")
    return 0


def check_valueprop(run_dir: Path) -> int:
    path = run_dir / "valueprop.json"
    if not path.exists():
        print(f"{path.name}: missing")
        return 1
    _, tax = check_taxonomy(run_dir)
    scopes_needed = {"homepage"} | ({o["id"] for o in tax["offerings"]} if tax else set())
    data = read_json(path)
    errs = []
    seen = set()
    for s in data.get("scopes", []):
        scope = s.get("scope")
        seen.add(scope)
        if not s.get("url"):
            errs.append(f"{scope}: url missing (the page that was scored)")
        crit = s.get("criteria", {})
        for c in VP_CRITERIA:
            item = crit.get(c)
            if not isinstance(item, dict):
                errs.append(f"{scope}.{c}: missing")
                continue
            score = item.get("score")
            if score not in (0, 1, 2):
                errs.append(f"{scope}.{c}: score must be 0, 1 or 2")
            if score in (1, 2) and not str(item.get("quote", "")).strip():
                errs.append(f"{scope}.{c}: a score above 0 needs a verbatim quote from the page")
            if score == 0 and not str(item.get("note", "")).strip():
                errs.append(f"{scope}.{c}: a score of 0 needs a note saying what is missing")
    for missing in sorted(scopes_needed - seen):
        errs.append(f"scope '{missing}' not scored (score it, or add it with \"url\": \"none\" and all zeros "
                    "if the offering has no page of its own)")
    if errs:
        print("\n".join(f"{path.name}: {e}" for e in errs))
        return 1
    print(f"OK: {len(seen)} value-proposition scopes scored")
    return 0


def main(argv=None) -> int:
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("what", choices=["taxonomy", "labels", "valueprop"])
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    if args.what == "taxonomy":
        errs, _ = check_taxonomy(run_dir)
        print("\n".join(errs) if errs else "OK: taxonomy.json is valid and confirmed")
        return 1 if errs else 0
    if args.what == "labels":
        return check_labels(run_dir)
    return check_valueprop(run_dir)


if __name__ == "__main__":
    sys.exit(main())
