from __future__ import annotations

from pathlib import Path

import pytest

from repo_utils import REPO_ROOT
from etl.carriers.load_carriers import (
    carrier_files, carriers_in, every_carrier, fiber_segment_body, fiber_segments_of, pop_body,
    pops_of,
)

SIX_CARRIERS = ["cogent", "dcn", "lumen", "uniti", "vision_net", "zayo"]


@pytest.mark.parametrize("path", [
    "data/pops/zayo.csv",
    "data/fiber_segments/terrestrial/zayo.csv",
    "data/fiber_segments/submarine/zayo.csv",
])
def test_a_carrier_is_named_by_each_of_its_files(path: str) -> None:
    assert carriers_in([path]) == {"zayo"}


@pytest.mark.parametrize("path", [
    "data/providers/providers.csv",
    "data/tenants/daf.csv",
    "data/pops/README.md",
    "etc/daf.yml",
])
def test_a_path_outside_the_carrier_data_names_no_carrier(path: str) -> None:
    assert carriers_in([path]) == set()


def test_the_data_names_six_carriers() -> None:
    assert sorted(every_carrier(REPO_ROOT)) == SIX_CARRIERS


def test_a_pop_row_becomes_the_body_the_api_takes() -> None:
    row = {"Municipality": "Akron", "State": "OH", "Country": "United States",
           "Latitude": "41.0814", "Longitude": "-81.5190"}
    assert pop_body(row) == {"municipality": "Akron", "state": "OH", "country": "United States",
                             "latitude": 41.0814, "longitude": -81.519}


@pytest.mark.parametrize("submarine", [True, False])
def test_a_fiber_segment_row_becomes_the_body_the_api_takes(submarine: bool) -> None:
    row = {"A_Municipality": "London", "A_State": "", "Z_Municipality": "Paris", "Z_State": ""}
    assert fiber_segment_body(row, submarine) == {
        "a_municipality": "London", "a_state": "", "z_municipality": "Paris", "z_state": "",
        "submarine": submarine}


def test_zayo_is_three_files() -> None:
    found = carrier_files(REPO_ROOT, "zayo")
    assert [path.relative_to(REPO_ROOT).as_posix() for path in found] == [
        "data/pops/zayo.csv",
        "data/fiber_segments/terrestrial/zayo.csv",
        "data/fiber_segments/submarine/zayo.csv",
    ]


def test_an_unknown_carrier_is_no_files() -> None:
    assert not carrier_files(REPO_ROOT, "nobody")


def test_the_pops_of_a_carrier_are_every_row_of_its_csv() -> None:
    assert len(pops_of(REPO_ROOT, "vision_net")) == 9


def test_a_carrier_without_a_pops_csv_has_no_pops(tmp_path: Path) -> None:
    assert not pops_of(tmp_path, "vision_net")


def test_the_fiber_segments_of_a_carrier_are_terrestrial_then_submarine() -> None:
    assert [segment["submarine"] for segment in fiber_segments_of(REPO_ROOT, "zayo")] == (
        [False] * 361 + [True] * 24)


def test_a_carrier_without_a_fiber_segments_csv_has_no_fiber_segments(tmp_path: Path) -> None:
    assert not fiber_segments_of(tmp_path, "zayo")
