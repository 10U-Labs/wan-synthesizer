from __future__ import annotations

from typing import Any, cast

import boto3
import pytest

from test_terraform_config import TEST_AWS_REGION

ISSUER = "token.actions.githubusercontent.com"


@pytest.fixture(scope="session", name="cloudfront_client")
def cloudfront_client_fixture() -> Any:
    return cast(Any, boto3).client("cloudfront", region_name=TEST_AWS_REGION)


@pytest.fixture(name="live_role")
def live_role_fixture(iam_client: Any, role_name: str) -> dict[str, Any]:
    return cast("dict[str, Any]", iam_client.get_role(RoleName=role_name)["Role"])


@pytest.fixture(name="live_trust_statement")
def live_trust_statement_fixture(live_role: dict[str, Any]) -> dict[str, Any]:
    statements: list[dict[str, Any]] = live_role["AssumeRolePolicyDocument"]["Statement"]
    if len(statements) != 1:
        raise AssertionError("the live trust must carry exactly one statement")
    return statements[0]


@pytest.fixture(name="live_trust_claims")
def live_trust_claims_fixture(live_trust_statement: dict[str, Any]) -> dict[str, Any]:
    equals: dict[str, Any] = live_trust_statement["Condition"]["StringEquals"]
    return {key.removeprefix(f"{ISSUER}:"): value for key, value in equals.items()}


@pytest.fixture(name="live_inline_policies")
def live_inline_policies_fixture(iam_client: Any, role_name: str) -> dict[str, dict[str, Any]]:
    names: list[str] = iam_client.list_role_policies(RoleName=role_name)["PolicyNames"]
    return {
        name: iam_client.get_role_policy(RoleName=role_name, PolicyName=name)["PolicyDocument"]
        for name in names
    }


@pytest.fixture(name="live_statements")
def live_statements_fixture(
        live_inline_policies: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        statement
        for document in live_inline_policies.values()
        for statement in document["Statement"]
    ]


@pytest.fixture(name="live_actions_of")
def live_actions_of_fixture() -> Any:
    def _actions(statement: dict[str, Any]) -> list[str]:
        listed = statement["Action"]
        return [listed] if isinstance(listed, str) else list(listed)
    return _actions


@pytest.fixture(name="live_resources")
def live_resources_fixture(live_statements: list[dict[str, Any]]) -> set[str]:
    resources: set[str] = set()
    for statement in live_statements:
        listed = statement["Resource"]
        resources.update([listed] if isinstance(listed, str) else listed)
    return resources


@pytest.fixture(name="declared_actions")
def declared_actions_fixture(
        permission_documents: dict[str, list[dict[str, Any]]],
        inline_policies: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    return {
        str(inline_policies[name]["name"]): {
            action for statement in statements for action in statement["actions"]
        }
        for name, statements in permission_documents.items()
    }
