from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from repo_utils import REPO_ROOT
from test_module_utils import create_lambda_loader
from test_terraform_config import api_key_parameter_name, find_resource, load_tf

ROUTING_DIR = REPO_ROOT / "src" / "api" / "common" / "routing"
GOOGLE_CLIENT_ID = "client.apps.googleusercontent.com"
HOSTED_DOMAIN = "10ulabs.com"
API_KEY_PARAMETER = "/wan-synthesizer/api-key"
AUTHORIZED_ACCOUNTS_PARAMETER = "/wan-synthesizer/authorized-accounts"


@pytest.fixture(name="routing_dir")
def routing_dir_fixture() -> Path:
    return ROUTING_DIR


@pytest.fixture(name="routing_main")
def routing_main_fixture() -> dict[str, object]:
    return load_tf(ROUTING_DIR / "main.tf")


@pytest.fixture(name="routing_authorizer")
def routing_authorizer_fixture() -> dict[str, object]:
    return load_tf(ROUTING_DIR / "authorizer.tf")


@pytest.fixture(name="routing_iam")
def routing_iam_fixture() -> dict[str, object]:
    return load_tf(ROUTING_DIR / "iam.tf")


@pytest.fixture(name="authorizer")
def authorizer_fixture(monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", GOOGLE_CLIENT_ID)
    monkeypatch.setenv("HOSTED_DOMAIN", HOSTED_DOMAIN)
    monkeypatch.setenv("API_KEY_PARAMETER", API_KEY_PARAMETER)
    monkeypatch.setenv("AUTHORIZED_ACCOUNTS_PARAMETER", AUTHORIZED_ACCOUNTS_PARAMETER)
    return create_lambda_loader(ROUTING_DIR / "lambdas")("authorizer.py", "routing_authorizer")


@pytest.fixture(name="api_key_parameter_name")
def api_key_parameter_name_fixture() -> str:
    return api_key_parameter_name()


@pytest.fixture(name="authorized_accounts_parameter_name")
def authorized_accounts_parameter_name_fixture(routing_authorizer: dict[str, object]) -> str:
    parameter = find_resource(routing_authorizer, "aws_ssm_parameter", "authorized_accounts")
    if parameter is None:
        raise AssertionError("aws_ssm_parameter.authorized_accounts is not declared")
    return str(parameter["name"])
