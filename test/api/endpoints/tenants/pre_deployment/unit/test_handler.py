from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from test_handler_contracts import SPA_ORIGIN, load_handler, write_clients
from test_s3_store_mock import fake_s3


def _tenant(monkeypatch: pytest.MonkeyPatch) -> Any:
    return load_handler("tenants", monkeypatch)


def test_a_get_without_a_tenant_answers_404(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    with patch("boto3.client", return_value=fake_s3({})):
        response = module.lambda_handler({"httpMethod": "GET"}, None)
    assert response["statusCode"] == 404


def test_a_get_of_a_tenant_answers_404(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    event = {"pathParameters": {"tenant": "f-35"}, "path": "/x/tenants/f-35/label"}
    with patch("boto3.client", return_value=fake_s3({})):
        response = module.lambda_handler(event, None)
    assert response["statusCode"] == 404


def test_caches_the_s3_client(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    with patch("boto3.client", return_value=fake_s3({}, keys=[])) as mock_client:
        module.lambda_handler({}, None)
        module.lambda_handler({}, None)
    assert mock_client.call_count == 1


def test_answers_the_spas_origin_and_no_other(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _tenant(monkeypatch)
    with patch("boto3.client", return_value=fake_s3({}, keys=[])):
        response = module.lambda_handler({}, None)
    assert response["headers"]["Access-Control-Allow-Origin"] == SPA_ORIGIN


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
        {"tenants/f-35/label.json": b"[]", "tenants/f-35/wan.json": b"{}"})
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
