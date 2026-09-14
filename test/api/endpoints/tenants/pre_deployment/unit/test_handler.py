from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from test_handler_contracts import ReaderContract, load_handler, write_clients
from test_s3_store_mock import fake_s3

_READER: dict[str, Any] = {
    "endpoint": "tenants",
    "stored_key": "tenants/f-35/degree-exempt-wan-pops.json",
    "stored": ["Nellis, NV"],
    "serve_event": {
        "pathParameters": {"tenant": "f-35"},
        "path": "/x/tenants/f-35/degree-exempt-wan-pops",
    },
    "serve_expect": ["Nellis, NV"],
    "unknown_event": {
        "pathParameters": {"tenant": "f-35"},
        "path": "/x/tenants/f-35/bogus",
    },
    "notbuilt_event": {
        "pathParameters": {"tenant": "minuteman"},
        "path": "/x/tenants/minuteman/degree-exempt-wan-pops",
    },
}


class TestTenantsReader(ReaderContract):
    CFG = _READER


def _tenant(monkeypatch: pytest.MonkeyPatch) -> Any:
    return load_handler("tenants", monkeypatch)


def test_a_get_without_a_tenant_answers_404(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    with patch("boto3.client", return_value=fake_s3({})):
        response = module.lambda_handler({"httpMethod": "GET"}, None)
    assert response["statusCode"] == 404


def test_tenant_serves_the_backbone_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    circuits = [{"source_name": "Minot, ND", "target_name": "Kansas City, MO"}]
    objects = {
        "tenants/f-35/wan.json": json.dumps({"backbone-circuits": circuits}).encode()
    }
    event = {
        "pathParameters": {"tenant": "f-35"},
        "path": "/x/tenants/f-35/backbone-circuits",
    }
    with patch("boto3.client", return_value=fake_s3(objects)):
        response = module.lambda_handler(event, None)
    assert json.loads(response["body"]) == circuits


def test_tenant_get_serves_an_input_document(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    stored = {"tenants/f-35/degree-exempt-wan-pops.json": json.dumps(["Luke, AZ"]).encode()}
    event = {"pathParameters": {"tenant": "f-35"}, "path": "/x/tenants/f-35/degree-exempt-wan-pops"}
    with patch("boto3.client", side_effect=write_clients(stored, [])):
        response = module.lambda_handler(event, None)
    assert json.loads(response["body"]) == ["Luke, AZ"]


def test_tenant_delete_removes_every_object(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    objects = {"tenants/f-35/config.json": b"{}", "tenants/f-35/wan.json": b"{}"}
    event = {"httpMethod": "DELETE", "pathParameters": {"tenant": "f-35"}}
    with patch("boto3.client", side_effect=write_clients(objects, [])):
        module.lambda_handler(event, None)
    assert not objects


def test_tenant_delete_leaves_no_delete_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    fake = fake_s3(
        {"tenants/f-35/degree-exempt-wan-pops.json": b"[]", "tenants/f-35/wan.json": b"{}"})
    event = {"httpMethod": "DELETE", "pathParameters": {"tenant": "f-35"}}
    with patch("boto3.client", return_value=fake):
        module.lambda_handler(event, None)
    assert fake.list_object_versions(Bucket="test-bucket")["DeleteMarkers"] == []


def test_tenant_delete_with_no_objects_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    event = {"httpMethod": "DELETE", "pathParameters": {"tenant": "ghost"}}
    with patch("boto3.client", side_effect=write_clients({}, [])):
        response = module.lambda_handler(event, None)
    assert response["statusCode"] == 200


def test_tenant_write_404_when_no_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    with patch("boto3.client", side_effect=write_clients({}, [])):
        response = module.lambda_handler({"httpMethod": "PUT"}, None)
    assert response["statusCode"] == 404
