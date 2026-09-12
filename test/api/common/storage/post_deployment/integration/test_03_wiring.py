from __future__ import annotations

from typing import Any


def test_no_expiry_rule_is_scoped_to_an_object_prefix(
        live_lifecycle_rules: dict[str, Any]) -> None:
    assert [
        rule_id for rule_id, rule in live_lifecycle_rules.items()
        if rule.get("Filter", {}).get("Prefix")
    ] == []
