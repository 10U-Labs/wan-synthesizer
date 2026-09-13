from __future__ import annotations


import pytest

from repo_utils import REPO_ROOT
from test_terraform_config import find_resource, lambda_handler_names, load_tf

WAN_DIR = REPO_ROOT / "src" / "api" / "endpoints" / "tenants" / "wan"



@pytest.fixture
def wan_lambda() -> dict[str, object]:
    return load_tf(WAN_DIR / "lambda.tf")


@pytest.fixture(name="wan_iam")
def wan_iam_fixture() -> dict[str, object]:
    return load_tf(WAN_DIR / "iam_lambda.tf")


@pytest.fixture
def function_name() -> str:
    return lambda_handler_names()["wan"]


@pytest.fixture
def role_name(wan_iam: dict[str, object]) -> str:
    role = find_resource(wan_iam, "aws_iam_role", "lambda")
    if role is None:
        raise AssertionError("aws_iam_role.lambda is not declared")
    return str(role["name"])
