from __future__ import annotations

from typing import Any

import pytest

import test_terraform_config
from test_terraform_config import api_key_parameter_name


def _routing_declares(monkeypatch: pytest.MonkeyPatch, parameters: dict[str, Any]) -> None:
    document = {"resource": [{"aws_ssm_parameter": parameters}]}
    monkeypatch.setattr(test_terraform_config, "load_tf", lambda _path: document)


def test_the_declared_parameter_name_is_returned(monkeypatch: pytest.MonkeyPatch) -> None:
    _routing_declares(monkeypatch, {"api_key": {"name": "/a/key"}})
    assert api_key_parameter_name() == "/a/key"


def test_a_routing_stack_without_the_parameter_is_an_error(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _routing_declares(monkeypatch, {"other": {"name": "/a/key"}})
    with pytest.raises(AssertionError):
        api_key_parameter_name()


def test_the_real_routing_stack_declares_the_key_under_the_product_name() -> None:
    assert api_key_parameter_name().startswith("/wan-synthesizer/")
