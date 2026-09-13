from __future__ import annotations

from typing import Any

import pytest

ISSUER = "token.actions.githubusercontent.com"
EXCLUSIVE_ATTACHMENTS = "aws_iam_role_policy_attachments_exclusive"
EXCLUSIVE_POLICIES = "aws_iam_role_policies_exclusive"


def test_the_role_keeps_the_name_every_workflow_assumes(role_name: str) -> None:
    assert role_name == "TenULabsWanSynthesizerRole"


def test_the_role_is_declared_by_that_name(deploy_role: dict[str, Any]) -> None:
    assert deploy_role["name"] == "${local.role_name}"


def test_the_existing_role_is_imported_rather_than_recreated(
        identity_main: dict[str, object], role_name: str) -> None:
    assert identity_main.get("import") == [{"to": "${aws_iam_role.deploy}", "id": role_name}]


def test_the_role_is_trusted_by_the_declared_document(
        deploy_role: dict[str, Any], trust_document_name: str) -> None:
    expected = f"${{data.aws_iam_policy_document.{trust_document_name}.json}}"
    assert deploy_role["assume_role_policy"] == expected


def test_the_role_is_assumable_for_an_hour(deploy_role: dict[str, Any]) -> None:
    assert deploy_role["max_session_duration"] == 3600


def test_the_trust_admits_the_web_identity_action_alone(
        trust_statement: dict[str, Any]) -> None:
    assert trust_statement["actions"] == ["sts:AssumeRoleWithWebIdentity"]


def test_the_trust_names_the_github_provider_alone(trust_statement: dict[str, Any]) -> None:
    assert trust_statement["principals"] == [{
        "type": "Federated",
        "identifiers": ["${data.aws_iam_openid_connect_provider.github.arn}"],
    }]


def test_the_provider_is_read_by_the_github_issuer(
        identity_main: dict[str, object], blocks_of: Any, resolve: Any) -> None:
    providers = [
        resolve(str(body["url"]))
        for block in blocks_of(identity_main, "data")
        for body in block.get("aws_iam_openid_connect_provider", {}).values()
    ]
    assert providers == [f"https://{ISSUER}"]


def test_the_trust_conditions_are_the_audience_and_the_subject(
        trust_conditions: dict[str, dict[str, Any]]) -> None:
    assert set(trust_conditions) == {"aud", "sub"}


@pytest.mark.parametrize("claim", ["aud", "sub"])
def test_each_trust_condition_reads_a_claim_of_the_github_issuer(
        trust_conditions: dict[str, dict[str, Any]], resolve: Any, claim: str) -> None:
    assert resolve(str(trust_conditions[claim]["variable"])) == f"{ISSUER}:{claim}"


@pytest.mark.parametrize("claim", ["aud", "sub"])
def test_each_trust_condition_is_an_exact_match(
        trust_conditions: dict[str, dict[str, Any]], claim: str) -> None:
    assert trust_conditions[claim]["test"] == "StringEquals"


def test_the_audience_is_sts(trust_conditions: dict[str, dict[str, Any]]) -> None:
    assert trust_conditions["aud"]["values"] == ["sts.amazonaws.com"]


def test_the_trust_names_exactly_one_subject(
        trust_conditions: dict[str, dict[str, Any]]) -> None:
    assert trust_conditions["sub"]["values"] == ["${local.subject}"]


def test_the_subject_names_a_repository_by_its_immutable_ids(
        declared_subject: str, matched_subject: Any) -> None:
    assert matched_subject(declared_subject) is not None


def test_the_subject_names_this_repository(
        declared_subject: str, matched_subject: Any, identity_tags: dict[str, str]) -> None:
    match = matched_subject(declared_subject)
    assert f"{match.group(1)}/{match.group(2)}" == identity_tags["Repository"]


def test_the_subject_names_the_main_branch_alone(
        declared_subject: str, matched_subject: Any) -> None:
    assert matched_subject(declared_subject).group(3) == "refs/heads/main"


def test_no_managed_policy_is_attached(identity_main: dict[str, object], declared: Any) -> None:
    assert declared(identity_main, EXCLUSIVE_ATTACHMENTS, "deploy")["policy_arns"] == []


@pytest.mark.parametrize("resource_type", [EXCLUSIVE_ATTACHMENTS, EXCLUSIVE_POLICIES])
def test_each_exclusive_list_is_held_on_the_declared_role(
        identity_main: dict[str, object], declared: Any, resource_type: str) -> None:
    exclusive = declared(identity_main, resource_type, "deploy")
    assert exclusive["role_name"] == "${aws_iam_role.deploy.name}"


def test_every_inline_policy_is_in_the_exclusive_list(
        identity_main: dict[str, object], declared: Any,
        inline_policies: dict[str, dict[str, Any]]) -> None:
    exclusive = declared(identity_main, EXCLUSIVE_POLICIES, "deploy")
    assert sorted(exclusive["policy_names"]) == sorted(
        f"${{aws_iam_role_policy.{name}.name}}" for name in inline_policies)


def test_every_inline_policy_is_attached_to_the_declared_role(
        inline_policies: dict[str, dict[str, Any]]) -> None:
    roles = {policy["role"] for policy in inline_policies.values()}
    assert roles == {"${aws_iam_role.deploy.id}"}


def test_every_inline_policy_is_named_after_its_document(
        inline_policies: dict[str, dict[str, Any]]) -> None:
    assert [
        name for name, policy in inline_policies.items()
        if policy["policy"] != f"${{data.aws_iam_policy_document.{name}.json}}"
    ] == []


def test_every_permission_document_is_an_inline_policy(
        permission_documents: dict[str, list[dict[str, Any]]],
        inline_policies: dict[str, dict[str, Any]]) -> None:
    assert sorted(permission_documents) == sorted(inline_policies)


def test_the_trust_is_not_a_permission_document(
        permission_documents: dict[str, list[dict[str, Any]]],
        trust_document_name: str) -> None:
    assert trust_document_name not in permission_documents


def test_no_statement_denies(permission_statements: list[dict[str, Any]]) -> None:
    assert [s for s in permission_statements if s.get("effect", "Allow") != "Allow"] == []


def test_every_statement_names_its_actions(permission_statements: list[dict[str, Any]]) -> None:
    assert [s for s in permission_statements if not s.get("actions")] == []


def test_no_action_is_a_wildcard(permission_statements: list[dict[str, Any]]) -> None:
    assert [
        action
        for statement in permission_statements
        for action in statement["actions"]
        if "*" in action
    ] == []


def test_every_statement_names_its_resources(
        permission_statements: list[dict[str, Any]]) -> None:
    assert [s for s in permission_statements if not s.get("resources")] == []


def test_no_statement_reaches_every_resource(
        permission_statements: list[dict[str, Any]],
        listings_iam_cannot_scope: frozenset[str]) -> None:
    assert [
        statement["sid"]
        for statement in permission_statements
        if "*" in statement["resources"]
        and not set(statement["actions"]) <= listings_iam_cannot_scope
    ] == []


def test_the_listings_iam_cannot_scope_are_granted_on_nothing_narrower(
        permission_statements: list[dict[str, Any]],
        listings_iam_cannot_scope: frozenset[str]) -> None:
    assert {
        action
        for statement in permission_statements
        for action in statement["actions"]
        if action in listings_iam_cannot_scope and statement["resources"] != ["*"]
    } == set()


def test_no_resource_is_a_whole_service(
        permission_statements: list[dict[str, Any]], resolve: Any) -> None:
    assert [
        resource
        for statement in permission_statements
        for resource in statement["resources"]
        if resource != "*" and resolve(resource).split(":", 5)[-1] == "*"
    ] == []


def test_no_statement_lacks_a_sid(permission_statements: list[dict[str, Any]]) -> None:
    assert [s for s in permission_statements if not s.get("sid")] == []


def test_every_sid_is_unique(permission_statements: list[dict[str, Any]]) -> None:
    sids = [s["sid"] for s in permission_statements]
    assert sorted(set(sids)) == sorted(sids)


def test_the_role_may_not_attach_a_managed_policy_to_itself(
        permission_statements: list[dict[str, Any]], resolve: Any, role_name: str) -> None:
    assert [
        statement["sid"]
        for statement in permission_statements
        if "iam:AttachRolePolicy" in statement["actions"]
        and any(resolve(resource).endswith(f":role/{role_name}")
                for resource in statement["resources"])
    ] == []


def test_the_role_passes_lambda_roles_to_lambda_alone(
        permission_statements: list[dict[str, Any]]) -> None:
    assert [
        statement["sid"]
        for statement in permission_statements
        if "iam:PassRole" in statement["actions"]
        and statement.get("condition") != [{
            "test": "StringEquals",
            "variable": "iam:PassedToService",
            "values": ["lambda.amazonaws.com"],
        }]
    ] == []


def test_the_data_sources_are_the_provider_and_the_policy_documents(
        identity_main: dict[str, object], identity_iam: dict[str, object],
        blocks_of: Any) -> None:
    kinds = {
        kind
        for document in (identity_main, identity_iam)
        for block in blocks_of(document, "data")
        for kind in block
    }
    assert kinds == {"aws_iam_openid_connect_provider", "aws_iam_policy_document"}


def test_the_stack_declares_the_role_and_its_two_exclusive_lists_and_nothing_else(
        identity_main: dict[str, object], blocks_of: Any) -> None:
    kinds = {kind for block in blocks_of(identity_main, "resource") for kind in block}
    assert kinds == {"aws_iam_role", EXCLUSIVE_POLICIES, EXCLUSIVE_ATTACHMENTS}


def test_the_permissions_file_declares_inline_policies_and_nothing_else(
        identity_iam: dict[str, object], blocks_of: Any) -> None:
    kinds = {kind for block in blocks_of(identity_iam, "resource") for kind in block}
    assert kinds == {"aws_iam_role_policy"}


def test_the_common_module_is_sourced(identity_main: dict[str, object]) -> None:
    assert identity_main.get("module") == [
        {"common": {"source": "../../../../lib/opentofu/common"}}]


def test_the_outputs_name_the_role_and_the_subject(
        identity_outputs: dict[str, object], blocks_of: Any) -> None:
    names = sorted(name for block in blocks_of(identity_outputs, "output") for name in block)
    assert names == ["role_arn", "role_name", "subject"]


def test_the_stack_is_tagged_as_this_repository(identity_tags: dict[str, str]) -> None:
    assert identity_tags == {
        "ManagedBy": "OpenTofu",
        "Project": "wan-synthesizer",
        "Repository": "10U-Labs/wan-synthesizer",
        "Stack": "common/identity",
    }


def test_the_managed_policies_are_detached_only_once_the_inline_ones_are_in_place(
        identity_main: dict[str, object], declared: Any) -> None:
    exclusive = declared(identity_main, EXCLUSIVE_ATTACHMENTS, "deploy")
    assert exclusive["depends_on"] == ["${aws_iam_role_policies_exclusive.deploy}"]
