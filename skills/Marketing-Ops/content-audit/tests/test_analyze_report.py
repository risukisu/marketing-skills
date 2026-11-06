import csv
import json
import re
import shutil

import analyze
import build_report


def metrics(run):
    return json.loads((run / "metrics.json").read_text(encoding="utf-8"))


def test_grid_statuses_follow_the_rules(run_dir):
    m = metrics(run_dir)
    dp = m["matrix"]["data-platform"]["cells"]
    fc = m["matrix"]["forecasting"]["cells"]
    assert [dp[s]["status"] for s in ("attention", "interest", "desire", "action")] == ["thin", "thin", "ok", "ok"]
    assert [fc[s]["status"] for s in ("attention", "interest", "desire", "action")] == ["thin", "missing", "thin", "missing"]
    assert "disconnected" in fc["desire"]["flags"]  # forecasting service page links to contact only in the nav
    assert "invisible" in fc["attention"]["flags"]  # not in a complete GSC export: zero is real
    assert m["per_offering"]["forecasting"]["journey_breaks_at"] == "attention"


def test_verdicts_report_evidence_and_what_was_not_assessed(run_dir):
    po = metrics(run_dir)["per_offering"]
    assert po["forecasting"]["verdicts"]["primary"] == "content"
    assert po["forecasting"]["verdicts"]["conversion"]["assessed"] is False  # 30 sessions is too few to judge
    assert po["data-platform"]["verdicts"]["paid_reliance"]["flag"] is True
    ev = po["data-platform"]["verdicts"]["findability"]["evidence"]
    assert ev["page_share_among_offerings"] == 0.75  # off-ICP and brand pages are left out of the ratio


def test_truncated_search_export_means_unknown_not_zero(run_dir, tmp_path):
    run = tmp_path / "run"
    shutil.copytree(run_dir, run)
    ex = json.loads((run / "exports.json").read_text(encoding="utf-8"))
    ex["sources"]["gsc_pages"]["capped_files"] = ["Pages.csv"]
    (run / "exports.json").write_text(json.dumps(ex), encoding="utf-8")
    assert analyze.main(["--run-dir", str(run), "--as-of", "2026-01-31"]) == 0
    m = metrics(run)
    flags = m["matrix"]["forecasting"]["cells"]["attention"]["flags"]
    assert "not-in-export" in flags and "invisible" not in flags
    assert m["pages"][next(k for k, p in m["pages"].items() if p["path"] == "/blog/demand-forecasting-basics.html")]["impressions"] is None


def test_report_builds_html_markdown_and_csv_without_contact_data(run_dir, tmp_path):
    run = tmp_path / "content-audit-fixture"
    shutil.copytree(run_dir, run)
    assert build_report.main(["--run-dir", str(run)]) == 0
    html = (run / "content-audit-fixture.html").read_text(encoding="utf-8")
    assert "Offering journey map" in html and "Demand forecasting" in html and "Confidential" in html
    assert not re.search(r"<h[1-4][^>]*>[^<]*\.</h[1-4]>", html)  # no heading ends in a period
    assert "example.test" not in html
    md = (run / "content-audit-fixture.md").read_text(encoding="utf-8")
    assert md.startswith("---") and "## The honest read" in md
    rows = list(csv.DictReader(open(run / "content-audit-fixture-pages.csv", encoding="utf-8-sig")))
    assert len(rows) == 18 and sum(1 for r in rows if r["excluded"]) == 4


def test_report_refuses_numbers_that_are_not_in_the_metrics(run_dir, tmp_path, capsys):
    run = tmp_path / "content-audit-fixture"
    shutil.copytree(run_dir, run)
    n = json.loads((run / "narrative.json").read_text(encoding="utf-8"))
    n["verdict"] += " Content drives 87% of all leads."
    (run / "narrative.json").write_text(json.dumps(n), encoding="utf-8")
    assert build_report.main(["--run-dir", str(run)]) == 1
    assert "87%" in capsys.readouterr().out
