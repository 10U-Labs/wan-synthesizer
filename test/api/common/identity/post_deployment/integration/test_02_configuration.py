from __future__ import annotations

from typing import Any


def test_the_live_trust_admits_the_web_identity_action_alone(
        live_trust_statement: dict[str, Any]) -> None:
    assert live_trust_statement["Action"] == "sts:AssumeRoleWithWebIdentity"


def test_the_live_trust_names_the_github_provider(
        live_trust_statement: dict[str, Any], config: dict[str, object]) -> None:
    expected = (
        f"arn:aws:iam::{config['aws_account_id']}:oidc-provider/"
        "token.actions.githubusercontent.com"
    )
    assert live_trust_statement["Principal"] == {"Federated": expected}


def test_the_live_trust_matches_exactly_and_never_by_pattern(
        live_trust_statement: dict[str, Any]) -> None:
    assert set(live_trust_statement["Condition"]) == {"StringEquals"}


def test_the_live_trust_holds_the_audience_and_the_subject(
        live_trust_claims: dict[str, Any]) -> None:
    assert set(live_trust_claims) == {"aud", "sub"}


def test_the_live_audience_is_sts(live_trust_claims: dict[str, Any]) -> None:
    assert live_trust_claims["aud"] == "sts.amazonaws.com"


def test_the_live_subject_is_the_declared_one_alone(
        live_trust_claims: dict[str, Any], declared_subject: str) -> None:
    assert live_trust_claims["sub"] == declared_subject


def test_the_provider_admits_sts_as_its_audience(
        iam_client: Any, live_trust_statement: dict[str, Any]) -> None:
    provider = iam_client.get_open_id_connect_provider(
        OpenIDConnectProviderArn=live_trust_statement["Principal"]["Federated"])
    assert provider["ClientIDList"] == ["sts.amazonaws.com"]


def test_no_managed_policy_is_attached(iam_client: Any, role_name: str) -> None:
    attached = iam_client.list_attached_role_policies(RoleName=role_name)["AttachedPolicies"]
    assert attached == []


def test_the_live_inline_policies_are_the_declared_ones(
        live_inline_policies: dict[str, dict[str, Any]],
        declared_actions: dict[str, set[str]]) -> None:
    assert sorted(live_inline_policies) == sorted(declared_actions)


def test_each_live_policy_carries_the_declared_actions_and_no_other(
        live_inline_policies: dict[str, dict[str, Any]], live_actions_of: Any,
        declared_actions: dict[str, set[str]]) -> None:
    live = {
        name: {
            action for statement in document["Statement"] for action in live_actions_of(statement)
        }
        for name, document in live_inline_policies.items()
    }
    assert live == declared_actions


def test_no_live_statement_denies(live_statements: list[dict[str, Any]]) -> None:
    assert [s["Sid"] for s in live_statements if s["Effect"] != "Allow"] == []


def test_no_live_statement_carries_a_wildcard_action(
        live_statements: list[dict[str, Any]], live_actions_of: Any) -> None:
    assert [
        action
        for statement in live_statements
        for action in live_actions_of(statement)
        if "*" in action
    ] == []


def test_no_live_statement_reaches_every_resource(
        live_statements: list[dict[str, Any]], live_actions_of: Any,
        listings_iam_cannot_scope: frozenset[str]) -> None:
    assert [
        statement["Sid"]
        for statement in live_statements
        if statement["Resource"] in ("*", ["*"])
        and not set(live_actions_of(statement)) <= listings_iam_cannot_scope
    ] == []


def test_the_live_session_lasts_an_hour(live_role: dict[str, Any]) -> None:
    assert live_role["MaxSessionDuration"] == 3600


def test_the_live_role_is_tagged_as_this_stack(
        live_role: dict[str, Any], identity_tags: dict[str, str]) -> None:
    assert {tag["Key"]: tag["Value"] for tag in live_role.get("Tags", [])} == identity_tags
