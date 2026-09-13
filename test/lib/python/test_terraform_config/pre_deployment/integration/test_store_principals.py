from __future__ import annotations

import json
from typing import Any, cast

from test_terraform_config import STACKS_DIR, common_outputs, declared_state_keys, load_tf

_STORE = ("storage.outputs.bucket_arn", "aws_s3_bucket.store.arn", "local.store_bucket")
_DOCUMENT = "${data.aws_iam_policy_document."


def _documents(stack: str) -> list[dict[str, Any]]:
    return [load_tf(path) for path in sorted((STACKS_DIR / stack).glob("*.tf"))]


def _named(
    documents: list[dict[str, Any]], section: str, kind: str
) -> dict[str, dict[str, Any]]:
    named: dict[str, dict[str, Any]] = {}
    for document in documents:
        for block in cast("list[dict[str, Any]]", document.get(section, [])):
            named.update(block.get(kind, {}))
    return named


def _local_values(documents: list[dict[str, Any]]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for document in documents:
        for block in cast("list[dict[str, Any]]", document.get("locals", [])):
            values.update(block)
    return values


def _resolved(value: str, local_values: dict[str, Any]) -> str:
    if value.startswith("${local.") and value.endswith("}"):
        return str(local_values[value[len("${local."):-1]])
    return value


def _touches_the_store(policy: dict[str, Any], documents: list[dict[str, Any]]) -> bool:
    text = str(policy["policy"])
    if text.startswith(_DOCUMENT):
        name = text[len(_DOCUMENT):-len(".json}")]
        text = json.dumps(_named(documents, "data", "aws_iam_policy_document")[name])
    return any(mark in text for mark in _STORE)


def _roles_granted_the_store() -> list[str]:
    granted: set[str] = set()
    for stack in declared_state_keys():
        documents = _documents(stack)
        roles = _named(documents, "resource", "aws_iam_role")
        local_values = _local_values(documents)
        for policy in _named(documents, "resource", "aws_iam_role_policy").values():
            if _touches_the_store(policy, documents):
                role = str(policy["role"]).removeprefix("${aws_iam_role.").removesuffix(".id}")
                granted.add(_resolved(str(roles[role]["name"]), local_values))
    return sorted(granted)


def _store_principals() -> list[str]:
    return [str(name) for name in cast("list[Any]", common_outputs()["store_principals"])]


def test_the_common_module_names_exactly_the_roles_the_tree_grants_the_store() -> None:
    assert _store_principals() == _roles_granted_the_store()


def test_the_store_principals_are_named_once_in_order() -> None:
    assert _store_principals() == sorted(set(_store_principals()))
