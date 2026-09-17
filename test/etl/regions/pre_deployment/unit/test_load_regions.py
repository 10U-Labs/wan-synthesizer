from __future__ import annotations

from repo_utils import REPO_ROOT
from etl.regions.load_regions import PROVIDERS, region_body, regions_of


def test_the_providers_file_is_where_the_data_keeps_it() -> None:
    assert (REPO_ROOT / PROVIDERS).is_file()


def test_a_region_row_becomes_the_body_the_api_takes() -> None:
    row = {"Name": "Provider A", "Municipality": "Columbus", "State": "OH",
           "Country": "United States", "Latitude": "39.9612", "Longitude": "-82.9988"}
    assert region_body(row) == {
        "name": "Provider A", "municipality": "Columbus", "state": "OH",
        "country": "United States", "latitude": 39.9612, "longitude": -82.9988}


def test_the_regions_are_every_row_of_the_file() -> None:
    assert len(regions_of(REPO_ROOT)) == 10


def test_every_region_is_named() -> None:
    assert all(region["name"] for region in regions_of(REPO_ROOT))
