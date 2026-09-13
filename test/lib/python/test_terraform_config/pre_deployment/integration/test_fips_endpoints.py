from __future__ import annotations

from typing import Any, cast

import yaml

from repo_utils import REPO_ROOT
from test_terraform_config import STACKS_DIR, declared_state_keys, load_tf

FIPS = "AWS_USE_FIPS_ENDPOINT"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
CREDENTIALS_ACTION = "aws-actions/configure-aws-credentials"


def _functions() -> list[tuple[str, str, dict[str, Any]]]:
    found: list[tuple[str, str, dict[str, Any]]] = []
    for stack in declared_state_keys():
        for path in sorted((STACKS_DIR / stack).glob("*.tf")):
            for block in cast("list[dict[str, Any]]", load_tf(path).get("resource", [])):
                found += [
                    (stack, name, function)
                    for name, function in block.get("aws_lambda_function", {}).items()
                ]
    return found


def _variables(function: dict[str, Any]) -> dict[str, Any]:
    environments: list[dict[str, Any]] = function.get("environment", [{}])
    variables: dict[str, Any] = environments[0].get("variables", {})
    return variables


def _workflows() -> dict[str, dict[Any, Any]]:
    return {
        path.name: yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted(WORKFLOWS.glob("*.yml"))
    }


def _assumes_a_role(workflow: dict[Any, Any]) -> bool:
    return any(
        str(step.get("uses", "")).startswith(CREDENTIALS_ACTION)
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
    )


def test_every_function_calls_aws_over_its_fips_endpoints() -> None:
    assert [
        (stack, name)
        for stack, name, function in _functions()
        if _variables(function).get(FIPS) != "true"
    ] == []


def test_every_workflow_that_assumes_a_role_calls_aws_over_its_fips_endpoints() -> None:
    assert [
        name
        for name, workflow in _workflows().items()
        if _assumes_a_role(workflow) and workflow.get("env", {}).get(FIPS) != "true"
    ] == []
