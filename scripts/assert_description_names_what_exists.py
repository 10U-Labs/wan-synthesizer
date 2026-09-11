from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from repo_utils import print_annotations, root_reading_parser

OPENAPI = Path("src", "www", "api", "openapi.json")
TREES = (Path("src"), Path("lib", "python"), Path("scripts"), Path("etc"))
SUFFIXES = frozenset({".py", ".js", ".json", ".tf", ".yml"})
UNREAD = (OPENAPI, Path("src", "www", "spa", "vendor"))
DESCRIPTION = "description"
NAMED = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")
SHORTEST = 4


def descriptions(spec: Any) -> list[str]:
    if isinstance(spec, list):
        return [found for held in spec for found in descriptions(held)]
    if not isinstance(spec, dict):
        return []
    return [
        found
        for key, held in spec.items()
        for found in (
            [held] if key == DESCRIPTION and isinstance(held, str) else descriptions(held)
        )
    ]


def identifiers(description: str) -> frozenset[str]:
    return frozenset(
        found for found in NAMED.findall(description) if len(found) >= SHORTEST
    )


def _unread(relative: Path) -> bool:
    return any(skipped == relative or skipped in relative.parents for skipped in UNREAD)


def _searched(root: Path) -> list[Path]:
    return [
        path
        for tree in TREES
        for path in sorted((root / tree).rglob("*"))
        if path.suffix in SUFFIXES and not _unread(path.relative_to(root))
    ]


def named_in_the_trees(root: Path) -> frozenset[str]:
    return frozenset(
        found
        for path in _searched(root)
        for found in NAMED.findall(path.read_text(encoding="utf-8"))
    )


def unnamed_identifiers(root: Path) -> list[tuple[str, str]]:
    declared = named_in_the_trees(root)
    spec = json.loads((root / OPENAPI).read_text(encoding="utf-8"))
    return sorted({
        (found, description)
        for description in descriptions(spec)
        for found in identifiers(description) - declared
    })


def main(argv: list[str] | None = None) -> int:
    parser = root_reading_parser(
        "Assert every served description names only identifiers this repository still has."
    )
    return print_annotations([
        f"::error file={OPENAPI}::{OPENAPI} describes {found},"
        f" and nothing this repository holds names it: {description}"
        for found, description in unnamed_identifiers(parser.parse_args(argv).root)
    ])
