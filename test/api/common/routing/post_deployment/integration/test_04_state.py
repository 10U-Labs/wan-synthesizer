from __future__ import annotations

import json
import subprocess
from typing import Any

from repo_utils import REPO_ROOT

ROUTING_DIR = REPO_ROOT / "src" / "api" / "common" / "routing"


def _state() -> str:
    return subprocess.run(
        ["tofu", "state", "pull"],
        capture_output=True,
        text=True,
        cwd=ROUTING_DIR,
        timeout=120,
        check=True,
    ).stdout


def _recorded(resource_type: str, name: str) -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = json.loads(_state())["resources"]
    return [
        resource for resource in resources
        if resource["type"] == resource_type and resource["name"] == name
    ]


def test_the_key_the_authorizer_admits_is_written_nowhere_in_the_state(api_key: str) -> None:
    assert api_key not in _state()


def test_the_state_records_the_api_key_parameter_without_its_value() -> None:
    assert not _recorded("aws_ssm_parameter", "api_key")[0]["instances"][0]["attributes"]["value"]


def test_the_state_records_no_password_for_the_api_key() -> None:
    assert _recorded("random_password", "api_key") == []
