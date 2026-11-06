import json
import shutil

import check_labels
import helpers


def clone(run_dir, tmp_path):
    dst = tmp_path / "run"
    shutil.copytree(run_dir, dst)
    return dst


def test_unconfirmed_taxonomy_blocks_classification(run_dir, tmp_path, capsys):
    run = clone(run_dir, tmp_path)
    tax = json.loads((run / "taxonomy.json").read_text(encoding="utf-8"))
    tax["confirmed"] = False
    (run / "taxonomy.json").write_text(json.dumps(tax), encoding="utf-8")
    assert check_labels.main(["--run-dir", str(run), "labels"]) == 1
    assert "not confirmed" in capsys.readouterr().out


def test_missing_and_invalid_labels_name_the_batch_to_rerun(run_dir, tmp_path, capsys):
    run = clone(run_dir, tmp_path)
    helpers.write_labels(run, drop="/pricing.html", bad_stage="/about.html")
    assert check_labels.main(["--run-dir", str(run), "labels"]) == 1
    out = capsys.readouterr().out
    assert "not labelled" in out and "awareness-ish" in out and "rerun: 0" in out


def test_valueprop_requires_quotes_notes_and_every_scope(run_dir, tmp_path, capsys):
    run = clone(run_dir, tmp_path)
    vp = json.loads((run / "valueprop.json").read_text(encoding="utf-8"))
    vp["scopes"][0]["criteria"]["proof"] = {"score": 2}
    vp["scopes"][0]["criteria"]["differentiation"] = {"score": 0}
    vp["scopes"] = vp["scopes"][:2]
    (run / "valueprop.json").write_text(json.dumps(vp), encoding="utf-8")
    assert check_labels.main(["--run-dir", str(run), "valueprop"]) == 1
    out = capsys.readouterr().out
    assert "verbatim quote" in out and "needs a note" in out and "'forecasting' not scored" in out
