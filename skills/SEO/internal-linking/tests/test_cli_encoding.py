"""The CLIs must not crash on a Windows console whose code page cannot encode the report's arrows.

Found on the first real run (2026-10-08): analyze_links.py printed "→" to a cp1250 console and died
with UnicodeEncodeError. The scripts reconfigure stdout to UTF-8 themselves; PYTHONIOENCODING
reproduces the legacy console in a subprocess on any platform.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
FIX = Path(__file__).resolve().parent / "fixtures"


def run(script, *args):
    env = dict(os.environ, PYTHONIOENCODING="cp1250")
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args], capture_output=True, env=env)


def test_analyze_prints_on_a_cp1250_console(tmp_path):
    crawl = tmp_path / "crawl.json"
    assert run("import_crawl.py", str(FIX / "sf_all_inlinks.csv"), "--pages", str(FIX / "sf_internal_html.csv"),
               "--out", str(crawl)).returncode == 0
    r = run("analyze_links.py", str(crawl), "--out", str(tmp_path / "metrics.json"))
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    out = r.stdout.decode("utf-8", "replace")
    assert "## Pages by inbound links" in out
    assert json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))["summary"]["pages"] == 6
