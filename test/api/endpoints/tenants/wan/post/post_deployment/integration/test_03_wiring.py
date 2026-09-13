from __future__ import annotations

from typing import Any

from test_fixtures.aws import log_group_arn, log_resources_of, managed_policies_of


def test_synthesizer_assumes_its_own_role(
        synthesizer_config: dict[str, Any], synthesizer_role_name: str) -> None:
    assert synthesizer_config["Role"].endswith(f"role/{synthesizer_role_name}")


def test_synthesizer_role_grants_store_access(
        iam_client: Any, synthesizer_role_name: str) -> None:
    policy = iam_client.get_role_policy(
        RoleName=synthesizer_role_name, PolicyName="store-access")
    assert "s3:PutObject" in str(policy["PolicyDocument"])


def test_synthesizer_role_may_delete_a_version(
        iam_client: Any, synthesizer_role_name: str) -> None:
    policy = iam_client.get_role_policy(
        RoleName=synthesizer_role_name, PolicyName="store-access")
    assert "s3:DeleteObjectVersion" in str(policy["PolicyDocument"])


def test_synthesizer_on_failure_targets_the_failure_handler(
        synthesizer_invoke_config: dict[str, Any], failure_handler_function_name: str) -> None:
    destination = synthesizer_invoke_config["DestinationConfig"]["OnFailure"]["Destination"]
    assert destination.endswith(f"function:{failure_handler_function_name}")


def test_synthesizer_role_may_invoke_the_failure_handler(
        iam_client: Any, synthesizer_role_name: str) -> None:
    policy = iam_client.get_role_policy(
        RoleName=synthesizer_role_name, PolicyName="on-failure-destination")
    assert "lambda:InvokeFunction" in str(policy["PolicyDocument"])


def test_failure_handler_role_grants_store_write(
        iam_client: Any, failure_handler_role_name: str) -> None:
    policy = iam_client.get_role_policy(
        RoleName=failure_handler_role_name, PolicyName="store-write")
    assert "s3:PutObject" in str(policy["PolicyDocument"])


def test_the_synthesizers_role_attaches_no_managed_policy(
        iam_client: Any, synthesizer_config: dict[str, Any]) -> None:
    assert not managed_policies_of(iam_client, synthesizer_config)


def test_the_synthesizers_role_writes_its_own_log_group_alone(
        iam_client: Any, logs_client: Any, synthesizer_config: dict[str, Any]) -> None:
    granted = log_resources_of(iam_client, synthesizer_config)
    assert granted == [log_group_arn(logs_client, synthesizer_config)]


def test_the_failure_handlers_role_attaches_no_managed_policy(
        iam_client: Any, failure_handler_config: dict[str, Any]) -> None:
    assert not managed_policies_of(iam_client, failure_handler_config)


def test_the_failure_handlers_role_writes_its_own_log_group_alone(
        iam_client: Any, logs_client: Any, failure_handler_config: dict[str, Any]) -> None:
    granted = log_resources_of(iam_client, failure_handler_config)
    assert granted == [log_group_arn(logs_client, failure_handler_config)]
