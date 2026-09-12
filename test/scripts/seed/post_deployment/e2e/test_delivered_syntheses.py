from __future__ import annotations

import csv
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError

import seed
from seed import DEFAULT_API, _get
from test_published_syntheses import (
    wan_pop_groups,
    cut_cities,
    diverse_circuit_count,
    offered_diverse_circuits,
    fiber_miles_run_over,
    overbuilt_pairs,
    removable_circuits,
    worst_haul,
)


_ROUNDED_TO = 0.001


def _rounding_slack(synthesis: dict[str, Any]) -> float:
    return (len(synthesis["fiber"]) + 1) * _ROUNDED_TO / 2


def _tenants_outside(
    syntheses: list[dict[str, Any]],
    allowed: Callable[[float, float, float], bool],
) -> dict[str, tuple[float, float]]:
    measured = {
        synthesis["tenant"]: (
            fiber_miles_run_over(synthesis),
            synthesis["lower_bound_miles"],
            _rounding_slack(synthesis),
        )
        for synthesis in syntheses
        if synthesis["lower_bound_miles"] is not None
    }
    return {
        tenant: (miles, floor)
        for tenant, (miles, floor, slack) in measured.items()
        if not allowed(miles, floor, slack)
    }


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


def test_every_published_network_is_one_network(
        published_syntheses: list[dict[str, Any]]) -> None:
    split = {
        synthesis["tenant"]: groups
        for synthesis in published_syntheses
        if len(groups := wan_pop_groups(synthesis)) > 1
    }
    assert split == {}


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


def test_no_published_network_runs_more_than_twice_the_fewest_miles_it_could_have(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert _tenants_outside(
        published_syntheses, lambda miles, floor, _slack: miles <= 2 * floor
    ) == {}


def test_no_published_network_runs_more_than_a_tenth_further_than_the_floor_it_publishes(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert _tenants_outside(
        published_syntheses, lambda miles, floor, _slack: miles <= 1.1 * floor
    ) == {}


def test_no_published_network_runs_fewer_miles_than_the_floor_it_publishes(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert _tenants_outside(
        published_syntheses, lambda miles, floor, slack: miles >= floor - slack
    ) == {}


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


def _carrier_fiber() -> set[frozenset[str]]:
    named = _city_names()
    pairs: set[frozenset[str]] = set()
    for path in sorted((seed.DATA / seed.FIBER_SEGMENTS).glob("*/*.csv")):
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
    fabricated = {row["name"] for row in synthesis["wan_pops"] if row.get("fabricated")}
    return {
        hop
        for circuit in synthesis["circuits"]
        for hop in _hops(circuit)
        if hop & fabricated
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


def _submarine_pairs(synthesis: dict[str, Any]) -> set[frozenset[str]]:
    return {
        frozenset({entry["source_name"], entry["target_name"]})
        for entry in synthesis["fiber"]
        if entry["submarine"]
    }


def _runs_under_water(pops: list[str], under_water: set[frozenset[str]]) -> bool:
    return any(
        frozenset({near, far}) in under_water for near, far in zip(pops, pops[1:])
    )


def _circuits_each_site_holds(synthesis: dict[str, Any]) -> dict[str, list[list[str]]]:
    held: dict[str, list[list[str]]] = {}
    for circuit in synthesis["circuits"]:
        for end in (circuit["route"][0], circuit["route"][-1]):
            held.setdefault(end, []).append(circuit["route"])
    return held


def _sites_ashore_holding_a_crossing(synthesis: dict[str, Any]) -> list[tuple[str, ...]]:
    under_water = _submarine_pairs(synthesis)
    return [
        (synthesis["tenant"], site, " -> ".join(pops))
        for site, circuits in sorted(_circuits_each_site_holds(synthesis).items())
        for pops in circuits
        if _runs_under_water(pops, under_water)
        and any(not _runs_under_water(other, under_water) for other in circuits)
    ]


def test_no_published_site_with_a_circuit_over_land_is_drawn_one_under_water(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert [
        offender
        for synthesis in published_syntheses
        for offender in _sites_ashore_holding_a_crossing(synthesis)
    ] == []


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
