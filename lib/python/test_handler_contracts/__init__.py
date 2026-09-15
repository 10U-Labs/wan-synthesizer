from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from repo_utils import REPO_ROOT
from test_module_utils import create_lambda_loader
from test_s3_store_mock import fake_lambda, fake_s3

SPA_ORIGIN = "https://www.10ulabs.com"


def load_handler(endpoint: str, monkeypatch: pytest.MonkeyPatch, **env: str) -> Any:
    monkeypatch.setenv("STORE_BUCKET", "test-bucket")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    lambdas = REPO_ROOT / "src" / "api" / "endpoints" / endpoint / "lambdas"
    name = endpoint.replace("/", "_")
    module: Any = create_lambda_loader(lambdas)("handler.py", f"{name}_handler")
    module.clear_clients()
    return module


def write_clients(objects: dict[str, bytes], invocations: list[dict[str, Any]]) -> Any:
    fakes = {"s3": fake_s3(objects), "lambda": fake_lambda(invocations)}
    return lambda service, **_kwargs: fakes[service]


class RegionsContract:
    CFG: dict[str, Any]

    def _handler(self, monkeypatch: pytest.MonkeyPatch) -> Any:
        return load_handler(self.CFG["endpoint"], monkeypatch)

    def _collection(self) -> str:
        return str(self.CFG["key"]).rsplit("/", 1)[-1].removesuffix(".json")

    def _status_of(self, monkeypatch: pytest.MonkeyPatch, event: dict[str, Any]) -> int:
        module = self._handler(monkeypatch)
        with patch("boto3.client", side_effect=write_clients({}, [])):
            response = module.lambda_handler(event, None)
        return int(response["statusCode"])

    def test_delete_removes_the_object(self, monkeypatch: pytest.MonkeyPatch) -> None:
        module = self._handler(monkeypatch)
        objects = {self.CFG["key"]: b"{}"}
        with patch("boto3.client", side_effect=write_clients(objects, [])):
            module.lambda_handler(self._delete_event(), None)
        assert self.CFG["key"] not in objects

    def test_delete_leaves_no_delete_marker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        module = self._handler(monkeypatch)
        fake = fake_s3({self.CFG["key"]: b"{}"})
        with patch("boto3.client", return_value=fake):
            module.lambda_handler(self._delete_event(), None)
        assert fake.list_object_versions(Bucket="test-bucket")["DeleteMarkers"] == []

    def test_write_404(self, monkeypatch: pytest.MonkeyPatch) -> None:
        refused = {"httpMethod": "PUT", "path": self._path(self._collection()), "body": "[]"}
        assert self._status_of(monkeypatch, refused) == 404

    def _path(self, collection: str) -> str:
        return f"/x/{self.CFG['endpoint']}/{collection}"

    def _delete_event(self) -> dict[str, Any]:
        return {"httpMethod": "DELETE", "path": self._path(self._collection())}

    def test_a_get_answers_404(self, monkeypatch: pytest.MonkeyPatch) -> None:
        module = self._handler(monkeypatch)
        stored = {self.CFG["key"]: json.dumps(self.CFG["valid"]).encode()}
        with patch("boto3.client", return_value=fake_s3(stored)):
            response = module.lambda_handler({"path": self._path(self._collection())}, None)
        assert response["statusCode"] == 404

    def test_caches_the_s3_client(self, monkeypatch: pytest.MonkeyPatch) -> None:
        module = self._handler(monkeypatch)
        with patch("boto3.client", return_value=fake_s3({})) as mock_client:
            module.lambda_handler({}, None)
            module.lambda_handler({}, None)
        assert mock_client.call_count == 1

    def test_delete_404_for_unknown_collection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        unknown = {"httpMethod": "DELETE", "path": self._path("bogus")}
        assert self._status_of(monkeypatch, unknown) == 404
