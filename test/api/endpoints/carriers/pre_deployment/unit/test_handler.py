from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from test_handler_contracts import ReaderContract, load_handler, write_clients
from test_s3_store_mock import fake_s3

_READER: dict[str, Any] = {
    "endpoint": "carriers",
    "stored_key": "carriers/lumen/pops.json",
    "stored": [{"id": "P"}],
    "serve_event": {
        "pathParameters": {"carrier": "lumen"},
        "path": "/x/carriers/lumen/pops",
    },
    "serve_expect": [{"id": "P"}],
    "unknown_event": {
        "pathParameters": {"carrier": "lumen"},
        "path": "/x/carriers/lumen/bogus",
    },
    "notbuilt_event": {
        "pathParameters": {"carrier": "zayo"},
        "path": "/x/carriers/zayo/fiber-segments",
    },
}


class TestCarriersReader(ReaderContract):
    CFG = _READER


def _store_after_deleting(
        monkeypatch: pytest.MonkeyPatch, stored: dict[str, bytes], carrier: str
) -> dict[str, bytes]:
    module = load_handler("carriers", monkeypatch)
    event = {"httpMethod": "DELETE", "pathParameters": {"carrier": carrier}}
    with patch("boto3.client", side_effect=write_clients(stored, [])):
        module.lambda_handler(event, None)
    return stored


def test_carrier_delete_removes_an_object_the_endpoint_never_wrote(
        monkeypatch: pytest.MonkeyPatch) -> None:
    stored = {"carriers/lumen/pops.json": b"[]", "carriers/lumen/vertices.json": b"[]"}
    assert not _store_after_deleting(monkeypatch, stored, "lumen")


def test_carrier_delete_leaves_another_carrier_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    stored = {"carriers/lumen/pops.json": b"[]", "carriers/zayo/pops.json": b"[]"}
    kept = list(_store_after_deleting(monkeypatch, stored, "lumen"))
    assert kept == ["carriers/zayo/pops.json"]


def test_carrier_delete_leaves_no_delete_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_handler("carriers", monkeypatch)
    fake = fake_s3({"carriers/lumen/pops.json": b"[]"})
    event = {"httpMethod": "DELETE", "pathParameters": {"carrier": "lumen"}}
    with patch("boto3.client", return_value=fake):
        module.lambda_handler(event, None)
    assert fake.list_object_versions(Bucket="test-bucket")["DeleteMarkers"] == []


def test_carrier_delete_404_when_no_carrier(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_handler("carriers", monkeypatch)
    with patch("boto3.client", side_effect=write_clients({}, [])):
        response = module.lambda_handler({"httpMethod": "DELETE"}, None)
    assert response["statusCode"] == 404


def test_carrier_put_404(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_handler("carriers", monkeypatch)
    event = {"httpMethod": "PUT", "pathParameters": {"carrier": "lumen"}, "body": "[]"}
    with patch("boto3.client", side_effect=write_clients({}, [])):
        response = module.lambda_handler(event, None)
    assert response["statusCode"] == 404
