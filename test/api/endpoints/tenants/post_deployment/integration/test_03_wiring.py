from __future__ import annotations

from typing import Any
from urllib.request import Request, urlopen

from seed import DEFAULT_API
from test_handler_contracts import SPA_ORIGIN


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


def test_an_answer_carrying_data_names_the_pages_origin_alone(api_key: str) -> None:
    headers = {"Authorization": f"Bearer {api_key}", "Origin": SPA_ORIGIN}
    with urlopen(Request(f"{DEFAULT_API}/tenants", headers=headers), timeout=30) as response:
        assert response.headers["Access-Control-Allow-Origin"] == SPA_ORIGIN
