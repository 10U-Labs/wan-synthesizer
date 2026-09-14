from __future__ import annotations

import csv
from typing import Any
from urllib.error import HTTPError

import seed
from seed import DEFAULT_API, _get
from synthesizer.input_graph import Site
from synthesizer.local_fiber import LOCAL_FIBER_HOMING_DEGREE, nearest_carrier_pops
from test_published_syntheses import (
    cut_cities,
    diverse_circuit_count,
    offered_diverse_circuits,
    overbuilt_pairs,
    removable_circuits,
    site_from_row,
    worst_haul,
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


def test_the_reported_worst_haul_is_the_one_the_published_network_delivers(
        published_syntheses: list[dict[str, Any]]) -> None:
    mismeasured = [
        (synthesis["tenant"], worst_haul(synthesis))
        for synthesis in published_syntheses
        if worst_haul(synthesis) != synthesis["status"]["coverage"]["worst_haul_miles"]
    ]
    assert mismeasured == []


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


def test_no_published_network_draws_a_pair_more_circuits_than_its_tenant_asked_for(
        published_syntheses: list[dict[str, Any]]) -> None:
    overbuilt = {
        synthesis["tenant"]: overbuilt_pairs(synthesis)
        for synthesis in published_syntheses
        if overbuilt_pairs(synthesis)
    }
    assert overbuilt == {}


def test_no_published_network_holds_a_circuit_that_is_nobodys_diverse_circuit(
        published_syntheses: list[dict[str, Any]]) -> None:
    spare = {
        synthesis["tenant"]: removable_circuits(synthesis)
        for synthesis in published_syntheses
    }
    assert {tenant: circuits for tenant, circuits in spare.items() if circuits} == {}


def test_no_published_network_is_split_by_the_loss_of_one_city(
        published_syntheses: list[dict[str, Any]]) -> None:
    split = {
        synthesis["tenant"]: cut_cities(synthesis["circuits"])
        for synthesis in published_syntheses
    }
    assert {tenant: cities for tenant, cities in split.items() if cities} == {}


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


def _hops(circuit: dict[str, Any]) -> list[frozenset[str]]:
    cities = circuit.get("route") or []
    return [frozenset({left, right}) for left, right in zip(cities, cities[1:])]


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


def _circuits_over_fiber_nobody_owns(syntheses: list[dict[str, Any]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for synthesis in syntheses:
        fiber = _tenants_fiber(synthesis)
        for circuit in synthesis["circuits"]:
            if any(hop not in fiber for hop in _hops(circuit)):
                found.setdefault(synthesis["tenant"], []).append(
                    f"{circuit['source_name']} to {circuit['target_name']}"
                )
    return found


def test_every_published_circuit_runs_over_segments_each_of_which_a_carrier_owns(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert not _circuits_over_fiber_nobody_owns(published_syntheses)


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


def _credited_past_the_ceiling(synthesis: dict[str, Any]) -> list[str]:
    names = {row["id"]: row["name"] for row in synthesis["wan_pops"]}
    ceilings = {
        str(entry["name"]): int(entry["ceiling"])
        for entry in synthesis["status"].get("diverse_circuits", {}).get("ceilings", [])
    }
    return [
        f"{name} credited {credited} against a ceiling of {ceilings[name]}"
        for site, name in sorted(names.items(), key=lambda pair: pair[1])
        if name in ceilings
        and (credited := diverse_circuit_count(synthesis["circuits"], site, names))
        > ceilings[name]
    ]


def test_no_published_wan_pop_is_credited_more_diverse_circuits_than_its_ceiling(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert {
        synthesis["tenant"]: _credited_past_the_ceiling(synthesis)
        for synthesis in published_syntheses
        if _credited_past_the_ceiling(synthesis)
    } == {}


def _sites_homed_the_wrong_number_of_times(synthesis: dict[str, Any]) -> dict[str, int]:
    homed: dict[str, int] = {}
    for circuit in synthesis["homings"]:
        homed[circuit["source_id"]] = homed.get(circuit["source_id"], 0) + 1
    return {
        site: count
        for site, count in sorted(homed.items())
        if count != synthesis["homing_degree"]
    }


def test_every_published_demand_site_holds_the_homing_circuits_it_was_asked_for(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert {
        synthesis["tenant"]: _sites_homed_the_wrong_number_of_times(synthesis)
        for synthesis in published_syntheses
        if _sites_homed_the_wrong_number_of_times(synthesis)
    } == {}


_KIND_OF = {"tenant_to_backbone": "tenant", "provider_to_backbone": "provider"}


def _homing_miles_served(synthesis: dict[str, Any], kind: str) -> float:
    miles: list[float] = [
        circuit["distance_miles"]
        for circuit in synthesis["homings"]
        if _KIND_OF[circuit["homing_kind"]] == kind
    ]
    return sum(miles)


def _figure_off_its_circuits(synthesis: dict[str, Any], kind: str) -> bool:
    published: float = synthesis["status"]["homing_miles"][kind]
    slack = (len(synthesis["homings"]) + 1) * _ROUNDED_TO / 2
    return abs(published - _homing_miles_served(synthesis, kind)) > slack


def test_every_published_figure_for_a_tenants_own_sites_is_the_miles_of_their_circuits(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert [
        synthesis["tenant"]
        for synthesis in published_syntheses
        if _figure_off_its_circuits(synthesis, "tenant")
    ] == []


def test_every_published_figure_for_the_provider_regions_is_the_miles_of_their_circuits(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert [
        synthesis["tenant"]
        for synthesis in published_syntheses
        if _figure_off_its_circuits(synthesis, "provider")
    ] == []


def test_no_published_site_is_served_as_a_tenant_site_and_a_provider_region_both(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert {
        synthesis["tenant"]: sorted(
            {row["id"] for row in synthesis["tenant_sites"]}
            & {row["id"] for row in synthesis["provider_regions"]}
        )
        for synthesis in published_syntheses
        if {row["id"] for row in synthesis["tenant_sites"]}
        & {row["id"] for row in synthesis["provider_regions"]}
    } == {}
