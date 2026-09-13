from __future__ import annotations

import json
from typing import Any

from repo_utils import REPO_ROOT
from test_handler_contracts import SPA_ORIGIN

_HEADER = "Access-Control-Allow-Origin"


def _spec() -> dict[str, Any]:
    spec: dict[str, Any] = json.loads(
        (REPO_ROOT / "src" / "www" / "api" / "openapi.json").read_text(encoding="utf-8"))
    return spec


def _origins_answered(node: Any) -> list[str]:
    if isinstance(node, dict):
        named = [
            str(value) for key, value in node.items()
            if key.endswith(_HEADER) and isinstance(value, str)
        ]
        return named + [origin for value in node.values() for origin in _origins_answered(value)]
    if isinstance(node, list):
        return [origin for item in node for origin in _origins_answered(item)]
    return []


def test_no_origin_is_answered_with_a_wildcard() -> None:
    assert "'*'" not in _origins_answered(_spec())


def test_every_origin_answered_is_the_spas() -> None:
    assert set(_origins_answered(_spec())) == {f"'{SPA_ORIGIN}'"}


def test_an_answer_the_gateway_writes_itself_can_be_read_by_the_page() -> None:
    responses = _spec()["x-amazon-apigateway-gateway-responses"]
    assert [
        name for name in ("DEFAULT_4XX", "DEFAULT_5XX")
        if responses[name]["responseParameters"].get(
            f"gatewayresponse.header.{_HEADER}") != f"'{SPA_ORIGIN}'"
    ] == []


def test_every_preflight_answers_the_spas_origin() -> None:
    spec = _spec()
    assert [
        path for path, operations in spec["paths"].items()
        if "options" in operations and operations["options"][
            "x-amazon-apigateway-integration"]["responses"]["default"][
            "responseParameters"][f"method.response.header.{_HEADER}"] != f"'{SPA_ORIGIN}'"
    ] == []
