import json
import shutil

import ingest


def exports(run):
    return json.loads((run / "exports.json").read_text(encoding="utf-8"))


def test_every_standard_export_is_recognised(run_dir):
    ex = exports(run_dir)
    assert set(ex["sources"]) == {"gsc_pages", "gsc_queries", "ga4_landing", "hubspot_contacts", "ads_landing"}
    ga = ex["sources"]["ga4_landing"]
    assert ga["window"] == "2025-08-01 to 2025-10-31"
    assert ga["by_path"]["/blog/what-is-a-data-platform.html"]["sessions"] == 460  # two channel rows summed
    assert ga["by_path"]["/blog/what-is-a-data-platform.html"]["channels"]["Email"] == 60
    assert "" not in ga["by_path"]  # (not set) dropped; the appended Date table ignored
    ads = ex["sources"]["ads_landing"]  # UTF-16, tab-separated, title lines, Total row
    assert ads["by_path"]["/services/data-platform.html"]["cost"] == 2340.5
    assert ads["window"] == "2025-08-01 to 2025-10-31"
    assert ex["sources"]["gsc_pages"]["window"] == "Last 3 months"


def test_hubspot_export_keeps_counts_not_people(run_dir):
    raw = (run_dir / "exports.json").read_text(encoding="utf-8")
    assert "example.test" not in raw and "Ada" not in raw
    hub = exports(run_dir)["sources"]["hubspot_contacts"]["by_path"]
    assert hub["/blog/what-is-a-data-platform.html"]["contacts"] == 1  # utm query stripped
    assert hub["(unknown)"]["contacts"] == 1


def test_unrecognised_file_stops_the_load(run_dir, tmp_path, capsys):
    run = tmp_path / "run"
    shutil.copytree(run_dir, run)
    (run / "ingest" / "mystery.csv").write_text("Foo,Bar\n1,2\n", encoding="utf-8")
    assert ingest.main(["--run-dir", str(run), "load"]) == 3
    assert "unrecognised: mystery.csv" in capsys.readouterr().out
    assert ingest.main(["--run-dir", str(run), "load", "--skip", "mystery.csv"]) == 0


def test_export_at_the_row_limit_is_marked_truncated(tmp_path):
    run = tmp_path / "run"
    (run / "ingest").mkdir(parents=True)
    rows = "\n".join(f"https://x.example/p{i},1,10,10%,5" for i in range(1000))
    (run / "ingest" / "Pages.csv").write_text("Top pages,Clicks,Impressions,CTR,Position\n" + rows, encoding="utf-8")
    assert ingest.main(["--run-dir", str(run), "load"]) == 0
    assert exports(run)["sources"]["gsc_pages"]["capped_files"] == ["Pages.csv"]


def test_overlapping_slices_are_not_double_counted(tmp_path):
    run = tmp_path / "run"
    (run / "ingest").mkdir(parents=True)
    head = "Top pages,Clicks,Impressions,CTR,Position\n"
    (run / "ingest" / "Pages-blog.csv").write_text(head + "https://x.example/blog/a,5,100,5%,3\n", encoding="utf-8")
    (run / "ingest" / "Pages-all.csv").write_text(
        head + "https://x.example/blog/a,5,100,5%,3\nhttps://x.example/b,1,10,10%,9\n", encoding="utf-8")
    assert ingest.main(["--run-dir", str(run), "load"]) == 0
    by = exports(run)["sources"]["gsc_pages"]["by_path"]
    assert by["/blog/a"]["impressions"] == 100 and by["/b"]["impressions"] == 10
