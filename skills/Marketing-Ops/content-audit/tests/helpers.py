"""Stand-ins for the model steps, so the scripts can be tested without a model.

write_labels() plays the classification subagents: it labels every batch from
fixtures/labels_by_path.json. copy_model_files() drops in the taxonomy, value-proposition
scores and narrative a model would have written.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

FIX = Path(__file__).resolve().parent / "fixtures"


def path_of(url: str) -> str:
    from urllib.parse import urlsplit
    return urlsplit(url).path.lower()


def write_labels(run_dir: Path, drop: str | None = None, bad_stage: str | None = None) -> None:
    by_path = json.loads((FIX / "labels_by_path.json").read_text(encoding="utf-8"))
    meta = json.loads((run_dir / "pages.json").read_text(encoding="utf-8"))
    (run_dir / "labels").mkdir(exist_ok=True)
    for b in range(meta["batches"]):
        batch = json.loads((run_dir / "batches" / f"batch_{b:02d}.json").read_text(encoding="utf-8"))
        rows = []
        for r in batch:
            p = path_of(r["url"])
            if p == drop:
                continue
            off, stage, ctype, icp, conf = by_path.get(p, ["none", "attention", "other", "unclear", "low"])
            if p == bad_stage:
                stage = "awareness-ish"
            rows.append({"id": r["id"], "url": r["url"], "offering": off, "secondary_offering": None, "stage": stage,
                         "content_type": ctype, "icp_fit": icp, "confidence": conf,
                         "evidence": f"fixture label for {p}", "note": ""})
        (run_dir / "labels" / f"batch_{b:02d}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")


def copy_model_files(run_dir: Path, narrative: bool = True) -> None:
    shutil.copy(FIX / "taxonomy.json", run_dir / "taxonomy.json")
    shutil.copy(FIX / "valueprop.json", run_dir / "valueprop.json")
    if narrative:
        shutil.copy(FIX / "narrative.json", run_dir / "narrative.json")


def copy_ingest(run_dir: Path) -> None:
    dst = run_dir / "ingest"
    dst.mkdir(exist_ok=True)
    for f in (FIX / "ingest").iterdir():
        shutil.copy(f, dst / f.name)
