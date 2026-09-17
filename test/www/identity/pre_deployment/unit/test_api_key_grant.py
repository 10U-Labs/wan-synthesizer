from __future__ import annotations

from typing import Any, cast

from hcl2.api import load as hcl2_load

from repo_utils import REPO_ROOT

IDENTITY = REPO_ROOT / "src" / "www" / "identity"
API_KEY_PARAMETER = "/api.10ulabs.com/api-key"
API_DOCUMENT = "api"
API_POLICY = "Api"


def _load(name: str) -> dict[str, Any]:
    with open(IDENTITY / name, encoding="utf-8") as handle:
        return cast("dict[str, Any]", hcl2_load(handle))


def _policy_documents(document: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        name: list(body["statement"])
        for block in document.get("data", [])
        for name, body in block.get("aws_iam_policy_document", {}).items()
    }


def _resources(document: dict[str, Any], kind: str) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for block in document.get("resource", []):
        found.update(block.get(kind, {}))
    return found


def _resolved(expression: str) -> str:
    values: dict[str, Any] = {}
    for block in _load("iam.tf").get("locals", []):
        values.update(block)
    resolved = expression
    for _ in range(3):
        for name, value in values.items():
            resolved = resolved.replace("${local." + name + "}", str(value))
    return resolved


def _api_statements() -> list[dict[str, Any]]:
    return _policy_documents(_load("iam.tf"))[API_DOCUMENT]


def _every_action() -> list[str]:
    return [
        action
        for statements in _policy_documents(_load("iam.tf")).values()
        for statement in statements
        for action in statement["actions"]
    ]


def test_the_api_document_carries_one_statement() -> None:
    assert len(_api_statements()) == 1


def test_the_api_statement_grants_reading_a_parameter_alone() -> None:
    assert _api_statements()[0]["actions"] == ["ssm:GetParameter"]


def test_the_api_statement_names_the_api_key_parameter_alone() -> None:
    assert [_resolved(resource) for resource in _api_statements()[0]["resources"]] == [
        f"arn:aws:ssm:${{module.common.aws_region}}:${{module.common.aws_account_id}}"
        f":parameter{API_KEY_PARAMETER}"]


def test_the_api_policy_is_named_for_the_api() -> None:
    assert _resources(_load("iam.tf"), "aws_iam_role_policy")[API_DOCUMENT]["name"] == API_POLICY


def test_the_api_policy_carries_the_api_document() -> None:
    policy = _resources(_load("iam.tf"), "aws_iam_role_policy")[API_DOCUMENT]["policy"]
    assert policy == f"${{data.aws_iam_policy_document.{API_DOCUMENT}.json}}"


def test_the_api_policy_is_held_on_the_deploy_role() -> None:
    policy = _resources(_load("iam.tf"), "aws_iam_role_policy")[API_DOCUMENT]
    assert policy["role"] == "${aws_iam_role.deploy.id}"


def test_the_api_policy_is_in_the_exclusive_list() -> None:
    exclusive = _resources(_load("main.tf"), "aws_iam_role_policies_exclusive")["deploy"]
    assert f"${{aws_iam_role_policy.{API_DOCUMENT}.name}}" in exclusive["policy_names"]


def test_the_role_decrypts_nothing_by_itself() -> None:
    assert [action for action in _every_action() if action.startswith("kms:")] == []


def test_the_role_reads_no_api_gateway() -> None:
    assert [action for action in _every_action() if action.startswith("apigateway:")] == []


def test_the_key_is_the_only_parameter_within_reach() -> None:
    assert [
        resource
        for statements in _policy_documents(_load("iam.tf")).values()
        for statement in statements
        for resource in map(_resolved, statement["resources"])
        if ":parameter" in resource and not resource.endswith(f":parameter{API_KEY_PARAMETER}")
    ] == []


def test_the_stack_is_the_files_the_tests_read() -> None:
    assert sorted(path.name for path in IDENTITY.glob("*.tf")) == [
        "backend.tf", "iam.tf", "main.tf", "outputs.tf", "providers.tf"]
