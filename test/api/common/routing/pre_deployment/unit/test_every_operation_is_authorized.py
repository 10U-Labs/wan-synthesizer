from __future__ import annotations

import json
from typing import Any

from repo_utils import REPO_ROOT

_METHODS = ("get", "put", "post", "delete", "patch", "head", "options")
_BEARER: list[dict[str, list[str]]] = [{"bearer": []}]


def _spec() -> dict[str, Any]:
    spec: dict[str, Any] = json.loads(
        (REPO_ROOT / "src" / "www" / "api" / "openapi.json").read_text(encoding="utf-8"))
    return spec


def _resolved_security() -> dict[tuple[str, str], list[dict[str, list[str]]]]:
    spec = _spec()
    return {
        (method, path): operation.get("security", spec.get("security", []))
        for path, operations in spec["paths"].items()
        for method, operation in operations.items()
        if method in _METHODS
    }


def test_the_spec_admits_the_bearer_by_default() -> None:
    assert _spec()["security"] == _BEARER


def test_every_operation_but_a_preflight_resolves_to_the_bearer() -> None:
    assert [
        (method, path)
        for (method, path), security in _resolved_security().items()
        if method != "options" and security != _BEARER
    ] == []


def test_every_preflight_resolves_to_no_security_at_all() -> None:
    assert [
        (method, path)
        for (method, path), security in _resolved_security().items()
        if method == "options" and security != []
    ] == []


def test_the_bearer_is_the_one_scheme_the_spec_names() -> None:
    assert list(_spec()["components"]["securitySchemes"]) == ["bearer"]
