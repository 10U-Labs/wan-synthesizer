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


def test_no_step_installs_a_tool_its_action_runs() -> None:
    runs = [str(step.get("run", "")) for job in _loaded()["jobs"].values() for step in job["steps"]]
    assert [
        run for run in runs if "pip install" in run and ("assert-" in run or "yamllint" in run)
    ] == []


def test_only_a_job_named_for_an_assert_tool_runs_one() -> None:
    assert [
        name for name, job in _loaded()["jobs"].items()
        if not name.startswith("assert-")
        and any(str(step.get("uses", "")).startswith("10U-Labs/assert-") for step in job["steps"])
    ] == []
