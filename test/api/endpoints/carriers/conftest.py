from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from repo_utils import REPO_ROOT
from test_terraform_config import lambda_handler_names, load_tf

CARRIERS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "carriers"


@pytest.fixture
def carriers_dir() -> Path:
    return CARRIERS_DIR


@pytest.fixture(name="carriers_main")
def carriers_main_fixture() -> dict[str, object]:
    return load_tf(CARRIERS_DIR / "main.tf")


@pytest.fixture
def carriers_iam() -> dict[str, object]:
    return load_tf(CARRIERS_DIR / "iam.tf")


@pytest.fixture(name="carriers_locals")
def carriers_locals_fixture(carriers_main: dict[str, object]) -> dict[str, Any]:
    blocks = carriers_main.get("locals", [])
    return blocks[0] if isinstance(blocks, list) and blocks else {}


@pytest.fixture
def function_name() -> str:
    return lambda_handler_names()["carriers"]


@pytest.fixture
def role_name(carriers_locals: dict[str, Any]) -> str:
    return str(carriers_locals["role_name"])
