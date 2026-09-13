from __future__ import annotations

from typing import Any

from test_fixtures.aws import log_group_arn, log_resources_of, managed_policies_of


def test_lambda_assumes_the_declared_role(
        lambda_config: dict[str, Any], role_name: str) -> None:
    assert lambda_config["Role"].endswith(f"role/{role_name}")


def test_api_gateway_may_invoke_the_lambda(lambda_client: Any, function_name: str) -> None:
    policy = lambda_client.get_policy(FunctionName=function_name)["Policy"]
    assert "apigateway.amazonaws.com" in policy


def test_role_grants_store_access(iam_client: Any, role_name: str) -> None:
    policy = iam_client.get_role_policy(RoleName=role_name, PolicyName="StoreAccess")
    assert "s3:GetObject" in str(policy["PolicyDocument"])


def test_role_may_delete_a_version(iam_client: Any, role_name: str) -> None:
    policy = iam_client.get_role_policy(RoleName=role_name, PolicyName="StoreAccess")
    assert "s3:DeleteObjectVersion" in str(policy["PolicyDocument"])


def test_the_handlers_role_attaches_no_managed_policy(
        iam_client: Any, lambda_config: dict[str, Any]) -> None:
    assert not managed_policies_of(iam_client, lambda_config)


def test_the_handlers_role_writes_its_own_log_group_alone(
        iam_client: Any, logs_client: Any, lambda_config: dict[str, Any]) -> None:
    granted = log_resources_of(iam_client, lambda_config)
    assert granted == [log_group_arn(logs_client, lambda_config)]
