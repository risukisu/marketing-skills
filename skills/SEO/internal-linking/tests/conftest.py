from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

from fixture_server import FixtureServer  # noqa: E402


@pytest.fixture
def site():
    with FixtureServer() as server:
        yield server.url
