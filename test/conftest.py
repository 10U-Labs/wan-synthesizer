from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from loader import API_KEY_VARIABLE
from stub_api import KEY

REPO_ROOT = Path(__file__).resolve().parent.parent
LIB_PYTHON_DIR = REPO_ROOT / "lib" / "python"
SRC_DIR = REPO_ROOT / "src"
TEST_DIR = REPO_ROOT / "test"

for candidate in (REPO_ROOT, LIB_PYTHON_DIR, SRC_DIR, TEST_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


@pytest.fixture
def the_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(API_KEY_VARIABLE, KEY)


@pytest.fixture(name="pauses")
def pauses_fixture() -> list[float]:
    return []


@pytest.fixture
def sleep(pauses: list[float]) -> Callable[[float], None]:
    return pauses.append
