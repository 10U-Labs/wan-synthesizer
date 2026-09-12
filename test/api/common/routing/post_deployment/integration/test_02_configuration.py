from __future__ import annotations

from typing import Any


def test_endpoint_is_regional(apigateway_client: Any, api_id: str) -> None:
    api = apigateway_client.get_rest_api(restApiId=api_id)
    assert "REGIONAL" in api["endpointConfiguration"]["types"]


def test_prod_stage_exists(apigateway_client: Any, api_id: str) -> None:
    stage = apigateway_client.get_stage(restApiId=api_id, stageName="prod")
    assert stage["stageName"] == "prod"


def test_the_live_authorizer_reads_the_whole_authorization_header(
        live_authorizer: dict[str, Any]) -> None:
    assert (live_authorizer["type"], live_authorizer["identitySource"]) == (
        "TOKEN", "method.request.header.Authorization")


def test_the_live_authorizer_is_the_lambda_the_stack_declares(
        live_authorizer: dict[str, Any], authorizer_config: dict[str, Any]) -> None:
    assert authorizer_config["FunctionArn"] in live_authorizer["authorizerUri"]


def test_the_authorizer_runs_on_python313(authorizer_config: dict[str, Any]) -> None:
    assert authorizer_config["Runtime"] == "python3.13"


def test_the_authorizer_knows_the_parameter_holding_the_key(
        authorizer_config: dict[str, Any], api_key_parameter_name: str) -> None:
    variables = authorizer_config["Environment"]["Variables"]
    assert variables["API_KEY_PARAMETER"] == api_key_parameter_name
