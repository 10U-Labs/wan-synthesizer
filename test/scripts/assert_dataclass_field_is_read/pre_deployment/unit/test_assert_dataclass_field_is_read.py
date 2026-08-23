from __future__ import annotations

from pathlib import Path

import pytest

from assert_dataclass_field_is_read import (
    attribute_reads,
    dataclass_fields,
    main,
    python_files,
    unread_fields,
)

MODEL = Path("src", "wan", "model.py")
READER = Path("src", "wan", "read.py")
FIELD_TEST = Path("test", "wan", "pre_deployment", "unit", "test_model.py")
CLASSES = frozenset({"Fiber", "Places"})
MODEL_SOURCE = '''from dataclasses import dataclass


@dataclass(frozen=True)
class Places:
    peers: int
    paths: int
    miles: int


@dataclass
class Fiber:
    miles: int

    def doubled(self) -> int:
        return 2


@total_ordering
class Loose:
    count: int
'''
READER_SOURCE = '''from wan.model import Fiber, Places

KIND = "fiber"


def counted(places: Places) -> int:
    return places.peers


def hauled(fiber: Fiber) -> int:
    return fiber.miles.numerator


def loosened(thing) -> int:
    return thing.count
'''
FIELD_TEST_SOURCE = '''from wan.model import Places


def test_paths(places: Places) -> None:
    assert places.paths == 2
'''


def _write(root: Path, relative: Path, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fields_repo(root: Path) -> Path:
    _write(root, MODEL, MODEL_SOURCE)
    _write(root, READER, READER_SOURCE)
    _write(root, FIELD_TEST, FIELD_TEST_SOURCE)
    return root


def _model_lines(root: Path) -> list[str]:
    return python_files(_fields_repo(root), (Path("src"),))[MODEL]


def _reader_reads(root: Path) -> set[tuple[str | None, str]]:
    lines = python_files(_fields_repo(root), (Path("src"),))[READER]
    return attribute_reads(lines, CLASSES)


def test_python_files_reads_every_python_file_under_the_trees(tmp_path: Path) -> None:
    assert sorted(python_files(_fields_repo(tmp_path), (Path("src"),))) == sorted([MODEL, READER])


def test_python_files_reads_nothing_from_a_tree_that_is_not_there(tmp_path: Path) -> None:
    assert not python_files(_fields_repo(tmp_path), (Path("nowhere"),))


def test_dataclass_fields_finds_every_field_of_every_dataclass(tmp_path: Path) -> None:
    assert dataclass_fields(_model_lines(tmp_path)) == [
        (6, "Places", "peers"),
        (7, "Places", "paths"),
        (8, "Places", "miles"),
        (13, "Fiber", "miles"),
    ]


def test_attribute_reads_resolves_a_base_through_its_annotation(tmp_path: Path) -> None:
    assert ("Places", "peers") in _reader_reads(tmp_path)


def test_attribute_reads_leaves_a_base_it_cannot_resolve_unresolved(tmp_path: Path) -> None:
    assert (None, "count") in _reader_reads(tmp_path)


def test_attribute_reads_counts_a_name_used_on_its_own(tmp_path: Path) -> None:
    assert (None, "int") in _reader_reads(tmp_path)


def test_attribute_reads_counts_a_string_the_code_holds(tmp_path: Path) -> None:
    assert (None, "fiber") in _reader_reads(tmp_path)


def test_unread_fields_reports_a_field_only_another_class_reads(tmp_path: Path) -> None:
    assert unread_fields(_fields_repo(tmp_path)) == [(MODEL, 8, "Places.miles")]


def test_unread_fields_counts_a_read_made_under_the_test_tree(tmp_path: Path) -> None:
    assert (MODEL, 7, "Places.paths") not in unread_fields(_fields_repo(tmp_path))


def test_main_answers_zero_when_every_field_is_read(tmp_path: Path) -> None:
    _write(tmp_path, MODEL, "from dataclasses import dataclass\n")
    assert main(["--root", str(tmp_path)]) == 0


def test_main_answers_one_when_a_field_is_written_and_never_read(tmp_path: Path) -> None:
    assert main(["--root", str(_fields_repo(tmp_path))]) == 1


def test_main_prints_an_annotation_naming_the_unread_field(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["--root", str(_fields_repo(tmp_path))])
    assert f"::error file={MODEL},line=8::" in capsys.readouterr().out
