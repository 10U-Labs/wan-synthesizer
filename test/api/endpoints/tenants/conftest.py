from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from repo_utils import REPO_ROOT
from test_terraform_config import lambda_handler_names, load_tf

TENANTS_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "tenants"


@pytest.fixture
def tenants_dir() -> Path:
    return TENANTS_DIR


@pytest.fixture(name="tenants_main")
def tenants_main_fixture() -> dict[str, object]:
    return load_tf(TENANTS_DIR / "main.tf")


@pytest.fixture
def tenants_iam() -> dict[str, object]:
    return load_tf(TENANTS_DIR / "iam.tf")


@pytest.fixture(name="tenants_locals")
def tenants_locals_fixture(tenants_main: dict[str, object]) -> dict[str, Any]:
    blocks = tenants_main.get("locals", [])
    return blocks[0] if isinstance(blocks, list) and blocks else {}


@pytest.fixture
def function_name() -> str:
    return lambda_handler_names()["tenants"]


@pytest.fixture
def role_name(tenants_locals: dict[str, Any]) -> str:
    return str(tenants_locals["role_name"])
