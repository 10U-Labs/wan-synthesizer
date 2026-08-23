from __future__ import annotations

import ast
from pathlib import Path

from repo_utils import root_reading_parser

FIELD_TREES = (Path("src"), Path("lib", "python"), Path("scripts"))
READ_TREES = FIELD_TREES + (Path("test"),)
DATACLASS = "dataclass"


def python_files(root: Path, trees: tuple[Path, ...]) -> dict[Path, list[str]]:
    read: dict[Path, list[str]] = {}
    for tree in trees:
        for path in sorted((root / tree).rglob("*.py")):
            read[path.relative_to(root)] = path.read_text(encoding="utf-8").splitlines()
    return read


def _is_dataclass(node: ast.ClassDef) -> bool:
    for decorator in node.decorator_list:
        named = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(named, ast.Name) and named.id == DATACLASS:
            return True
    return False


def dataclass_fields(lines: list[str]) -> list[tuple[int, str, str]]:
    declared: list[tuple[int, str, str]] = []
    for node in ast.walk(ast.parse("\n".join(lines))):
        if not isinstance(node, ast.ClassDef) or not _is_dataclass(node):
            continue
        for statement in node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                declared.append((statement.lineno, node.name, statement.target.id))
    return declared


def _instance_classes(tree: ast.Module, classes: frozenset[str]) -> dict[str, str]:
    holding: dict[str, str] = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.arg)
            and isinstance(node.annotation, ast.Name)
            and node.annotation.id in classes
        ):
            holding[node.arg] = node.annotation.id
    return holding


def attribute_reads(lines: list[str], classes: frozenset[str]) -> set[tuple[str | None, str]]:
    tree = ast.parse("\n".join(lines))
    holding = _instance_classes(tree, classes)
    read: set[tuple[str | None, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            base = node.value
            read.add((holding.get(base.id) if isinstance(base, ast.Name) else None, node.attr))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            read.add((None, node.id))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            read.add((None, node.value))
    return read


def _declares_fields(path: Path) -> bool:
    return any(tree in path.parents for tree in FIELD_TREES)


def unread_fields(root: Path) -> list[tuple[Path, int, str]]:
    source = python_files(root, READ_TREES)
    declared = [
        (path, lineno, owner, name)
        for path, lines in source.items()
        if _declares_fields(path)
        for lineno, owner, name in dataclass_fields(lines)
    ]
    classes = frozenset(owner for _, _, owner, _ in declared)
    read: set[tuple[str | None, str]] = set()
    for lines in source.values():
        read |= attribute_reads(lines, classes)
    loose = {name for owner, name in read if owner is None}
    return sorted(
        (path, lineno, f"{owner}.{name}")
        for path, lineno, owner, name in declared
        if name not in loose and (owner, name) not in read
    )


def main(argv: list[str] | None = None) -> int:
    parser = root_reading_parser(
        "Assert every dataclass field the repository declares is read somewhere."
    )
    arguments = parser.parse_args(argv)
    reported = [
        f"::error file={path},line={lineno}::{path}:{lineno} writes {name}"
        f" and nothing reads it; delete it or read it"
        for path, lineno, name in unread_fields(arguments.root)
    ]
    for line in reported:
        print(line)
    return 1 if reported else 0
