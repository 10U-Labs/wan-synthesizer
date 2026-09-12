from __future__ import annotations

import json
import re
from typing import Any, cast

from repo_utils import REPO_ROOT
from test_terraform_config import COMMON_OUTPUTS_FILE, output_values

ROUTING_DIR = REPO_ROOT / "src" / "api" / "common" / "routing"
OPENAPI_SPEC = REPO_ROOT / "src" / "www" / "api" / "openapi.json"


def _main_text() -> str:
    return (ROUTING_DIR / "main.tf").read_text(encoding="utf-8")


def test_locals_reference_only_declared_common_outputs() -> None:
    refs = set(re.findall(r"module\.common\.(\w+)", _main_text()))
    declared = set(output_values(COMMON_OUTPUTS_FILE))
    assert refs <= declared


def test_templatefile_provides_every_openapi_handler_placeholder() -> None:
    needed = set(re.findall(r"\$\{(\w+HandlerArn)\}",
                            OPENAPI_SPEC.read_text(encoding="utf-8")))
    supplied = set(re.findall(r"(\w+HandlerArn)\s*=", _main_text()))
    assert needed <= supplied


def test_templatefile_supplies_no_placeholder_the_spec_does_not_need() -> None:
    needed = set(re.findall(r"\$\{(\w+HandlerArn)\}",
                            OPENAPI_SPEC.read_text(encoding="utf-8")))
    supplied = set(re.findall(r"(\w+HandlerArn)\s*=", _main_text()))
    assert supplied <= needed


def test_api_id_output_references_the_declared_rest_api() -> None:
    outputs = output_values(ROUTING_DIR / "outputs.tf")
    assert "aws_api_gateway_rest_api.api" in str(outputs["api_gateway_id"])


def _spec() -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(OPENAPI_SPEC.read_text(encoding="utf-8")))


def _operations(spec: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (path, verb): operation
        for path, verbs in spec["paths"].items()
        for verb, operation in verbs.items()
    }


def _secured_by(spec: dict[str, Any], operation: dict[str, Any]) -> list[str]:
    requirements = operation.get("security", spec.get("security", []))
    return [name for requirement in requirements for name in requirement]


def _scheme(spec: dict[str, Any]) -> dict[str, Any]:
    return next(iter(spec["components"]["securitySchemes"].values()))


def test_the_spec_names_one_way_in() -> None:
    assert len(_spec()["components"]["securitySchemes"]) == 1


def test_every_operation_but_a_preflight_is_behind_the_authorizer() -> None:
    spec = _spec()
    open_operations = [
        (path, verb) for (path, verb), operation in _operations(spec).items()
        if verb != "options" and _secured_by(spec, operation) != list(
            spec["components"]["securitySchemes"])
    ]
    assert open_operations == []


def test_every_preflight_is_open_because_a_browser_sends_it_no_token() -> None:
    spec = _spec()
    guarded = [
        path for (path, verb), operation in _operations(spec).items()
        if verb == "options" and _secured_by(spec, operation) != []
    ]
    assert guarded == []


def test_the_authorizer_reads_the_authorization_header() -> None:
    scheme = _scheme(_spec())
    assert scheme["name"] == "Authorization"


def test_the_authorizer_is_the_lambda_the_stack_declares() -> None:
    scheme = _scheme(_spec())
    assert scheme["x-amazon-apigateway-authorizer"]["authorizerUri"] == "${AuthorizerHandlerArn}"


def test_the_authorizer_is_handed_the_whole_token() -> None:
    scheme = _scheme(_spec())
    assert scheme["x-amazon-apigateway-authorizer"]["type"] == "token"


def test_a_verdict_is_remembered_no_longer_than_a_google_token_lives() -> None:
    ttl = _scheme(_spec())["x-amazon-apigateway-authorizer"]["authorizerResultTtlInSeconds"]
    assert 0 < ttl <= 3600


def test_an_answer_the_gateway_writes_itself_can_be_read_by_the_browser() -> None:
    responses = _spec()["x-amazon-apigateway-gateway-responses"]
    assert [
        name for name in ("DEFAULT_4XX", "DEFAULT_5XX")
        if responses[name]["responseParameters"].get(
            "gatewayresponse.header.Access-Control-Allow-Origin") != "'*'"
    ] == []


def test_every_preflight_lets_the_token_through() -> None:
    spec = _spec()
    refusing = [
        path for (path, verb), operation in _operations(spec).items()
        if verb == "options" and "Authorization" not in operation[
            "x-amazon-apigateway-integration"]["responses"]["default"][
            "responseParameters"]["method.response.header.Access-Control-Allow-Headers"]
    ]
    assert refusing == []
