from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from repo_utils import print_annotations, root_reading_parser

OPENAPI = Path("src", "www", "api", "openapi.json")
TENANTS = Path("src", "api", "endpoints", "tenants", "lambdas", "handler.py")
SPA = Path("src", "www", "spa", "app.js")
ROUTE = "/wan-synthesizer/tenants/{tenant}/"
COLLECTIONS = "_WAN_COLLECTIONS"
INPUTS = "_INPUTS"
ROUTES = "the routes it documents"
MAP = "the collections the map fetches"
FETCHED = re.compile(r"/tenants/\$\{tenantId\}/([a-z0-9-]+)`")

_Held = tuple[Path, str, frozenset[str]]


def _read(root: Path, relative: Path) -> str:
    return (root / relative).read_text(encoding="utf-8")


def _routes(root: Path, verb: str) -> frozenset[str]:
    spec: dict[str, Any] = json.loads(_read(root, OPENAPI))
    return frozenset(
        route.removeprefix(ROUTE)
        for route, verbs in spec["paths"].items()
        if route.startswith(ROUTE) and verb in verbs
    )


def documented_inputs(root: Path) -> frozenset[str]:
    return _routes(root, "put")


def documented_collections(root: Path) -> frozenset[str]:
    return _routes(root, "get") - documented_inputs(root)


def _assigns(node: ast.Assign, name: str) -> bool:
    return any(isinstance(target, ast.Name) and target.id == name for target in node.targets)


def _strings_in(node: ast.expr) -> frozenset[str]:
    return frozenset(
        held.value
        for held in ast.walk(node)
        if isinstance(held, ast.Constant) and isinstance(held.value, str)
    )


def named_strings(source: str, name: str) -> frozenset[str]:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assign) and _assigns(node, name):
            return _strings_in(node.value)
    return frozenset()


def fetched_collections(source: str) -> frozenset[str]:
    return frozenset(FETCHED.findall(source))


def _apart(here: _Held, there: _Held) -> list[str]:
    where, held, names = here
    against, missing, known = there
    return [
        f"::error file={where}::{where} lists {name} in {held},"
        f" and {against} leaves it out of {missing}"
        for name in sorted(names - known)
    ]


def _both_ways(one: _Held, other: _Held) -> list[str]:
    return _apart(one, other) + _apart(other, one)


def disagreements(root: Path) -> list[str]:
    tenants = _read(root, TENANTS)
    collections: _Held = (TENANTS, COLLECTIONS, named_strings(tenants, COLLECTIONS))
    inputs: _Held = (TENANTS, INPUTS, named_strings(tenants, INPUTS))
    return (
        _both_ways(collections, (OPENAPI, ROUTES, documented_collections(root)))
        + _both_ways(inputs, (OPENAPI, ROUTES, documented_inputs(root)))
        + _apart((SPA, MAP, fetched_collections(_read(root, SPA))), collections)
    )


def main(argv: list[str] | None = None) -> int:
    parser = root_reading_parser(
        "Assert every hand-written list of resource names agrees with the served surface."
    )
    return print_annotations(disagreements(parser.parse_args(argv).root))
