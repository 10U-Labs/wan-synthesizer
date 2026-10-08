from __future__ import annotations

import time
from typing import Any

import pytest

from loader import DEFAULT_API, Api, key, sorted_without_ids
from repo_utils import REPO_ROOT
from etl.carriers.load_carriers import every_carrier, fiber_segments_of, pops_of

CARRIERS = sorted(every_carrier(REPO_ROOT))
API = Api(DEFAULT_API, key(), time.sleep)


@pytest.fixture(name="listing", scope="module")
def listing_fixture() -> list[dict[str, Any]]:
    return API.listing("carriers")


@pytest.fixture(name="carrier_id")
def carrier_id_fixture(listing: list[dict[str, Any]], name: str) -> int:
    ids = [int(carrier["id"]) for carrier in listing if carrier["name"] == name]
    if len(ids) != 1:
        raise AssertionError(f"{name} is listed {len(ids)} times")
    return ids[0]


@pytest.mark.parametrize("name", CARRIERS)
def test_each_carrier_the_data_names_is_listed_once(
        listing: list[dict[str, Any]], name: str) -> None:
    assert [carrier["name"] for carrier in listing].count(name) == 1


def test_no_carrier_the_data_does_not_name_is_listed(listing: list[dict[str, Any]]) -> None:
    assert sorted(carrier["name"] for carrier in listing) == CARRIERS


@pytest.mark.parametrize("name", CARRIERS)
def test_the_pops_served_are_the_csv(carrier_id: int, name: str) -> None:
    served = API.get(f"carriers/{carrier_id}/pops")
    assert sorted_without_ids(served) == sorted_without_ids(pops_of(REPO_ROOT, name))


@pytest.mark.parametrize("name", CARRIERS)
def test_the_fiber_segments_served_are_the_csv(carrier_id: int, name: str) -> None:
    served = API.get(f"carriers/{carrier_id}/fiber-segments")
    assert sorted_without_ids(served) == sorted_without_ids(fiber_segments_of(REPO_ROOT, name))
