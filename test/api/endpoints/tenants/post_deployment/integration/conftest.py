from __future__ import annotations

from typing import Any, cast

import pytest

from test_terraform_config import api_key_parameter_name


@pytest.fixture(name="api_key")
def api_key_fixture(ssm_client: Any) -> str:
    response = ssm_client.get_parameter(Name=api_key_parameter_name(), WithDecryption=True)
    return str(response["Parameter"]["Value"])


@pytest.fixture(name="lambda_config")
def lambda_config_fixture(lambda_client: Any, function_name: str) -> dict[str, Any]:
    response = lambda_client.get_function(FunctionName=function_name)
    return cast("dict[str, Any]", response["Configuration"])
