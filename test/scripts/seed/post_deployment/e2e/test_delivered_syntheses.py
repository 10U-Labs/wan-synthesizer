from __future__ import annotations

import csv
from typing import Any
from urllib.error import HTTPError

import seed
from seed import DEFAULT_API, _get
from synthesizer.input_graph import Site
from synthesizer.local_fiber import LOCAL_FIBER_HOMING_DEGREE, nearest_carrier_pops
from test_published_syntheses import (
    offered_diverse_circuits,
    site_from_row,
)


def _published_cities(synthesis: dict[str, Any]) -> set[str]:
    return {site["name"] for site in synthesis["wan_pops"]}


_SPLIT_REFUSAL = "splits the WAN at: "


def _refused_for_a_split(status: dict[str, Any]) -> bool:
    return status.get("status") == "fail" and _SPLIT_REFUSAL in status.get("reason", "")


def _still_serves_a_wan(tenant: str) -> bool:
    try:
        _get(DEFAULT_API, f"tenants/{tenant}/wan-pops")
    except HTTPError:
        return False
    return True


def test_every_tenant_the_roster_declares_is_published_or_refused_for_a_split(
        delivered_syntheses: list[dict[str, Any]]) -> None:
    unfinished = {
        synthesis["tenant"]: synthesis["status"].get("status")
        for synthesis in delivered_syntheses
        if synthesis["status"].get("status") != "success"
        and not _refused_for_a_split(synthesis["status"])
    }
    assert unfinished == {}


def test_every_split_refusal_names_the_pop_whose_loss_would_split_the_wan(
        delivered_syntheses: list[dict[str, Any]]) -> None:
    unnamed = [
        synthesis["tenant"]
        for synthesis in delivered_syntheses
        if _refused_for_a_split(synthesis["status"])
        and not synthesis["status"]["reason"].split(_SPLIT_REFUSAL, 1)[1].strip()
    ]
    assert unnamed == []


def test_no_refused_tenant_still_serves_the_wan_it_published_before(
        delivered_syntheses: list[dict[str, Any]]) -> None:
    served = [
        synthesis["tenant"]
        for synthesis in delivered_syntheses
        if synthesis["status"].get("status") != "success"
        and _still_serves_a_wan(synthesis["tenant"])
    ]
    assert served == []


def test_every_published_network_reports_the_coverage_it_delivered(
        published_syntheses: list[dict[str, Any]]) -> None:
    silent = [
        synthesis["tenant"]
        for synthesis in published_syntheses
        if "coverage" not in synthesis["status"]
    ]
    assert silent == []


def test_every_report_is_measured_against_the_target_its_tenant_declares(
        published_syntheses: list[dict[str, Any]]) -> None:
    reported = {
        synthesis["tenant"]: synthesis["status"]["coverage"]["target_miles"]
        for synthesis in published_syntheses
    }
    declared = {synthesis["tenant"]: synthesis["target_miles"] for synthesis in published_syntheses}
    assert reported == declared


def test_every_city_a_tenant_pins_is_selected_into_its_published_backbone(
        published_syntheses: list[dict[str, Any]]) -> None:
    unselected = {
        synthesis["tenant"]: sorted(set(synthesis["forced"]) - _published_cities(synthesis))
        for synthesis in published_syntheses
        if not set(synthesis["forced"]) <= _published_cities(synthesis)
    }
    assert unselected == {}


def test_no_synthesis_missed_its_coverage_target_below_the_wan_pops_it_was_allowed(
        published_syntheses: list[dict[str, Any]]) -> None:
    gave_up_early = [
        (synthesis["tenant"], len(synthesis["wan_pops"]), synthesis["max_wan_pop_count"])
        for synthesis in published_syntheses
        if not synthesis["status"]["coverage"]["met"]
        and len(synthesis["wan_pops"]) < synthesis["max_wan_pop_count"]
    ]
    assert gave_up_early == []


def test_no_published_status_carries_a_backup_path_multiple(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert [
        synthesis["tenant"]
        for synthesis in published_syntheses
        if "max_backup_path_multiple" in synthesis["status"]
    ] == []


def test_no_published_network_leaves_a_site_short_of_the_circuits_it_was_asked_for(
        published_syntheses: list[dict[str, Any]]) -> None:
    short = {
        synthesis["tenant"]: synthesis["status"]["diverse_circuits"]["short"]
        for synthesis in published_syntheses
    }
    assert {tenant: sites for tenant, sites in short.items() if sites} == {}


def _city_names() -> dict[tuple[str, str], str]:
    named: dict[tuple[str, str], str] = {}
    for path in sorted((seed.DATA / "pops").glob("*.csv")):
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                region = (
                    row["State"] if row["Country"] == "United States" else row["Country"]
                )
                named[(row["Municipality"], row["State"])] = (
                    f"{row['Municipality']}, {region}"
                )
    return named


def _carrier_pops() -> list[Site]:
    named = _city_names()
    pops: dict[str, Site] = {}
    for path in sorted((seed.DATA / "pops").glob("*.csv")):
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                name = named[(row["Municipality"], row["State"])]
                pops.setdefault(
                    name,
                    Site(name, name, "PoP", (float(row["Latitude"]), float(row["Longitude"]))),
                )
    return list(pops.values())


def _carrier_fiber(directory: str = "*") -> set[frozenset[str]]:
    named = _city_names()
    pairs: set[frozenset[str]] = set()
    for path in sorted((seed.DATA / seed.FIBER_SEGMENTS).glob(f"{directory}/*.csv")):
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                near = named.get((row["A_Municipality"], row["A_State"]))
                far = named.get((row["Z_Municipality"], row["Z_State"]))
                if near and far:
                    pairs.add(frozenset({near, far}))
    return pairs


def _fiber_laid_to_a_fabricated_wan_pop(synthesis: dict[str, Any]) -> set[frozenset[str]]:
    pops = _carrier_pops()
    return {
        frozenset({row["name"], pop.name})
        for row in synthesis["wan_pops"]
        if row.get("fabricated")
        for pop in nearest_carrier_pops(
            site_from_row(row), pops, LOCAL_FIBER_HOMING_DEGREE, None
        )
    }


def _tenants_fiber(synthesis: dict[str, Any]) -> set[frozenset[str]]:
    return _carrier_fiber() | _fiber_laid_to_a_fabricated_wan_pop(synthesis)


def _cities_with_fiber(held: set[frozenset[str]]) -> set[str]:
    return {city for pair in held for city in pair}


def _overstated_ceilings(syntheses: list[dict[str, Any]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for synthesis in syntheses:
        held = _tenants_fiber(synthesis)
        reached = _cities_with_fiber(held)
        cities = _published_cities(synthesis)
        for entry in synthesis["status"].get("diverse_circuits", {}).get("ceilings", []):
            city = str(entry["name"])
            if city not in reached:
                continue
            offered = offered_diverse_circuits(held, city, frozenset(cities - {city}))
            if int(entry["ceiling"]) > offered:
                found.setdefault(synthesis["tenant"], []).append(
                    f"{city} at {entry['ceiling']} against {offered}"
                )
    return found


def test_no_published_networks_ceiling_is_higher_than_the_circuits_its_carriers_can_offer(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert not _overstated_ceilings(published_syntheses)
