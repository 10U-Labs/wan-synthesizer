from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

import pytest

from repo_utils import REPO_ROOT
from etl.carriers.load_carriers import DEFAULT_API, every_carrier, fiber_segments_of, pops_of

CARRIERS = sorted(every_carrier(REPO_ROOT))


def _served(path: str) -> Any:
    request = urllib.request.Request(
        f"{DEFAULT_API}/{path}", headers={"Authorization": f"Bearer {os.environ['API_KEY']}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def _sorted(rows: list[dict[str, Any]]) -> list[str]:
    return sorted(json.dumps({k: v for k, v in row.items() if k != "id"}, sort_keys=True)
                  for row in rows)


@pytest.fixture(name="listing", scope="module")
def listing_fixture() -> list[dict[str, Any]]:
    listed: list[dict[str, Any]] = _served("carriers")
    return listed


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
    served = _served(f"carriers/{carrier_id}/pops")
    assert _sorted(served) == _sorted(pops_of(REPO_ROOT, name))


@pytest.mark.parametrize("name", CARRIERS)
def test_the_fiber_segments_served_are_the_csv(carrier_id: int, name: str) -> None:
    served = _served(f"carriers/{carrier_id}/fiber-segments")
    assert _sorted(served) == _sorted(fiber_segments_of(REPO_ROOT, name))
