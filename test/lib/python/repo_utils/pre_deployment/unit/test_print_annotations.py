from __future__ import annotations

import pytest

from repo_utils import print_annotations


def test_nothing_reported_answers_zero() -> None:
    assert print_annotations([]) == 0


def test_nothing_reported_prints_nothing(capsys: pytest.CaptureFixture[str]) -> None:
    print_annotations([])
    assert capsys.readouterr().out == ""


def test_something_reported_answers_one() -> None:
    assert print_annotations(["::error file=a.py::a.py is wrong"]) == 1


def test_every_line_reported_is_printed(capsys: pytest.CaptureFixture[str]) -> None:
    print_annotations(["first", "second"])
    assert capsys.readouterr().out == "first\nsecond\n"
