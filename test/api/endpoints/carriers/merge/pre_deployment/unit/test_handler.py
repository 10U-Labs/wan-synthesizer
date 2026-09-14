from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from test_handler_contracts import SPA_ORIGIN, load_handler
from test_s3_store_mock import fake_s3


def test_merge_get_serves_fiber_segments(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_handler("carriers/merge", monkeypatch)
    stored = {"carriers/merge/fiber-segments.json": json.dumps([{"id": "S"}]).encode()}
    with patch("boto3.client", return_value=fake_s3(stored)):
        response = module.lambda_handler({"path": "/x/carriers/merge/fiber-segments"}, None)
    assert json.loads(response["body"]) == [{"id": "S"}]


def test_merge_get_404_for_an_unknown_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_handler("carriers/merge", monkeypatch)
    with patch("boto3.client", return_value=fake_s3({})):
        response = module.lambda_handler({"path": "/x/carriers/merge/bogus"}, None)
    assert response["statusCode"] == 404


def test_merge_get_404_when_not_built(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_handler("carriers/merge", monkeypatch)
    with patch("boto3.client", return_value=fake_s3({})):
        response = module.lambda_handler({"path": "/x/carriers/merge/fiber-segments"}, None)
    assert response["statusCode"] == 404


def test_merge_answers_the_spas_origin_and_no_other(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_handler("carriers/merge", monkeypatch)
    stored = {"carriers/merge/fiber-segments.json": b"[]"}
    with patch("boto3.client", return_value=fake_s3(stored)):
        response = module.lambda_handler({"path": "/x/carriers/merge/fiber-segments"}, None)
    assert response["headers"]["Access-Control-Allow-Origin"] == SPA_ORIGIN
