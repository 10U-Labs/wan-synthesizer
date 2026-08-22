from __future__ import annotations

import ast
import re
from pathlib import Path

from repo_utils import root_reading_parser

MODULES = Path("lib", "python")
TREES = (Path("lib", "python"), Path("scripts"), Path("test"))
FIELD_TREES = (Path("src"), Path("lib", "python"), Path("scripts"))
READ_TREES = FIELD_TREES + (Path("test"),)
DEFINITIONS = (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef)
DATACLASS = "dataclass"


def python_files(root: Path, trees: tuple[Path, ...]) -> dict[Path, list[str]]:
    read: dict[Path, list[str]] = {}
    for tree in trees:
        for path in sorted((root / tree).rglob("*.py")):
            read[path.relative_to(root)] = path.read_text(encoding="utf-8").splitlines()
    return read


def public_definitions(lines: list[str]) -> list[tuple[int, str]]:
    return [
        (node.lineno, node.name)
        for node in ast.parse("\n".join(lines)).body
        if isinstance(node, DEFINITIONS) and not node.name.startswith("_")
    ]


def named_elsewhere(
    name: str,
    source: dict[Path, list[str]],
    written: tuple[Path, int],
    skipped: Path | None,
) -> bool:
    word = re.compile(r"\b" + re.escape(name) + r"\b")
    for other, lines in source.items():
        if skipped is not None and skipped in other.parents:
            continue
        for number, line in enumerate(lines, 1):
            if (other, number) == written:
                continue
            if word.search(line):
                return True
    return False


def unused_definitions(root: Path, outside_own_tests: bool) -> list[tuple[Path, int, str]]:
    source = python_files(root, TREES)
    unused: list[tuple[Path, int, str]] = []
    for path, lines in source.items():
        if MODULES not in path.parents:
            continue
        skipped = None
        if outside_own_tests and len(path.parts) > len(MODULES.parts) + 1:
            skipped = Path("test", *path.parts[: len(MODULES.parts) + 1])
        for lineno, name in public_definitions(lines):
            if not named_elsewhere(name, source, (path, lineno), skipped):
                unused.append((path, lineno, name))
    return sorted(unused)


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
        "Assert every public definition under lib/python/ is used"
        " and every dataclass field the repository declares is read."
    )
    parser.add_argument(
        "--outside-own-tests",
        action="store_true",
        help="Do not count a use in the module's own directory under test/lib/python/.",
    )
    arguments = parser.parse_args(argv)
    reported = [
        f"::error file={path},line={lineno}::{path}:{lineno} defines {name}"
        f" and nothing outside it uses it; delete it or use it"
        for path, lineno, name in unused_definitions(arguments.root, arguments.outside_own_tests)
    ] + [
        f"::error file={path},line={lineno}::{path}:{lineno} writes {name}"
        f" and nothing reads it; delete it or read it"
        for path, lineno, name in unread_fields(arguments.root)
    ]
    for line in reported:
        print(line)
    return 1 if reported else 0
