from __future__ import annotations

from pathlib import Path

import pytest

from throwaway_repository import commit, git, write


@pytest.fixture(name="repository")
def repository_fixture(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    return tmp_path


def test_git_answers_what_the_command_prints_less_its_newline(repository: Path) -> None:
    assert git(repository, "rev-parse", "--is-inside-work-tree") == "true"


def test_write_puts_the_text_at_the_path_under_the_repository(repository: Path) -> None:
    write(repository, "notes.txt", "kept\n")
    assert (repository / "notes.txt").read_text(encoding="utf-8") == "kept\n"


def test_write_makes_the_directories_the_path_needs(repository: Path) -> None:
    write(repository, "data/pops/alpha.csv", "A\n")
    assert (repository / "data" / "pops" / "alpha.csv").is_file()


def test_a_commit_answers_the_hash_it_made(repository: Path) -> None:
    write(repository, "notes.txt", "kept\n")
    made = commit(repository, "first")
    assert made == git(repository, "rev-parse", "HEAD")


def test_a_commit_takes_every_file_in_the_tree(repository: Path) -> None:
    write(repository, "a.txt", "a\n")
    write(repository, "b/c.txt", "c\n")
    commit(repository, "first")
    assert git(repository, "ls-files").split() == ["a.txt", "b/c.txt"]


def test_a_commit_takes_a_file_removed_since_the_last(repository: Path) -> None:
    write(repository, "a.txt", "a\n")
    write(repository, "b.txt", "b\n")
    commit(repository, "first")
    (repository / "a.txt").unlink()
    commit(repository, "second")
    assert git(repository, "ls-files").split() == ["b.txt"]


def test_a_commit_carries_its_message(repository: Path) -> None:
    write(repository, "a.txt", "a\n")
    commit(repository, "the message")
    assert git(repository, "log", "-1", "--format=%s") == "the message"
