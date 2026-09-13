from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

REPOSITORY = "10U-Labs/wan-synthesizer"
ANALYSES = f"repos/{REPOSITORY}/code-scanning/analyses?ref=refs/heads/main&per_page=100"
SCAN_CADENCE = timedelta(days=7)
UPLOAD_LAG = timedelta(days=1)


@pytest.fixture(name="analyses", scope="module")
def analyses_fixture() -> list[dict[str, Any]]:
    completed = subprocess.run(
        ["gh", "api", ANALYSES], capture_output=True, text=True, check=True, timeout=60,
    )
    loaded: list[dict[str, Any]] = json.loads(completed.stdout)
    return [analysis for analysis in loaded if analysis["tool"]["name"] == "CodeQL"]


def _latest(analyses: list[dict[str, Any]], category: str) -> datetime:
    return max(
        datetime.fromisoformat(analysis["created_at"])
        for analysis in analyses
        if analysis["category"] == category
    )


@pytest.mark.parametrize("language", ["python", "javascript-typescript"])
def test_codeql_analysed_main_within_the_week(
        analyses: list[dict[str, Any]], language: str) -> None:
    assert datetime.now(UTC) - _latest(analyses, f"/language:{language}") <= (
        SCAN_CADENCE + UPLOAD_LAG
    )


def test_codeql_analyses_carry_no_open_result(analyses: list[dict[str, Any]]) -> None:
    assert [analysis["results_count"] for analysis in analyses[:2]] == [0, 0]
