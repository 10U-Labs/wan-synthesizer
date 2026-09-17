from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

import pytest

from loader import DEFAULT_API
from repo_utils import REPO_ROOT
from etl.syntheses.load_syntheses import SYNTHESES, configurations, read_configuration, sites_of

CONFIGURATIONS = {path.stem: read_configuration(path) for path in configurations(REPO_ROOT)}


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
    listed: list[dict[str, Any]] = _served(SYNTHESES)
    return listed


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
    served = _served(f"{SYNTHESES}/{newest}/sites")
    assert _sorted(served) == _sorted(sites_of(REPO_ROOT, CONFIGURATIONS[name]))


@pytest.mark.parametrize("name", sorted(CONFIGURATIONS))
def test_the_newest_synthesis_of_each_run_was_given_its_forced_wan_pops(
        newest: int, name: str) -> None:
    served = _served(f"{SYNTHESES}/{newest}/forced-wan-pops")
    forced = CONFIGURATIONS[name]["backbone"]["forced"]["wan_pops"]
    assert [one["name"] for one in served] == forced

