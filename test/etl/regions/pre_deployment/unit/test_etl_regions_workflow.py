from __future__ import annotations

from typing import Any

import pytest
import yaml

from repo_utils import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "etl_regions.yml"
LOAD = "load"
E2E = "post-deployment-e2e-tests"
CHECKS = [
    "assert-no-comments",
    "assert-no-inline-directives",
    "assert-no-pytest-plugin-declarations",
    "assert-one-assert-per-pytest",
    "assert-pytest-class-holds-state",
    "assert-pytest-fixture-name-is-needed",
    "assert-pytest-test-can-fail",
    "copy-paste-source",
    "copy-paste-tests",
    "mypy-source",
    "mypy-tests",
    "pre-deployment-tests",
    "pylint-source",
    "pylint-tests",
    "yamllint",
]


def _loaded() -> dict[str, Any]:
    loaded: dict[Any, Any] = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return loaded


def _steps(job: str) -> list[str]:
    return [str(step.get("run", "")) for step in _loaded()["jobs"][job]["steps"]]


def test_the_load_waits_for_every_check() -> None:
    assert sorted(_loaded()["jobs"][LOAD]["needs"]) == CHECKS


def test_the_load_runs_on_main_alone() -> None:
    assert _loaded()["jobs"][LOAD]["if"] == "github.ref == 'refs/heads/main'"


def test_the_load_masks_the_key_before_using_it() -> None:
    assert [run for run in _steps(LOAD) if "::add-mask::" in run] != []


def test_the_load_never_passes_the_key_as_an_argument() -> None:
    assert [run for run in _steps(LOAD) if "--key" in run or "--api-key" in run] == []


def test_the_load_runs_the_program() -> None:
    assert [run for run in _steps(LOAD) if "load_regions" in run and "main(" in run] != []


def test_the_load_checks_out_the_history_the_diff_needs() -> None:
    assert [
        step for step in _loaded()["jobs"][LOAD]["steps"]
        if step.get("uses", "").startswith("actions/checkout@")
        and step.get("with", {}).get("fetch-depth") == 0
    ] != []


def test_the_loaded_regions_are_read_back_only_after_the_load() -> None:
    assert _loaded()["jobs"][E2E]["needs"] == [LOAD]


def test_the_e2e_job_runs_the_post_deployment_e2e_tier() -> None:
    assert [run for run in _steps(E2E) if "test/etl/regions/post_deployment/e2e/" in run] != []


@pytest.mark.parametrize("path", [
    "data/providers/**",
    "src/etl/regions/**",
    "test/etl/regions/**",
    "lib/python/**",
    ".github/workflows/etl_regions.yml",
])
def test_a_change_to_the_data_the_program_or_its_tests_starts_the_workflow(path: str) -> None:
    assert path in _loaded()["on"]["push"]["paths"]


def test_the_workflow_can_be_told_to_load_the_file_unchanged_or_not() -> None:
    assert _loaded()["on"]["workflow_dispatch"]["inputs"]["all"]["type"] == "boolean"
