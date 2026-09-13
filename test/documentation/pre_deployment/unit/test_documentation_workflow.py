from __future__ import annotations

from typing import Any

import yaml

from repo_utils import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "documentation.yml"
JOB = "code-scanning"


def _loaded() -> dict[Any, Any]:
    loaded: dict[Any, Any] = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return loaded


def test_the_workflow_runs_when_the_tests_over_the_repository_settings_change() -> None:
    assert "test/documentation/**" in _loaded()[True]["push"]["paths"]


def test_the_code_scanning_job_may_read_the_setting_it_holds() -> None:
    assert _loaded()["jobs"][JOB]["permissions"] == {"contents": "read", "security-events": "read"}


def test_the_code_scanning_job_runs_the_tests_over_the_repository_settings() -> None:
    assert [
        step for step in _loaded()["jobs"][JOB]["steps"]
        if "test/documentation/" in str(step.get("run", ""))
    ] != []
