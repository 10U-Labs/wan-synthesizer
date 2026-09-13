from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from seed import DEFAULT_API
from test_terraform_config import lambda_handler_names


def test_rest_api_exists(apigateway_client: Any, api_id: str) -> None:
    api = apigateway_client.get_rest_api(restApiId=api_id)
    assert api["name"] == "wan-synthesizer"


def test_every_live_route_sits_under_the_served_prefix(
        apigateway_client: Any, api_id: str) -> None:
    prefix = urlsplit(DEFAULT_API).path
    resources = apigateway_client.get_resources(restApiId=api_id, limit=500)["items"]
    paths = [item["path"] for item in resources if item["path"] not in ("/", prefix)]
    assert [path for path in paths if not path.startswith(f"{prefix}/")] == []


def test_the_authorizer_lambda_exists(authorizer_config: dict[str, Any]) -> None:
    assert authorizer_config["FunctionName"] == lambda_handler_names()["authorizer"]


def test_the_api_key_is_kept(ssm_client: Any, api_key_parameter_name: str) -> None:
    response = ssm_client.get_parameter(Name=api_key_parameter_name, WithDecryption=True)
    assert response["Parameter"]["Value"]


def test_the_api_stands_behind_an_authorizer(live_authorizer: dict[str, Any]) -> None:
    assert live_authorizer["name"]


def test_the_authorized_accounts_are_kept(
        ssm_client: Any, authorized_accounts_parameter_name: str) -> None:
    response = ssm_client.get_parameter(Name=authorized_accounts_parameter_name)
    assert response["Parameter"]["Type"] == "StringList"
