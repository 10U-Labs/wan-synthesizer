from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from repo_utils import REPO_ROOT
from etl.syntheses.load_syntheses import (
    body, configuration_named, configurations, read_configuration, region_given, site_body,
    sites_of, sites_paths, touched,
)

ROW = {"Name": "Ashburn", "Municipality": "Ashburn", "State": "VA", "Country": "United States",
       "Latitude": "39.0438", "Longitude": "-77.4874", "ExemptFromDistanceConstraint": "No"}
DAF = read_configuration(configuration_named(REPO_ROOT, "daf"))
REGION = {"id": 7, "name": "Provider A", "municipality": "Columbus", "state": "OH",
          "country": "United States", "latitude": 39.9612, "longitude": -82.9988}
FIELDS = [
    "label", "wan_pop_count", "backbone_number_of_diverse_circuits", "homing_degree",
    "convergence_promotion", "knobs", "settings", "sites",
    "hyperscale_cloud_service_provider_regions", "off_net", "forced_wan_pops",
    "forced_circuits", "forced_homes", "prohibited_wan_pops", "prohibited_circuits",
    "degree_exempt_wan_pops",
]


def test_the_configurations_are_every_yml_under_etc() -> None:
    assert [path.stem for path in configurations(REPO_ROOT)] == [
        "daf", "dow", "f_35", "minuteman", "two_pop"]


def test_a_configuration_is_named_by_its_stem() -> None:
    assert configuration_named(REPO_ROOT, "daf") == REPO_ROOT / "etc" / "daf.yml"


def test_a_site_row_becomes_the_body_the_api_takes() -> None:
    assert site_body(ROW) == {
        "name": "Ashburn", "municipality": "Ashburn", "state": "VA", "country": "United States",
        "latitude": 39.0438, "longitude": -77.4874, "exempt_from_distance_constraint": False}


@pytest.mark.parametrize("answer", ["Yes", "yes", " YES "])
def test_a_site_answering_yes_is_exempt_from_the_distance_constraint(answer: str) -> None:
    assert site_body({**ROW, "ExemptFromDistanceConstraint": answer})[
        "exempt_from_distance_constraint"] is True


def test_the_sites_of_a_configuration_are_every_row_of_the_files_it_names() -> None:
    assert len(sites_of(REPO_ROOT, DAF)) == 75


def test_a_region_is_given_less_its_id() -> None:
    assert region_given(REGION) == {key: value for key, value in REGION.items() if key != "id"}


def test_the_body_carries_exactly_the_fields_the_api_takes() -> None:
    assert list(body(DAF, [], [REGION])) == FIELDS


@pytest.mark.parametrize("field, expected", [
    ("label", "DAF"),
    ("wan_pop_count", {"min": 3, "max": 99}),
    ("backbone_number_of_diverse_circuits", 2),
    ("homing_degree", 2),
    ("convergence_promotion", False),
    ("knobs", {"backbone_coverage_target_miles": 745}),
    ("off_net", []),
    ("forced_circuits", []),
    ("forced_homes", []),
    ("prohibited_wan_pops", []),
    ("degree_exempt_wan_pops", []),
])
def test_the_body_is_read_off_the_configuration(field: str, expected: Any) -> None:
    assert body(DAF, [], [REGION])[field] == expected


def test_the_body_carries_the_forced_wan_pops_of_the_configuration() -> None:
    assert body(DAF, [], [REGION])["forced_wan_pops"] == DAF["backbone"]["forced"]["wan_pops"]


def test_the_body_carries_the_settings_as_given() -> None:
    assert body(DAF, [], [REGION])["settings"] == DAF["settings"]


def test_the_body_carries_the_sites_it_is_handed() -> None:
    assert body(DAF, [site_body(ROW)], [])["sites"] == [site_body(ROW)]


def test_the_body_carries_the_regions_less_their_ids() -> None:
    assert body(DAF, [], [REGION])["hyperscale_cloud_service_provider_regions"] == [
        region_given(REGION)]


def test_a_configuration_is_touched_by_a_change_to_itself() -> None:
    every = configurations(REPO_ROOT)
    assert touched(REPO_ROOT, every, ["etc/dow.yml"]) == [REPO_ROOT / "etc" / "dow.yml"]


def test_a_configuration_is_touched_by_a_change_to_a_sites_file_it_names() -> None:
    every = configurations(REPO_ROOT)
    assert touched(REPO_ROOT, every, ["data/tenants/f_35.csv"]) == [REPO_ROOT / "etc" / "f_35.yml"]


def test_a_configuration_is_untouched_by_a_change_elsewhere() -> None:
    assert touched(REPO_ROOT, configurations(REPO_ROOT), ["data/tenants/README.md"]) == []


def test_the_sites_paths_are_relative_to_the_repository() -> None:
    assert sites_paths(DAF) == [Path("data") / "tenants" / "daf.csv"]
