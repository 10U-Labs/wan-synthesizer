from __future__ import annotations

import time
from typing import Any

import pytest

from loader import DEFAULT_API, Api, key, sorted_without_ids
from repo_utils import REPO_ROOT
from etl.syntheses.load_syntheses import SYNTHESES, configurations, read_configuration, sites_of

CONFIGURATIONS = {path.stem: read_configuration(path) for path in configurations(REPO_ROOT)}
API = Api(DEFAULT_API, key(), time.sleep)


@pytest.fixture(name="listing", scope="module")
def listing_fixture() -> list[dict[str, Any]]:
    return API.listing(SYNTHESES)


@pytest.fixture(name="newest")
def newest_fixture(listing: list[dict[str, Any]], name: str) -> int:
    label = CONFIGURATIONS[name]["label"]
    ids = [int(one["id"]) for one in listing if one["label"] == label]
    if not ids:
        raise AssertionError(f"no synthesis is labelled {label}")
    return max(ids)


@pytest.mark.parametrize("name", sorted(CONFIGURATIONS))
def test_every_configuration_has_a_synthesis(listing: list[dict[str, Any]], name: str) -> None:
    assert CONFIGURATIONS[name]["label"] in [one["label"] for one in listing]


def test_no_synthesis_carries_a_label_no_configuration_has(
        listing: list[dict[str, Any]]) -> None:
    labels = {configuration["label"] for configuration in CONFIGURATIONS.values()}
    assert [one for one in listing if one["label"] not in labels] == []


@pytest.mark.parametrize("name", sorted(CONFIGURATIONS))
def test_the_newest_synthesis_of_each_run_was_given_the_sites_of_its_files(
        newest: int, name: str) -> None:
    served = API.get(f"{SYNTHESES}/{newest}/sites")
    given = sites_of(REPO_ROOT, CONFIGURATIONS[name])
    assert sorted_without_ids(served) == sorted_without_ids(given)


@pytest.mark.parametrize("name", sorted(CONFIGURATIONS))
def test_the_newest_synthesis_of_each_run_was_given_its_forced_wan_pops(
        newest: int, name: str) -> None:
    served = API.get(f"{SYNTHESES}/{newest}/forced-wan-pops")
    forced = CONFIGURATIONS[name]["backbone"]["forced"]["wan_pops"]
    assert [one["name"] for one in served] == forced
