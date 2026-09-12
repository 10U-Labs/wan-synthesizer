from __future__ import annotations

import json
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
        {"Contents": [{"Key": "csps/aws/vertices.json"}],
         "IsTruncated": True, "NextContinuationToken": "more"},
        {"Contents": [{"Key": "csps/azure/vertices.json"}], "IsTruncated": False},
    ]
    fake = fake_s3({})
    fake.list_objects_v2 = lambda **kwargs: pages[1 if kwargs.get("ContinuationToken") else 0]
    with patch("boto3.client", return_value=fake):
        response = prune_handler.lambda_handler({"httpMethod": "POST"}, None)
    assert json.loads(response["body"])["deleted"] == [
        "csps/aws/vertices.json", "csps/azure/vertices.json",
    ]


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
