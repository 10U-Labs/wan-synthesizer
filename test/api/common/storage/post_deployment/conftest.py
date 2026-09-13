from __future__ import annotations

from typing import Any, cast

import pytest

from test_terraform_config import lambda_handler_names


@pytest.fixture(name="live_lifecycle_rules")
def live_lifecycle_rules_fixture(
        s3_client: Any, store_bucket_name: str) -> dict[str, Any]:
    response = s3_client.get_bucket_lifecycle_configuration(Bucket=store_bucket_name)
    rules: list[dict[str, Any]] = response["Rules"]
    return {rule["ID"]: rule for rule in rules}


@pytest.fixture(name="prune_config")
def prune_config_fixture(lambda_client: Any) -> dict[str, Any]:
    response = lambda_client.get_function(FunctionName=lambda_handler_names()["prune"])
    return cast("dict[str, Any]", response["Configuration"])
