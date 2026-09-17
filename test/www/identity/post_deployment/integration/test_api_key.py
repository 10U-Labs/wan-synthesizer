from __future__ import annotations

from typing import Any, cast

import boto3
import pytest

REGION = "us-east-2"
ROLE_NAME = "TenULabsWanSynthesizerRole"
API_KEY_PARAMETER = "/api.10ulabs.com/api-key"
API_KEY_LENGTH = 48


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture() -> dict[str, Any]:
    client = cast(Any, boto3).client("ssm", region_name=REGION)
    parameter = client.get_parameter(Name=API_KEY_PARAMETER, WithDecryption=True)["Parameter"]
    described = {key: value for key, value in parameter.items() if key != "Value"}
    described["Length"] = len(parameter["Value"])
    return described


@pytest.fixture(name="live_policy_names", scope="module")
def live_policy_names_fixture() -> list[str]:
    client = cast(Any, boto3).client("iam", region_name=REGION)
    names: list[str] = client.list_role_policies(RoleName=ROLE_NAME)["PolicyNames"]
    return sorted(names)


def test_the_role_reads_the_api_key(api_key: dict[str, Any]) -> None:
    assert api_key["Name"] == API_KEY_PARAMETER


def test_the_key_read_is_the_secure_string_the_api_writes(api_key: dict[str, Any]) -> None:
    assert api_key["Type"] == "SecureString"


def test_the_key_read_is_decrypted(api_key: dict[str, Any]) -> None:
    assert api_key["Length"] == API_KEY_LENGTH


def test_the_live_role_holds_the_api_policy_beside_the_other_three(
        live_policy_names: list[str]) -> None:
    assert live_policy_names == ["Api", "Self", "Site", "State"]
