from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

import pytest

from loader import DEFAULT_API
from repo_utils import REPO_ROOT
from etl.regions.load_regions import REGIONS, regions_of


def _served(path: str) -> Any:
    request = urllib.request.Request(
        f"{DEFAULT_API}/{path}", headers={"Authorization": f"Bearer {os.environ['API_KEY']}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def _sorted(listed: list[dict[str, Any]]) -> list[str]:
    return sorted(json.dumps({k: v for k, v in row.items() if k != "id"}, sort_keys=True)
                  for row in listed)


@pytest.fixture(name="listing", scope="module")
def listing_fixture() -> list[dict[str, Any]]:
    listed: list[dict[str, Any]] = _served(REGIONS)
    return listed


def test_the_regions_served_are_the_csv(listing: list[dict[str, Any]]) -> None:
    assert _sorted(listing) == _sorted(regions_of(REPO_ROOT))


def test_every_region_served_is_served_at_its_own_url(listing: list[dict[str, Any]]) -> None:
    assert [_served(f"{REGIONS}/{region['id']}") for region in listing] == listing
