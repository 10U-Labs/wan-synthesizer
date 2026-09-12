from __future__ import annotations

from typing import Any, cast

import pytest

from test_terraform_config import lambda_handler_names

API_NAME = "wan-synthesizer"


@pytest.fixture(name="api_id")
def api_id_fixture(apigateway_client: Any) -> str:
    items = apigateway_client.get_rest_apis(limit=500)["items"]
    for api in items:
        if api["name"] == API_NAME:
            return str(api["id"])
    raise AssertionError(f"REST API '{API_NAME}' not found in AWS")


@pytest.fixture(name="live_authorizer")
def live_authorizer_fixture(apigateway_client: Any, api_id: str) -> dict[str, Any]:
    items = apigateway_client.get_authorizers(restApiId=api_id)["items"]
    if len(items) != 1:
        raise AssertionError(f"expected one authorizer on '{API_NAME}', found {len(items)}")
    return cast("dict[str, Any]", items[0])


@pytest.fixture(name="authorizer_config")
def authorizer_config_fixture(lambda_client: Any) -> dict[str, Any]:
    response = lambda_client.get_function(FunctionName=lambda_handler_names()["authorizer"])
    return cast("dict[str, Any]", response["Configuration"])


@pytest.fixture(name="api_key")
def api_key_fixture(ssm_client: Any, api_key_parameter_name: str) -> str:
    response = ssm_client.get_parameter(Name=api_key_parameter_name, WithDecryption=True)
    return str(response["Parameter"]["Value"])
