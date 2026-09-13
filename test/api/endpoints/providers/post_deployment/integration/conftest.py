from __future__ import annotations

from typing import Any, cast

import pytest


@pytest.fixture
def lambda_config(lambda_client: Any, function_name: str) -> dict[str, Any]:
    response = lambda_client.get_function(FunctionName=function_name)
    return cast("dict[str, Any]", response["Configuration"])
