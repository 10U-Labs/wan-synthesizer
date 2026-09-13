from __future__ import annotations

from typing import Any

import pytest

from repo_utils import REPO_ROOT
from test_module_utils import create_lambda_loader
from test_terraform_config import find_resource, load_tf

STORAGE_DIR = REPO_ROOT / "src" / "api" / "common" / "storage"



@pytest.fixture(name="storage_main")
def storage_main_fixture() -> dict[str, object]:
    return load_tf(STORAGE_DIR / "main.tf")


@pytest.fixture
def storage_iam() -> dict[str, object]:
    return load_tf(STORAGE_DIR / "iam.tf")


@pytest.fixture
def prune_handler(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setenv("STORE_BUCKET", "test-bucket")
    module: Any = create_lambda_loader(STORAGE_DIR / "lambdas")(
        "handler.py", "storage_prune_handler"
    )
    module.clear_clients()
    return module


@pytest.fixture
def store_bucket_name(storage_main: dict[str, object]) -> str:
    bucket = find_resource(storage_main, "aws_s3_bucket", "store")
    if bucket is None:
        raise AssertionError("aws_s3_bucket.store is not declared in main.tf")
    return str(bucket["bucket"])
