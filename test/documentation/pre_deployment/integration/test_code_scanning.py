from __future__ import annotations

import json
import subprocess
from typing import Any

import pytest

REPOSITORY = "10U-Labs/wan-synthesizer"
SCANNED = {"javascript-typescript", "python"}


@pytest.fixture(name="default_setup", scope="module")
def default_setup_fixture() -> dict[str, Any]:
    completed = subprocess.run(
        ["gh", "api", f"repos/{REPOSITORY}/code-scanning/default-setup"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    loaded: dict[str, Any] = json.loads(completed.stdout)
    return loaded


def test_code_scanning_is_configured(default_setup: dict[str, Any]) -> None:
    assert default_setup["state"] == "configured"


def test_code_scanning_runs_the_extended_query_suite(default_setup: dict[str, Any]) -> None:
    assert default_setup["query_suite"] == "extended"


def test_code_scanning_covers_the_python_and_the_javascript(
        default_setup: dict[str, Any]) -> None:
    assert SCANNED <= set(default_setup["languages"])
