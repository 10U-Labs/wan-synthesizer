from __future__ import annotations

from typing import Any

from test_fixtures.aws import log_group_arn, log_resources_of, managed_policies_of


def test_no_expiry_rule_is_scoped_to_an_object_prefix(
        live_lifecycle_rules: dict[str, Any]) -> None:
    assert [
        rule_id for rule_id, rule in live_lifecycle_rules.items()
        if rule.get("Filter", {}).get("Prefix")
    ] == []


def test_the_prunes_role_attaches_no_managed_policy(
        iam_client: Any, prune_config: dict[str, Any]) -> None:
    assert not managed_policies_of(iam_client, prune_config)


def test_the_prunes_role_writes_its_own_log_group_alone(
        iam_client: Any, logs_client: Any, prune_config: dict[str, Any]) -> None:
    granted = log_resources_of(iam_client, prune_config)
    assert granted == [log_group_arn(logs_client, prune_config)]
