from __future__ import annotations

from typing import Any


def test_the_role_exists(live_role: dict[str, Any], role_name: str) -> None:
    assert live_role["RoleName"] == role_name


def test_this_run_is_the_declared_role(sts_client: Any, role_name: str) -> None:
    assert f":assumed-role/{role_name}/" in sts_client.get_caller_identity()["Arn"]


def test_the_github_provider_exists(
        iam_client: Any, live_trust_statement: dict[str, Any]) -> None:
    provider = iam_client.get_open_id_connect_provider(
        OpenIDConnectProviderArn=live_trust_statement["Principal"]["Federated"])
    assert provider["Url"] == "token.actions.githubusercontent.com"
