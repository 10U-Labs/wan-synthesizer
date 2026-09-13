from __future__ import annotations

from pathlib import Path

from test_terraform_config import STACKS_DIR, STATE_KEY_PREFIX, declared_state_keys


def _stack(stacks: Path, name: str, backend: str) -> None:
    (stacks / name).mkdir(parents=True)
    (stacks / name / "backend.tf").write_text(backend, encoding="utf-8")


def test_each_backend_is_read_under_its_stack_path(tmp_path: Path) -> None:
    _stack(tmp_path, "common/one", 'terraform {\n  backend "s3" {\n    key = "a/one"\n  }\n}\n')
    _stack(tmp_path, "endpoints/two", '  key = "a/two"\n')
    assert declared_state_keys(tmp_path) == {"common/one": "a/one", "endpoints/two": "a/two"}


def test_a_backend_without_a_key_is_not_a_stack(tmp_path: Path) -> None:
    _stack(tmp_path, "keyless", 'terraform {\n  backend "s3" {\n    bucket = "b"\n  }\n}\n')
    assert not declared_state_keys(tmp_path)


def test_a_tree_without_a_backend_declares_nothing(tmp_path: Path) -> None:
    assert not declared_state_keys(tmp_path)


def test_the_real_tree_files_every_stack_under_the_repository_prefix() -> None:
    assert [
        key for key in declared_state_keys(STACKS_DIR).values()
        if not key.startswith(STATE_KEY_PREFIX)
    ] == []
