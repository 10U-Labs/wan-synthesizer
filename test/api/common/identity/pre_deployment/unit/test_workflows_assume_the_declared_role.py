from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from repo_utils import REPO_ROOT

WORKFLOWS = REPO_ROOT / ".github" / "workflows"
ROLE_VARIABLE = "${{ vars.OIDC_ROLE_ARN }}"
CREDENTIALS_ACTION = "aws-actions/configure-aws-credentials@v5"


def _steps(path: Path) -> list[dict[str, Any]]:
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [
        step
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
    ]


def _credential_steps() -> list[tuple[str, dict[str, Any]]]:
    return [
        (path.name, step)
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for step in _steps(path)
        if str(step.get("uses", "")).startswith("aws-actions/configure-aws-credentials")
    ]


def test_every_workflow_assumes_the_role_by_the_one_variable() -> None:
    assert [
        name for name, step in _credential_steps()
        if step["with"].get("role-to-assume") != ROLE_VARIABLE
    ] == []


def test_every_workflow_assumes_the_role_through_one_pinned_action() -> None:
    assert {step["uses"] for _, step in _credential_steps()} == {CREDENTIALS_ACTION}


def test_every_workflow_assumes_the_role_in_the_declared_region() -> None:
    assert {step["with"].get("aws-region") for _, step in _credential_steps()} == {"us-east-2"}


def test_no_workflow_carries_a_static_credential() -> None:
    assert [
        name for name, step in _credential_steps()
        if "aws-access-key-id" in step["with"] or "aws-secret-access-key" in step["with"]
    ] == []


def test_every_job_that_assumes_the_role_asks_for_an_id_token_and_nothing_wider() -> None:
    assuming = [
        (path.name, job_name)
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for job_name, job in yaml.safe_load(path.read_text(encoding="utf-8"))["jobs"].items()
        if any(str(step.get("uses", "")).startswith("aws-actions/configure-aws-credentials")
               for step in job.get("steps", []))
        and job.get("permissions") != {"contents": "read", "id-token": "write"}
    ]
    assert assuming == []
