from __future__ import annotations

from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from seed import DEFAULT_API
from test_handler_contracts import SPA_ORIGIN

_ORIGIN_HEADER = "Access-Control-Allow-Origin"


def _answer(headers: dict[str, str], method: str = "GET", path: str = "tenants") -> Any:
    request = Request(f"{DEFAULT_API}/{path}", headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return response
    except HTTPError as refusal:
        return refusal


def _status(headers: dict[str, str], method: str = "GET", path: str = "tenants") -> int:
    return int(_answer(headers, method, path).status)


def test_prod_stage_points_to_a_deployment(apigateway_client: Any, api_id: str) -> None:
    stage = apigateway_client.get_stage(restApiId=api_id, stageName="prod")
    assert stage["deploymentId"]


def test_api_has_resources_beyond_root(apigateway_client: Any, api_id: str) -> None:
    resources = apigateway_client.get_resources(restApiId=api_id, limit=500)["items"]
    assert len(resources) > 1


def test_a_request_through_cloudfront_carrying_the_key_reaches_the_gateway(
        api_key: str) -> None:
    assert _status({"Authorization": f"Bearer {api_key}"}) == 200


def test_a_request_carrying_nothing_is_turned_away() -> None:
    assert _status({}) == 401


def test_a_request_carrying_a_made_up_token_is_turned_away() -> None:
    assert _status({"Authorization": "Bearer made-up"}) == 401


def test_the_key_is_refused_the_delete_of_a_carrier(api_key: str) -> None:
    headers = {"Authorization": f"Bearer {api_key}"}
    assert _status(headers, "DELETE", "carriers/no-such-carrier") == 403


def test_a_preflight_is_answered_with_the_pages_origin_alone() -> None:
    headers = {"Origin": SPA_ORIGIN, "Access-Control-Request-Method": "GET"}
    assert _answer(headers, "OPTIONS").headers[_ORIGIN_HEADER] == SPA_ORIGIN


def test_an_answer_carrying_data_names_the_pages_origin_alone(api_key: str) -> None:
    headers = {"Authorization": f"Bearer {api_key}", "Origin": SPA_ORIGIN}
    assert _answer(headers).headers[_ORIGIN_HEADER] == SPA_ORIGIN


def test_a_refusal_the_gateway_writes_names_the_pages_origin_alone() -> None:
    assert _answer({"Origin": SPA_ORIGIN}).headers[_ORIGIN_HEADER] == SPA_ORIGIN
