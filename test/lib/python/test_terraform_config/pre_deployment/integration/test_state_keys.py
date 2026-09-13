from __future__ import annotations

from repo_utils import REPO_ROOT
from test_terraform_config import STATE_KEY_LINE, STATE_KEY_PREFIX, declared_state_keys

SRC = REPO_ROOT / "src"


def _read_keys() -> set[str]:
    return {
        match.group(1)
        for path in sorted(SRC.rglob("*.tf"))
        if path.name != "backend.tf"
        for match in STATE_KEY_LINE.finditer(path.read_text(encoding="utf-8"))
    }


def test_every_stack_files_its_state_under_its_own_path() -> None:
    expected = {
        stack: f"{STATE_KEY_PREFIX}{stack}/terraform.tfstate" for stack in declared_state_keys()
    }
    assert declared_state_keys() == expected


def test_every_remote_state_read_names_the_repository_prefix() -> None:
    assert {key for key in _read_keys() if not key.startswith(STATE_KEY_PREFIX)} == set()


def test_every_remote_state_read_names_a_key_some_stack_writes() -> None:
    assert _read_keys() - set(declared_state_keys().values()) == set()
