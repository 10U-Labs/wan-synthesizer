from __future__ import annotations

from repo_utils import REPO_ROOT
from etl.regions.load_regions import PROVIDERS, regions_of


def test_the_providers_file_is_where_the_data_keeps_it() -> None:
    assert (REPO_ROOT / PROVIDERS).is_file()


def test_the_regions_are_every_row_of_the_file() -> None:
    assert len(regions_of(REPO_ROOT)) == 10


def test_every_region_is_named() -> None:
    assert all(region["name"] for region in regions_of(REPO_ROOT))
