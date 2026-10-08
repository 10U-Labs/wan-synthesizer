from __future__ import annotations

import time
from typing import Any

import pytest

from loader import DEFAULT_API, Api, key, sorted_without_ids
from repo_utils import REPO_ROOT
from etl.regions.load_regions import REGIONS, regions_of

API = Api(DEFAULT_API, key(), time.sleep)


@pytest.fixture(name="listing", scope="module")
def listing_fixture() -> list[dict[str, Any]]:
    return API.listing(REGIONS)


def test_the_regions_served_are_the_csv(listing: list[dict[str, Any]]) -> None:
    assert sorted_without_ids(listing) == sorted_without_ids(regions_of(REPO_ROOT))


def test_every_region_served_is_served_at_its_own_url(listing: list[dict[str, Any]]) -> None:
    assert [API.get(f"{REGIONS}/{region['id']}") for region in listing] == listing
