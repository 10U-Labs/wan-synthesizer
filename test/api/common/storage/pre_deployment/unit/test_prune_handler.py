from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from test_s3_store_mock import fake_s3

_CURRENT = [
    "carriers/lumen/pops.json",
    "carriers/lumen/fiber-segments.json",
    "carriers/merge/pops.json",
    "carriers/merge/fiber-segments.json",
    "providers/regions.json",
    "tenants/daf/locations.json",
    "tenants/daf/wan.json",
    "tenants/daf/wan-status.json",
]
_STALE = [
    "source/carriers/lumen.csv",
    "builds/daf/2026-08-20/graph.json",
    "carriers/lumen/vertices.json",
    "carriers/lumen/edges.json",
    "carriers/merge/edges.json",
    "providers/vertices.json",
    "tenants/daf/csp-regions.json",
    "tenants/daf/forced-connections.json",
    "csps/aws/vertices.json",
    "data-centers/equinix/facilities.json",
]


def _store() -> dict[str, bytes]:
    return {key: b"[]" for key in _CURRENT + _STALE}


def _prune(handler: Any, objects: dict[str, bytes]) -> Any:
    with patch("boto3.client", return_value=fake_s3(objects)):
        response = handler.lambda_handler({"httpMethod": "POST"}, None)
    return json.loads(response["body"])


_WRITTEN_THIS_RUN = "tenants/daf/forced-connections.json"


def _prune_after_writing(handler: Any, objects: dict[str, bytes]) -> Any:
    event = {"httpMethod": "POST", "body": json.dumps({"written": [_WRITTEN_THIS_RUN]})}
    with patch("boto3.client", return_value=fake_s3(objects)):
        response = handler.lambda_handler(event, None)
    return json.loads(response["body"])


def test_the_prune_keeps_a_key_its_caller_wrote_this_run(prune_handler: Any) -> None:
    objects = _store()
    _prune_after_writing(prune_handler, objects)
    assert _WRITTEN_THIS_RUN in objects


def test_the_prune_still_takes_out_what_its_caller_did_not_write(prune_handler: Any) -> None:
    assert _prune_after_writing(prune_handler, _store())["deleted"] == sorted(
        key for key in _STALE if key != _WRITTEN_THIS_RUN
    )


def test_a_prune_sent_no_body_keeps_only_what_the_lambda_lists(prune_handler: Any) -> None:
    assert _prune(prune_handler, {_WRITTEN_THIS_RUN: b"[]"})["deleted"] == [_WRITTEN_THIS_RUN]


def test_the_prune_deletes_every_stale_object(prune_handler: Any) -> None:
    assert _prune(prune_handler, _store())["deleted"] == sorted(_STALE)


def test_the_prune_leaves_every_current_object_where_it_is(prune_handler: Any) -> None:
    objects = _store()
    _prune(prune_handler, objects)
    assert sorted(objects) == sorted(_CURRENT)


@pytest.mark.parametrize("key", [
    "source/carriers/lumen.csv",
    "builds/daf/2026-08-20/graph.json",
    "csps/aws/vertices.json",
    "data-centers/qts/facilities.json",
])
def test_the_prune_takes_out_a_prefix_the_product_does_not_write(
        prune_handler: Any, key: str) -> None:
    assert _prune(prune_handler, {key: b""})["deleted"] == [key]


def test_the_prune_takes_out_a_bare_prefix_marker(prune_handler: Any) -> None:
    assert _prune(prune_handler, {"carriers/": b""})["deleted"] == ["carriers/"]


def test_a_second_prune_finds_nothing_left_to_do(prune_handler: Any) -> None:
    objects = _store()
    _prune(prune_handler, objects)
    assert _prune(prune_handler, objects)["deleted"] == []


def test_the_prune_reads_every_page_of_the_listing(prune_handler: Any) -> None:
    pages = [
        {"Versions": [{"Key": "csps/aws/vertices.json", "VersionId": "null", "IsLatest": True}]},
        {"Versions": [{"Key": "csps/azure/vertices.json", "VersionId": "null", "IsLatest": True}]},
    ]
    fake = fake_s3({})
    fake.get_paginator = lambda _name: SimpleNamespace(paginate=lambda **_kwargs: iter(pages))
    with patch("boto3.client", return_value=fake):
        response = prune_handler.lambda_handler({"httpMethod": "POST"}, None)
    assert json.loads(response["body"])["deleted"] == [
        "csps/aws/vertices.json", "csps/azure/vertices.json",
    ]


def test_the_prune_pages_the_listing_of_versions(prune_handler: Any) -> None:
    paged: list[str] = []
    fake = fake_s3({})

    def _paginator(name: str) -> Any:
        paged.append(name)
        return SimpleNamespace(paginate=lambda **_kwargs: iter([]))

    fake.get_paginator = _paginator
    with patch("boto3.client", return_value=fake):
        prune_handler.lambda_handler({"httpMethod": "POST"}, None)
    assert paged == ["list_object_versions"]


def _marked(objects: dict[str, bytes], keys: list[str]) -> Any:
    fake = fake_s3(objects)
    for key in keys:
        fake.delete_object(Key=key)
    return fake


def _markers_after_pruning(handler: Any, fake: Any) -> list[dict[str, Any]]:
    with patch("boto3.client", return_value=fake):
        handler.lambda_handler({"httpMethod": "POST"}, None)
    listing = fake.list_object_versions(Bucket="test-bucket")
    markers: list[dict[str, Any]] = listing["DeleteMarkers"]
    return markers


def test_the_prune_removes_a_marker_over_a_current_key(prune_handler: Any) -> None:
    fake = _marked(_store(), ["tenants/daf/wan.json"])
    assert _markers_after_pruning(prune_handler, fake) == []


def test_the_prune_removes_a_marker_over_a_stale_key(prune_handler: Any) -> None:
    fake = _marked(_store(), ["tenants/daf/csp-regions.json"])
    assert _markers_after_pruning(prune_handler, fake) == []


def test_the_prune_names_the_key_a_marker_hid(prune_handler: Any) -> None:
    fake = _marked({key: b"[]" for key in _CURRENT}, ["tenants/daf/wan.json"])
    with patch("boto3.client", return_value=fake):
        response = prune_handler.lambda_handler({"httpMethod": "POST"}, None)
    assert json.loads(response["body"])["deleted"] == ["tenants/daf/wan.json"]


def test_the_prune_leaves_every_current_object_beside_a_marker(prune_handler: Any) -> None:
    objects = _store()
    _markers_after_pruning(prune_handler, _marked(objects, ["tenants/two-node/wan.json"]))
    assert sorted(objects) == sorted(_CURRENT)


def test_the_prune_removes_a_marker_by_the_version_it_was_listed_with(
        prune_handler: Any) -> None:
    named: list[tuple[str, str | None]] = []
    marker = {"Key": "tenants/two-node/wan.json", "VersionId": "3sL4kqtJ", "IsLatest": True}
    fake = fake_s3({})
    fake.get_paginator = lambda _name: SimpleNamespace(
        paginate=lambda **_kwargs: iter([{"DeleteMarkers": [marker]}]))
    fake.delete_object = lambda **kwargs: named.append((kwargs["Key"], kwargs.get("VersionId")))
    with patch("boto3.client", return_value=fake):
        prune_handler.lambda_handler({"httpMethod": "POST"}, None)
    assert named == [("tenants/two-node/wan.json", "3sL4kqtJ")]


def test_a_get_names_the_key_a_marker_hides(prune_handler: Any) -> None:
    fake = _marked({key: b"[]" for key in _CURRENT}, ["tenants/two-node/wan.json"])
    with patch("boto3.client", return_value=fake):
        response = prune_handler.lambda_handler({"httpMethod": "GET"}, None)
    assert json.loads(response["body"])["stale"] == ["tenants/two-node/wan.json"]


def test_a_get_leaves_a_marker_where_it_is(prune_handler: Any) -> None:
    fake = _marked({}, ["tenants/two-node/wan.json"])
    with patch("boto3.client", return_value=fake):
        prune_handler.lambda_handler({"httpMethod": "GET"}, None)
    assert len(fake.list_object_versions(Bucket="test-bucket")["DeleteMarkers"]) == 1


def test_a_second_prune_finds_no_marker_left_to_remove(prune_handler: Any) -> None:
    fake = _marked(_store(), ["tenants/two-node/wan.json", "tenants/two-node/knobs.json"])
    _markers_after_pruning(prune_handler, fake)
    with patch("boto3.client", return_value=fake):
        response = prune_handler.lambda_handler({"httpMethod": "POST"}, None)
    assert json.loads(response["body"])["deleted"] == []


def test_the_prune_removes_a_key_rather_than_tombstoning_it(prune_handler: Any) -> None:
    named: list[str | None] = []
    fake = fake_s3({"csps/aws/vertices.json": b""})
    fake.delete_object = lambda **kwargs: named.append(kwargs.get("VersionId"))
    with patch("boto3.client", return_value=fake):
        prune_handler.lambda_handler({"httpMethod": "POST"}, None)
    assert named == ["null"]


def test_a_get_says_what_would_go_without_deleting_it(prune_handler: Any) -> None:
    objects = _store()
    with patch("boto3.client", return_value=fake_s3(objects)):
        prune_handler.lambda_handler({"httpMethod": "GET"}, None)
    assert sorted(objects) == sorted(_CURRENT + _STALE)


def test_a_get_names_the_same_keys_the_prune_would_delete(prune_handler: Any) -> None:
    with patch("boto3.client", return_value=fake_s3(_store())):
        response = prune_handler.lambda_handler({"httpMethod": "GET"}, None)
    assert json.loads(response["body"])["stale"] == sorted(_STALE)
