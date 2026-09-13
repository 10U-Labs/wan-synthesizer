from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from test_fixtures.aws import (
    LOG_POLICY,
    log_group_arn,
    log_resources_of,
    managed_policies_of,
    role_name_of,
)

_ROLE = "wan-synthesizer-carriers"
_GROUP = "/aws/lambda/wan-synthesizer-carriers"
_GROUP_ARN = f"arn:aws:logs:us-east-2:1:log-group:{_GROUP}:*"
_FUNCTION = {
    "Role": f"arn:aws:iam::1:role/{_ROLE}",
    "LoggingConfig": {"LogGroup": _GROUP},
}


def _iam(asked: dict[str, Any], attached: list[str], resources: list[list[str]]) -> Any:
    def _attached(**kwargs: Any) -> dict[str, Any]:
        asked.update(kwargs)
        return {"AttachedPolicies": [{"PolicyArn": arn} for arn in attached]}

    def _policy(**kwargs: Any) -> dict[str, Any]:
        asked.update(kwargs)
        statements = [{"Effect": "Allow", "Resource": listed} for listed in resources]
        return {"PolicyDocument": {"Statement": statements}}

    return SimpleNamespace(list_attached_role_policies=_attached, get_role_policy=_policy)


def _logs(*groups: dict[str, Any]) -> Any:
    return SimpleNamespace(describe_log_groups=lambda **_kwargs: {"logGroups": list(groups)})


def test_the_role_is_the_last_segment_of_the_functions_role_arn() -> None:
    assert role_name_of(_FUNCTION) == _ROLE


def test_every_attached_policy_is_listed_in_order() -> None:
    assert managed_policies_of(_iam({}, ["arn:b", "arn:a"], []), _FUNCTION) == ["arn:a", "arn:b"]


def test_a_role_with_nothing_attached_lists_nothing() -> None:
    assert not managed_policies_of(_iam({}, [], []), _FUNCTION)


def test_the_attachments_asked_for_are_the_functions_roles() -> None:
    asked: dict[str, Any] = {}
    managed_policies_of(_iam(asked, [], []), _FUNCTION)
    assert asked == {"RoleName": _ROLE}


def test_every_resource_of_every_log_statement_is_listed_in_order() -> None:
    iam = _iam({}, [], [["arn:b"], ["arn:a", "arn:c"]])
    assert log_resources_of(iam, _FUNCTION) == ["arn:a", "arn:b", "arn:c"]


def test_the_log_policy_asked_for_is_the_functions_roles() -> None:
    asked: dict[str, Any] = {}
    log_resources_of(_iam(asked, [], []), _FUNCTION)
    assert asked == {"RoleName": _ROLE, "PolicyName": LOG_POLICY}


def test_the_arn_reported_is_the_one_cloudwatch_holds_for_the_functions_group() -> None:
    neighbour = {"logGroupName": f"{_GROUP}-merge", "arn": "arn:other"}
    logs = _logs(neighbour, {"logGroupName": _GROUP, "arn": _GROUP_ARN})
    assert log_group_arn(logs, _FUNCTION) == _GROUP_ARN


def test_a_group_cloudwatch_does_not_hold_has_no_arn() -> None:
    with pytest.raises(StopIteration):
        log_group_arn(_logs(), _FUNCTION)
