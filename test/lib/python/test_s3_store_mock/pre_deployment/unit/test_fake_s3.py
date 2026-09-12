from __future__ import annotations

import pytest

from test_s3_store_mock import NoSuchKey, fake_s3


def test_a_stored_object_reads_back_as_it_was_stored() -> None:
    client = fake_s3({"carriers/lumen/pops.json": b'[{"id": "P0"}]'})
    served = client.get_object(Key="carriers/lumen/pops.json")
    assert served["Body"].read() == b'[{"id": "P0"}]'


def test_a_key_nobody_stored_raises_what_the_real_client_raises() -> None:
    client = fake_s3({})
    with pytest.raises(NoSuchKey):
        client.get_object(Key="carriers/lumen/pops.json")


def test_the_error_the_handlers_catch_is_the_error_the_double_raises() -> None:
    assert fake_s3({}).exceptions.NoSuchKey is NoSuchKey


def test_a_written_object_is_readable_afterwards() -> None:
    client = fake_s3({})
    client.put_object(Key="tenants/daf/label.json", Body=b'{"name": "daf"}')
    assert client.get_object(Key="tenants/daf/label.json")["Body"].read() == b'{"name": "daf"}'


def test_a_write_replaces_what_was_there() -> None:
    objects = {"tenants/daf/label.json": b'{"name": "stale"}'}
    fake_s3(objects).put_object(Key="tenants/daf/label.json", Body=b'{"name": "daf"}')
    assert objects["tenants/daf/label.json"] == b'{"name": "daf"}'


def test_a_write_is_answered_the_way_the_real_client_answers() -> None:
    assert fake_s3({}).put_object(Key="tenants/daf/label.json", Body=b"{}") == {}


def test_a_deleted_object_is_gone_from_the_store() -> None:
    objects = {"tenants/daf/label.json": b"{}"}
    fake_s3(objects).delete_object(Key="tenants/daf/label.json")
    assert "tenants/daf/label.json" not in objects


def test_deleting_a_key_that_is_not_there_is_not_an_error() -> None:
    assert fake_s3({}).delete_object(Key="tenants/daf/label.json") == {}


def test_the_listing_is_the_keys_the_store_holds() -> None:
    client = fake_s3({"carriers/lumen/pops.json": b"[]", "carriers/zayo/pops.json": b"[]"})
    assert client.list_objects_v2(Bucket="store")["Contents"] == [
        {"Key": "carriers/lumen/pops.json"},
        {"Key": "carriers/zayo/pops.json"},
    ]


def test_a_listing_given_outright_is_the_one_served() -> None:
    client = fake_s3({}, keys=["carriers/lumen/pops.json"])
    assert client.list_objects_v2(Bucket="store")["Contents"] == [
        {"Key": "carriers/lumen/pops.json"}
    ]


def test_a_listing_given_as_empty_is_served_empty() -> None:
    client = fake_s3({"carriers/lumen/pops.json": b"[]"}, keys=[])
    assert client.list_objects_v2(Bucket="store")["Contents"] == []


def test_a_listing_narrowed_by_prefix_leaves_out_what_is_not_under_it() -> None:
    client = fake_s3({"carriers/lumen/pops.json": b"[]", "carriers/zayo/pops.json": b"[]"})
    listing = client.list_objects_v2(Bucket="store", Prefix="carriers/lumen/")
    assert listing["Contents"] == [{"Key": "carriers/lumen/pops.json"}]


def test_a_prefix_the_store_has_nothing_under_lists_nothing() -> None:
    client = fake_s3({"carriers/lumen/pops.json": b"[]"})
    assert client.list_objects_v2(Bucket="store", Prefix="carriers/ghost/")["Contents"] == []


def test_a_listing_given_outright_is_narrowed_by_prefix_too() -> None:
    keys = ["carriers/lumen/pops.json", "tenants/daf/label.json"]
    client = fake_s3({}, keys=keys)
    listing = client.list_objects_v2(Bucket="store", Prefix="tenants/")
    assert listing["Contents"] == [{"Key": "tenants/daf/label.json"}]


_NULL_VERSION = {"Key": "tenants/daf/label.json", "VersionId": "null", "IsLatest": True}


def test_a_delete_naming_no_version_leaves_a_delete_marker() -> None:
    client = fake_s3({"tenants/daf/label.json": b"{}"})
    client.delete_object(Key="tenants/daf/label.json")
    assert client.list_object_versions(Bucket="store")["DeleteMarkers"] == [_NULL_VERSION]


def test_a_delete_naming_no_version_hides_the_key_from_get_object() -> None:
    client = fake_s3({"tenants/daf/label.json": b"{}"})
    client.delete_object(Key="tenants/daf/label.json")
    with pytest.raises(NoSuchKey):
        client.get_object(Key="tenants/daf/label.json")


def test_a_delete_naming_no_version_hides_the_key_from_the_listing() -> None:
    client = fake_s3({"tenants/daf/label.json": b"{}"})
    client.delete_object(Key="tenants/daf/label.json")
    assert client.list_objects_v2(Bucket="store")["Contents"] == []


def test_a_delete_naming_the_null_version_leaves_no_marker() -> None:
    client = fake_s3({"tenants/daf/label.json": b"{}"})
    client.delete_object(Key="tenants/daf/label.json", VersionId="null")
    assert client.list_object_versions(Bucket="store")["DeleteMarkers"] == []


def test_a_delete_naming_the_null_version_removes_the_object() -> None:
    objects = {"tenants/daf/label.json": b"{}"}
    fake_s3(objects).delete_object(Key="tenants/daf/label.json", VersionId="null")
    assert "tenants/daf/label.json" not in objects


def test_a_delete_naming_the_null_version_clears_the_marker_over_a_key() -> None:
    client = fake_s3({"tenants/daf/label.json": b"{}"})
    client.delete_object(Key="tenants/daf/label.json")
    client.delete_object(Key="tenants/daf/label.json", VersionId="null")
    assert client.list_object_versions(Bucket="store")["DeleteMarkers"] == []


def test_a_write_over_a_marker_clears_it() -> None:
    client = fake_s3({"tenants/daf/label.json": b"{}"})
    client.delete_object(Key="tenants/daf/label.json")
    client.put_object(Key="tenants/daf/label.json", Body=b"{}")
    assert client.list_object_versions(Bucket="store")["DeleteMarkers"] == []


def test_the_versions_listing_is_every_object_as_its_null_version() -> None:
    client = fake_s3({"tenants/daf/label.json": b"{}"})
    assert client.list_object_versions(Bucket="store")["Versions"] == [_NULL_VERSION]


def test_the_versions_listing_is_narrowed_by_prefix() -> None:
    client = fake_s3({"carriers/lumen/pops.json": b"[]", "tenants/daf/label.json": b"{}"})
    listing = client.list_object_versions(Bucket="store", Prefix="tenants/")
    assert listing["Versions"] == [_NULL_VERSION]


def test_the_markers_listing_is_narrowed_by_prefix() -> None:
    client = fake_s3({"carriers/lumen/pops.json": b"[]", "tenants/daf/label.json": b"{}"})
    client.delete_object(Key="carriers/lumen/pops.json")
    client.delete_object(Key="tenants/daf/label.json")
    listing = client.list_object_versions(Bucket="store", Prefix="tenants/")
    assert listing["DeleteMarkers"] == [_NULL_VERSION]


def test_the_paginator_serves_the_versions_listing_as_one_page() -> None:
    client = fake_s3({"tenants/daf/label.json": b"{}"})
    pages = list(client.get_paginator("list_object_versions").paginate(Bucket="store"))
    assert [page["Versions"] for page in pages] == [[_NULL_VERSION]]


def test_the_paginator_serves_the_markers_on_the_same_page() -> None:
    client = fake_s3({"tenants/daf/label.json": b"{}"})
    client.delete_object(Key="tenants/daf/label.json")
    page = next(iter(client.get_paginator("list_object_versions").paginate(Bucket="store")))
    assert page["DeleteMarkers"] == [_NULL_VERSION]
