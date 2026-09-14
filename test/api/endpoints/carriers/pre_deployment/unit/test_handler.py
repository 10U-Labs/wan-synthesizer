from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from test_handler_contracts import SPA_ORIGIN, load_handler, write_clients
from test_s3_store_mock import fake_s3


def _carriers(monkeypatch: pytest.MonkeyPatch) -> Any:
    return load_handler("carriers", monkeypatch)


def test_a_get_answers_404(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _carriers(monkeypatch)
    event = {"pathParameters": {"carrier": "lumen"}, "path": "/x/carriers/lumen/fiber-segments"}
    stored = {"carriers/lumen/fiber-segments.json": b"[]"}
    with patch("boto3.client", return_value=fake_s3(stored)):
        response = module.lambda_handler(event, None)
    assert response["statusCode"] == 404


def test_caches_the_s3_client(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _carriers(monkeypatch)
    with patch("boto3.client", return_value=fake_s3({}, keys=[])) as mock_client:
        module.lambda_handler({}, None)
        module.lambda_handler({}, None)
    assert mock_client.call_count == 1


def test_answers_the_spas_origin_and_no_other(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _carriers(monkeypatch)
    with patch("boto3.client", return_value=fake_s3({}, keys=[])):
        response = module.lambda_handler({}, None)
    assert response["headers"]["Access-Control-Allow-Origin"] == SPA_ORIGIN


def _store_after_deleting(
        monkeypatch: pytest.MonkeyPatch, stored: dict[str, bytes], carrier: str
) -> dict[str, bytes]:
    module = _carriers(monkeypatch)
    event = {"httpMethod": "DELETE", "pathParameters": {"carrier": carrier}}
    with patch("boto3.client", side_effect=write_clients(stored, [])):
        module.lambda_handler(event, None)
    return stored


def test_carrier_delete_removes_an_object_the_endpoint_never_wrote(
        monkeypatch: pytest.MonkeyPatch) -> None:
    stored = {"carriers/lumen/fiber-segments.json": b"[]", "carriers/lumen/vertices.json": b"[]"}
    assert not _store_after_deleting(monkeypatch, stored, "lumen")


def test_carrier_delete_leaves_another_carrier_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    stored = {
        "carriers/lumen/fiber-segments.json": b"[]", "carriers/zayo/fiber-segments.json": b"[]"}
    kept = list(_store_after_deleting(monkeypatch, stored, "lumen"))
    assert kept == ["carriers/zayo/fiber-segments.json"]


def test_carrier_delete_leaves_no_delete_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _carriers(monkeypatch)
    fake = fake_s3({"carriers/lumen/fiber-segments.json": b"[]"})
    event = {"httpMethod": "DELETE", "pathParameters": {"carrier": "lumen"}}
    with patch("boto3.client", return_value=fake):
        module.lambda_handler(event, None)
    assert fake.list_object_versions(Bucket="test-bucket")["DeleteMarkers"] == []


def test_carrier_delete_404_when_no_carrier(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _carriers(monkeypatch)
    with patch("boto3.client", side_effect=write_clients({}, [])):
        response = module.lambda_handler({"httpMethod": "DELETE"}, None)
    assert response["statusCode"] == 404


def test_carrier_put_404(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _carriers(monkeypatch)
    event = {"httpMethod": "PUT", "pathParameters": {"carrier": "lumen"}, "body": "[]"}
    with patch("boto3.client", side_effect=write_clients({}, [])):
        response = module.lambda_handler(event, None)
    assert response["statusCode"] == 404
