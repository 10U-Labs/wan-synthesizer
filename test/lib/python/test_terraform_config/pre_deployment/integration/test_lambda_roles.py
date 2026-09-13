from __future__ import annotations

import json
from typing import Any

from test_terraform_config import STACKS_DIR, declared_state_keys, lambda_handler_names, load_tf

_JSONENCODE = "${jsonencode("
_STREAM_WRITES = {"logs:CreateLogStream", "logs:PutLogEvents"}


def _stacks() -> dict[str, list[dict[str, Any]]]:
    return {
        stack: [
            block
            for path in sorted((STACKS_DIR / stack).glob("*.tf"))
            for block in load_tf(path).get("resource", [])
        ]
        for stack in declared_state_keys()
    }


def _declared(blocks: list[dict[str, Any]], kind: str) -> dict[str, dict[str, Any]]:
    declared: dict[str, dict[str, Any]] = {}
    for block in blocks:
        declared.update(block.get(kind, {}))
    return declared


def _statements(policy: dict[str, Any]) -> list[dict[str, Any]]:
    encoded = str(policy["policy"])
    if not encoded.startswith(_JSONENCODE):
        return []
    return list(json.loads(encoded[len(_JSONENCODE):-2])["Statement"])


def _inline_statements() -> list[tuple[str, str, dict[str, Any]]]:
    return [
        (stack, name, statement)
        for stack, blocks in _stacks().items()
        for name, policy in _declared(blocks, "aws_iam_role_policy").items()
        for statement in _statements(policy)
    ]


def _log_statements_of(blocks: list[dict[str, Any]], role: str) -> list[dict[str, Any]]:
    return [
        statement
        for policy in _declared(blocks, "aws_iam_role_policy").values()
        if policy["role"] == f"${{aws_iam_role.{role}.id}}"
        for statement in _statements(policy)
        if any(str(action).startswith("logs:") for action in statement["Action"])
    ]


def _reference(expression: str, kind: str, attribute: str) -> str:
    return str(expression).removeprefix(f"${{{kind}.").removesuffix(f".{attribute}}}")


def _functions() -> list[tuple[str, str, dict[str, Any], list[dict[str, Any]]]]:
    return [
        (stack, name, function, blocks)
        for stack, blocks in _stacks().items()
        for name, function in _declared(blocks, "aws_lambda_function").items()
    ]


def _log_groups_granted() -> dict[tuple[str, str], list[str]]:
    return {
        (stack, name): [
            resource
            for statement in _log_statements_of(
                blocks, _reference(function["role"], "aws_iam_role", "arn"))
            for resource in statement["Resource"]
        ]
        for stack, name, function, blocks in _functions()
    }


def _log_groups_logged_to() -> dict[tuple[str, str], list[str]]:
    return {
        (stack, name): [
            "${aws_cloudwatch_log_group."
            + _reference(logging["log_group"], "aws_cloudwatch_log_group", "name")
            + ".arn}:*"
            for logging in function["logging_config"]
        ]
        for stack, name, function, _blocks in _functions()
    }


def test_every_stack_is_read() -> None:
    assert sorted(_stacks()) == sorted(
        str(path.parent.relative_to(STACKS_DIR)) for path in STACKS_DIR.rglob("backend.tf"))


def test_no_stack_attaches_a_managed_policy() -> None:
    assert [
        (stack, name)
        for stack, blocks in _stacks().items()
        for name in _declared(blocks, "aws_iam_role_policy_attachment")
    ] == []


def test_no_inline_statement_reaches_every_resource() -> None:
    assert [
        (stack, name)
        for stack, name, statement in _inline_statements()
        if statement["Resource"] in ("*", ["*"])
    ] == []


def test_every_function_declares_the_log_group_it_logs_to() -> None:
    assert [
        (stack, name)
        for stack, name, function, _blocks in _functions()
        if len(function.get("logging_config", [])) != 1
    ] == []


def test_every_function_role_writes_the_log_group_its_function_logs_to_and_no_other() -> None:
    assert _log_groups_granted() == _log_groups_logged_to()


def test_every_log_grant_is_a_stream_write() -> None:
    assert [
        (stack, name)
        for stack, name, statement in _inline_statements()
        if any(str(action).startswith("logs:") for action in statement["Action"])
        and set(statement["Action"]) != _STREAM_WRITES
    ] == []


def test_at_least_every_named_handler_is_held() -> None:
    assert len(_functions()) >= len(lambda_handler_names())
