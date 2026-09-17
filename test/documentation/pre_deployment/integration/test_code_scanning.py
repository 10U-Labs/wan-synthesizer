from __future__ import annotations

import json
import subprocess
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

REPOSITORY = "10U-Labs/wan-synthesizer"
ANALYSES = f"repos/{REPOSITORY}/code-scanning/analyses?ref=refs/heads/main&per_page=100"
SCAN_CADENCE = timedelta(days=7)
UPLOAD_LAG = timedelta(days=1)
ANALYSIS_WAIT = timedelta(minutes=20)
POLL = timedelta(seconds=30)
LANGUAGES = ["python", "javascript-typescript"]
CATEGORIES = [f"/language:{language}" for language in LANGUAGES]


def _head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=60,
    )
    return completed.stdout.strip()


def _codeql_analyses() -> list[dict[str, Any]]:
    completed = subprocess.run(
        ["gh", "api", ANALYSES], capture_output=True, text=True, check=True, timeout=60,
    )
    loaded: list[dict[str, Any]] = json.loads(completed.stdout)
    return [analysis for analysis in loaded if analysis["tool"]["name"] == "CodeQL"]


def _of_this_commit(analyses: list[dict[str, Any]], head: str) -> list[dict[str, Any]]:
    return [
        analysis for analysis in analyses
        if analysis["commit_sha"] == head and analysis["category"] in CATEGORIES
    ]


@pytest.fixture(name="analyses", scope="module")
def analyses_fixture() -> list[dict[str, Any]]:
    head = _head()
    deadline = time.monotonic() + ANALYSIS_WAIT.total_seconds()
    while True:
        analyses = _codeql_analyses()
        if len(_of_this_commit(analyses, head)) == len(CATEGORIES):
            return analyses
        if time.monotonic() > deadline:
            raise AssertionError(f"CodeQL has not analysed {head} within {ANALYSIS_WAIT}")
        time.sleep(POLL.total_seconds())


def _latest(analyses: list[dict[str, Any]], category: str) -> datetime:
    return max(
        datetime.fromisoformat(analysis["created_at"])
        for analysis in analyses
        if analysis["category"] == category
    )


@pytest.mark.parametrize("language", LANGUAGES)
def test_codeql_analysed_main_within_the_week(
        analyses: list[dict[str, Any]], language: str) -> None:
    assert datetime.now(UTC) - _latest(analyses, f"/language:{language}") <= (
        SCAN_CADENCE + UPLOAD_LAG
    )


def test_codeql_found_nothing_in_this_commit(analyses: list[dict[str, Any]]) -> None:
    assert [
        analysis["results_count"] for analysis in _of_this_commit(analyses, _head())
    ] == [0] * len(CATEGORIES)
