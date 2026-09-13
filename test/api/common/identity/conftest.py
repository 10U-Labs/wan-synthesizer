from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

import pytest

from repo_utils import REPO_ROOT
from test_terraform_config import find_resource, load_tf

IDENTITY_DIR = REPO_ROOT / "src" / "api" / "common" / "identity"
TRUST_DOCUMENT = "trust"
IMMUTABLE_SUBJECT = re.compile(r"^repo:([^/@]+)@\d+/([^/@]+)@\d+:ref:(.+)$")
LISTINGS_IAM_CANNOT_SCOPE = frozenset({
    "cloudfront:ListDistributions", "lambda:ListFunctions", "ssm:DescribeParameters",
})


def _blocks(document: dict[str, object], kind: str) -> list[dict[str, Any]]:
    return cast("list[dict[str, Any]]", document.get(kind, []))


def _policy_documents(document: dict[str, object]) -> dict[str, list[dict[str, Any]]]:
    documents: dict[str, list[dict[str, Any]]] = {}
    for block in _blocks(document, "data"):
        for name, body in block.get("aws_iam_policy_document", {}).items():
            documents[name] = list(body["statement"])
    return documents


def _resources_of(document: dict[str, object], resource_type: str) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for block in _blocks(document, "resource"):
        found.update(block.get(resource_type, {}))
    return found


def _resolve(expression: str, values: dict[str, Any]) -> str:
    resolved = expression
    for _ in range(3):
        for name, value in values.items():
            resolved = resolved.replace("${local." + name + "}", str(value))
    return resolved


def _declared(document: dict[str, object], resource_type: str, name: str) -> dict[str, Any]:
    body = find_resource(document, resource_type, name)
    if body is None:
        raise AssertionError(f"{resource_type}.{name} is not declared")
    return body


def _matched(subject: str) -> re.Match[str]:
    match = IMMUTABLE_SUBJECT.match(subject)
    if match is None:
        raise AssertionError(f"{subject} is not an immutable GitHub subject")
    return match


@pytest.fixture
def identity_dir() -> Path:
    return IDENTITY_DIR


@pytest.fixture(name="identity_main")
def identity_main_fixture() -> dict[str, object]:
    return load_tf(IDENTITY_DIR / "main.tf")


@pytest.fixture(name="identity_iam")
def identity_iam_fixture() -> dict[str, object]:
    return load_tf(IDENTITY_DIR / "iam.tf")


@pytest.fixture
def identity_outputs() -> dict[str, object]:
    return load_tf(IDENTITY_DIR / "outputs.tf")


@pytest.fixture
def identity_tags() -> dict[str, str]:
    providers = _blocks(load_tf(IDENTITY_DIR / "providers.tf"), "provider")
    return dict(providers[0]["aws"]["default_tags"][0]["tags"])


@pytest.fixture(name="identity_locals")
def identity_locals_fixture(
        identity_main: dict[str, object], identity_iam: dict[str, object]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for document in (identity_main, identity_iam):
        for block in _blocks(document, "locals"):
            merged.update(block)
    return merged


@pytest.fixture
def blocks_of() -> Any:
    return _blocks


@pytest.fixture
def resources_of() -> Any:
    return _resources_of


@pytest.fixture
def declared() -> Any:
    return _declared


@pytest.fixture(name="resolve")
def resolve_fixture(identity_locals: dict[str, Any]) -> Any:
    return lambda expression: _resolve(expression, identity_locals)


@pytest.fixture
def matched_subject() -> Any:
    return _matched


@pytest.fixture
def listings_iam_cannot_scope() -> frozenset[str]:
    return LISTINGS_IAM_CANNOT_SCOPE


@pytest.fixture
def role_name(identity_locals: dict[str, Any]) -> str:
    return str(identity_locals["role_name"])


@pytest.fixture
def seed_role_name(identity_locals: dict[str, Any]) -> str:
    return str(identity_locals["seed_role_name"])


@pytest.fixture
def declared_subject(identity_locals: dict[str, Any], resolve: Any) -> str:
    return str(resolve(str(identity_locals["subject"])))


@pytest.fixture
def trust_document_name() -> str:
    return TRUST_DOCUMENT


@pytest.fixture(name="trust_statement")
def trust_statement_fixture(identity_main: dict[str, object]) -> dict[str, Any]:
    statements = _policy_documents(identity_main)[TRUST_DOCUMENT]
    if len(statements) != 1:
        raise AssertionError("the trust document must carry exactly one statement")
    return statements[0]


@pytest.fixture
def trust_conditions(trust_statement: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(condition["variable"]).rsplit(":", 1)[-1]: condition
        for condition in trust_statement["condition"]
    }


@pytest.fixture(name="permission_documents")
def permission_documents_fixture(
        identity_iam: dict[str, object]) -> dict[str, list[dict[str, Any]]]:
    return _policy_documents(identity_iam)


@pytest.fixture
def permission_statements(
        permission_documents: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        statement
        for statements in permission_documents.values()
        for statement in statements
    ]


@pytest.fixture(name="inline_policies")
def inline_policies_fixture(identity_iam: dict[str, object]) -> dict[str, dict[str, Any]]:
    return _resources_of(identity_iam, "aws_iam_role_policy")


@pytest.fixture(name="inline_policies_of")
def inline_policies_of_fixture(inline_policies: dict[str, dict[str, Any]]) -> Any:
    return lambda role: {
        name: policy for name, policy in inline_policies.items()
        if policy["role"] == f"${{aws_iam_role.{role}.id}}"
    }


@pytest.fixture
def seed_statements(
        permission_documents: dict[str, list[dict[str, Any]]],
        inline_policies_of: Any) -> list[dict[str, Any]]:
    return [
        statement
        for name in inline_policies_of("seed")
        for statement in permission_documents[name]
    ]


@pytest.fixture
def deploy_role(identity_main: dict[str, object]) -> dict[str, Any]:
    return _declared(identity_main, "aws_iam_role", "deploy")


@pytest.fixture
def seed_role(identity_main: dict[str, object]) -> dict[str, Any]:
    return _declared(identity_main, "aws_iam_role", "seed")
