from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

from fixture_server import FixtureServer  # noqa: E402


@pytest.fixture(scope="session")
def site():
    with FixtureServer() as server:
        yield server.url


@pytest.fixture(scope="session")
def run_dir(site, tmp_path_factory):
    """A full run on the fixture site: crawl, prepare, model stand-ins, exports, analysis."""
    import analyze
    import check_labels
    import crawl_site
    import helpers
    import ingest
    import prepare

    run = tmp_path_factory.mktemp("work") / "content-audit-fixture"
    assert crawl_site.main([site + "index.html", "--run-dir", str(run), "--delay", "0"]) == 0
    assert prepare.main(["--run-dir", str(run)]) == 0
    helpers.copy_model_files(run)
    helpers.write_labels(run)
    assert check_labels.main(["--run-dir", str(run), "labels"]) == 0
    assert check_labels.main(["--run-dir", str(run), "valueprop"]) == 0
    assert ingest.main(["--run-dir", str(run), "init"]) == 0
    helpers.copy_ingest(run)
    assert ingest.main(["--run-dir", str(run), "load"]) == 0
    assert analyze.main(["--run-dir", str(run), "--as-of", "2026-01-31"]) == 0
    return run
