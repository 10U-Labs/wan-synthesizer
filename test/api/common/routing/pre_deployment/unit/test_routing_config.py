from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from test_terraform_config import find_resource, output_values


def _resource(document: dict[str, object], resource_type: str, name: str) -> dict[str, Any]:
    body = find_resource(document, resource_type, name)
    if body is None:
        raise AssertionError(f"{resource_type}.{name} is not declared")
    return body


def _modules(routing_main: dict[str, object]) -> list[dict[str, Any]]:
    blocks = routing_main.get("module", [])
    return blocks if isinstance(blocks, list) else []


def test_rest_api_is_declared(routing_main: dict[str, object]) -> None:
    assert find_resource(routing_main, "aws_api_gateway_rest_api", "api") is not None


def test_rest_api_has_the_product_name(routing_main: dict[str, object]) -> None:
    api = _resource(routing_main, "aws_api_gateway_rest_api", "api")
    assert api["name"] == "wan-synthesizer"


def test_rest_api_is_regional(routing_main: dict[str, object]) -> None:
    api = _resource(routing_main, "aws_api_gateway_rest_api", "api")
    assert api["endpoint_configuration"][0]["types"] == ["REGIONAL"]


def test_prod_stage_is_declared(routing_main: dict[str, object]) -> None:
    stage = _resource(routing_main, "aws_api_gateway_stage", "prod")
    assert stage["stage_name"] == "prod"


def test_deployment_is_declared(routing_main: dict[str, object]) -> None:
    assert find_resource(routing_main, "aws_api_gateway_deployment", "prod") is not None


def test_common_module_is_sourced(routing_main: dict[str, object]) -> None:
    common = next(m["common"] for m in _modules(routing_main) if "common" in m)
    assert common["source"] == "../../../../lib/opentofu/common"


def _authorizer(routing_authorizer: dict[str, object]) -> dict[str, Any]:
    return _resource(routing_authorizer, "aws_lambda_function", "authorizer")


def _authorizer_variables(routing_authorizer: dict[str, object]) -> dict[str, Any]:
    variables = _authorizer(routing_authorizer)["environment"][0]["variables"]
    return dict(variables)


def test_the_authorizer_is_named_by_the_common_module(
        routing_authorizer: dict[str, object]) -> None:
    function = _authorizer(routing_authorizer)
    assert "lambda_handler_names.authorizer" in str(function["function_name"])


def test_the_authorizer_runs_on_python313(routing_authorizer: dict[str, object]) -> None:
    assert _authorizer(routing_authorizer)["runtime"] == "python3.13"


def test_the_authorizer_entrypoint_is_its_own_module(
        routing_authorizer: dict[str, object]) -> None:
    assert _authorizer(routing_authorizer)["handler"] == "authorizer.lambda_handler"


@pytest.mark.parametrize("variable", [
    "GOOGLE_CLIENT_ID", "HOSTED_DOMAIN", "API_KEY_PARAMETER", "AUTHORIZED_ACCOUNTS_PARAMETER",
])
def test_the_authorizer_is_handed_its_setting(
        routing_authorizer: dict[str, object], variable: str) -> None:
    assert variable in _authorizer_variables(routing_authorizer)


def test_the_authorizer_is_handed_the_parameter_the_stack_declares(
        routing_authorizer: dict[str, object]) -> None:
    variables = _authorizer_variables(routing_authorizer)
    assert "aws_ssm_parameter.api_key.name" in str(variables["API_KEY_PARAMETER"])


def test_the_hosted_domain_is_the_one_the_mail_is_hosted_on(
        routing_authorizer: dict[str, object]) -> None:
    assert _authorizer_variables(routing_authorizer)["HOSTED_DOMAIN"] == "10ulabs.com"


def test_the_client_id_is_a_google_one(routing_authorizer: dict[str, object]) -> None:
    client_id = str(_authorizer_variables(routing_authorizer)["GOOGLE_CLIENT_ID"])
    assert client_id.endswith(".apps.googleusercontent.com")


def test_the_api_key_is_kept_encrypted(routing_authorizer: dict[str, object]) -> None:
    parameter = _resource(routing_authorizer, "aws_ssm_parameter", "api_key")
    assert parameter["type"] == "SecureString"


def test_the_api_key_is_generated_not_written_down(
        routing_authorizer: dict[str, object]) -> None:
    parameter = _resource(routing_authorizer, "aws_ssm_parameter", "api_key")
    assert "random_password.api_key.result" in str(parameter["value"])


def test_the_api_key_is_long_enough_to_be_unguessable(
        routing_authorizer: dict[str, object]) -> None:
    generated = _resource(routing_authorizer, "random_password", "api_key")
    assert int(generated["length"]) >= 32


def test_the_gateway_may_invoke_the_authorizer(routing_authorizer: dict[str, object]) -> None:
    permission = _resource(routing_authorizer, "aws_lambda_permission", "api_gateway")
    assert permission["principal"] == "apigateway.amazonaws.com"


def test_the_authorizer_role_may_read_the_api_key(routing_iam: dict[str, object]) -> None:
    policy = _resource(routing_iam, "aws_iam_role_policy", "api_key_access")
    assert "ssm:GetParameter" in str(policy["policy"])


def _encoded(policy: dict[str, Any]) -> dict[str, Any]:
    rendered = str(policy["policy"])
    document: dict[str, Any] = json.loads(rendered.removeprefix("${jsonencode(").removesuffix(")}"))
    return document


def test_the_authorizer_role_may_read_nothing_but_the_two_parameters(
        routing_iam: dict[str, object]) -> None:
    policy = _encoded(_resource(routing_iam, "aws_iam_role_policy", "api_key_access"))
    assert sorted(policy["Statement"][0]["Resource"]) == [
        "${aws_ssm_parameter.api_key.arn}",
        "${aws_ssm_parameter.authorized_accounts.arn}",
    ]


def test_the_authorized_accounts_are_kept_as_a_list(
        routing_authorizer: dict[str, object]) -> None:
    parameter = _resource(routing_authorizer, "aws_ssm_parameter", "authorized_accounts")
    assert parameter["type"] == "StringList"


def test_the_authorized_accounts_are_kept_under_the_product_prefix(
        routing_authorizer: dict[str, object]) -> None:
    parameter = _resource(routing_authorizer, "aws_ssm_parameter", "authorized_accounts")
    assert parameter["name"] == "/wan-synthesizer/authorized-accounts"


def test_the_authorized_accounts_are_the_ones_the_deploy_passes(
        routing_authorizer: dict[str, object]) -> None:
    parameter = _resource(routing_authorizer, "aws_ssm_parameter", "authorized_accounts")
    assert parameter["value"] == "${var.authorized_accounts}"


def _variable(routing_authorizer: dict[str, object], name: str) -> dict[str, Any]:
    for block in cast("list[dict[str, Any]]", routing_authorizer.get("variable", [])):
        if name in block:
            return dict(block[name])
    raise AssertionError(f"variable {name} is not declared")


def test_the_deploy_must_pass_the_authorized_accounts_as_one_string(
        routing_authorizer: dict[str, object]) -> None:
    variable = _variable(routing_authorizer, "authorized_accounts")
    assert (variable["type"], "default" in variable) == ("string", False)


def test_every_passed_account_is_held_to_the_hosted_domain(
        routing_authorizer: dict[str, object]) -> None:
    condition = _variable(routing_authorizer, "authorized_accounts")["validation"][0]["condition"]
    assert 'endswith(trimspace(account), "@10ulabs.com")' in condition


def test_the_authorized_accounts_are_the_only_variable(
        routing_authorizer: dict[str, object]) -> None:
    declared = [
        name
        for block in cast("list[dict[str, Any]]", routing_authorizer.get("variable", []))
        for name in block
    ]
    assert declared == ["authorized_accounts"]


def test_the_authorizer_is_handed_the_list_the_stack_declares(
        routing_authorizer: dict[str, object]) -> None:
    variables = _authorizer_variables(routing_authorizer)
    expected = "${aws_ssm_parameter.authorized_accounts.name}"
    assert variables["AUTHORIZED_ACCOUNTS_PARAMETER"] == expected


def test_the_api_key_parameter_is_published_for_the_seed(routing_dir: Path) -> None:
    outputs = output_values(routing_dir / "outputs.tf")
    assert "aws_ssm_parameter.api_key.name" in str(outputs["api_key_parameter_name"])
