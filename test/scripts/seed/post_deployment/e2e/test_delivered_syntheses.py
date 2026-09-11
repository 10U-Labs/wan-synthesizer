from __future__ import annotations

import csv
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError

import seed
from seed import DEFAULT_API, _get
from test_published_syntheses import (
    FIBER,
    wan_pop_groups,
    cut_cities,
    offered_diverse_circuits,
    ordered_fiber_miles,
    overbuilt_pairs,
    removable_circuits,
    worst_haul,
)


_ROUNDED_TO = 0.001


def _rounding_slack(synthesis: dict[str, Any]) -> float:
    segments = sum(1 for entry in synthesis["paths"] if entry["link_kind"] == FIBER)
    return (segments + 1) * _ROUNDED_TO / 2


def _tenants_outside(
    syntheses: list[dict[str, Any]],
    allowed: Callable[[float, float, float], bool],
) -> dict[str, tuple[float, float]]:
    measured = {
        synthesis["tenant"]: (
            ordered_fiber_miles(synthesis),
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


def _circuits_clear_of_a_capped_seat(synthesis: dict[str, Any]) -> list[dict[str, Any]]:
    capped = {
        entry["id"]
        for entry in synthesis["status"]["diverse_circuits"]["ceilings"]
        if entry["ceiling"] < 2
    }
    return [
        circuit
        for circuit in synthesis["links"]
        if circuit["source_id"] not in capped and circuit["target_id"] not in capped
    ]


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


def test_every_city_a_tenant_pins_is_seated_in_its_published_backbone(
        published_syntheses: list[dict[str, Any]]) -> None:
    unseated = {
        synthesis["tenant"]: sorted(set(synthesis["forced"]) - _published_cities(synthesis))
        for synthesis in published_syntheses
        if not set(synthesis["forced"]) <= _published_cities(synthesis)
    }
    assert unseated == {}


def test_the_reported_worst_haul_is_the_one_the_published_network_delivers(
        published_syntheses: list[dict[str, Any]]) -> None:
    mismeasured = [
        (synthesis["tenant"], worst_haul(synthesis))
        for synthesis in published_syntheses
        if worst_haul(synthesis) != synthesis["status"]["coverage"]["worst_haul_miles"]
    ]
    assert mismeasured == []


def test_no_synthesis_stopped_short_of_its_target_with_a_seat_left_to_spend(
        published_syntheses: list[dict[str, Any]]) -> None:
    gave_up_early = [
        (synthesis["tenant"], len(synthesis["wan_pops"]), synthesis["seat_cap"])
        for synthesis in published_syntheses
        if not synthesis["status"]["coverage"]["met"]
        and len(synthesis["wan_pops"]) < synthesis["seat_cap"]
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


def test_no_published_network_holds_a_circuit_that_buys_nobody_a_diverse_circuit(
        published_syntheses: list[dict[str, Any]]) -> None:
    spare = {
        synthesis["tenant"]: removable_circuits(synthesis)
        for synthesis in published_syntheses
    }
    assert {tenant: circuits for tenant, circuits in spare.items() if circuits} == {}


def test_no_published_network_is_split_by_the_loss_of_one_city(
        published_syntheses: list[dict[str, Any]]) -> None:
    split = {
        synthesis["tenant"]: cut_cities(_circuits_clear_of_a_capped_seat(synthesis))
        for synthesis in published_syntheses
        if synthesis["number_of_diverse_circuits"] >= 2
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


def _fiber_by_carrier() -> dict[str, set[frozenset[str]]]:
    named = _city_names()
    held: dict[str, set[frozenset[str]]] = {}
    for path in sorted((seed.DATA / seed.FIBER_SEGMENTS).glob("*/*.csv")):
        pairs: set[frozenset[str]] = set()
        with path.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                near = named.get((row["A_Municipality"], row["A_State"]))
                far = named.get((row["Z_Municipality"], row["Z_State"]))
                if near and far:
                    pairs.add(frozenset({near, far}))
        held.setdefault(path.stem, set()).update(pairs)
    return held


def _anybodys_fiber(held: dict[str, set[frozenset[str]]]) -> set[frozenset[str]]:
    everyone: set[frozenset[str]] = set()
    for pairs in held.values():
        everyone |= pairs
    return everyone


def _hops(circuit: dict[str, Any]) -> list[frozenset[str]]:
    cities = circuit.get("path") or []
    return [frozenset({left, right}) for left, right in zip(cities, cities[1:])]


def _circuits_changing_hands(syntheses: list[dict[str, Any]]) -> dict[str, list[str]]:
    held = _fiber_by_carrier()
    anybody = _anybodys_fiber(held)
    found: dict[str, list[str]] = {}
    for synthesis in syntheses:
        for circuit in synthesis["links"]:
            mine = held.get(circuit.get("carrier", ""), set())
            if any(hop in anybody and hop not in mine for hop in _hops(circuit)):
                found.setdefault(synthesis["tenant"], []).append(
                    f"{circuit['source_name']} to {circuit['target_name']}"
                )
    return found


def _circuits_naming_no_carrier(syntheses: list[dict[str, Any]]) -> dict[str, list[str]]:
    anybody = _anybodys_fiber(_fiber_by_carrier())
    found: dict[str, list[str]] = {}
    for synthesis in syntheses:
        for circuit in synthesis["links"]:
            if not circuit.get("carrier") and any(hop in anybody for hop in _hops(circuit)):
                found.setdefault(synthesis["tenant"], []).append(
                    f"{circuit['source_name']} to {circuit['target_name']}"
                )
    return found


def test_no_published_circuit_changes_carrier_partway_along_itself(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert not _circuits_changing_hands(published_syntheses)


def test_every_published_circuit_over_a_carriers_fiber_names_that_carrier(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert not _circuits_naming_no_carrier(published_syntheses)


def _tenants_fiber(synthesis: dict[str, Any]) -> dict[str, set[frozenset[str]]]:
    held = _fiber_by_carrier()
    anybody = _anybodys_fiber(held)
    laid = {
        hop for circuit in synthesis["links"] for hop in _hops(circuit) if hop not in anybody
    }
    return {carrier: pairs | laid for carrier, pairs in held.items()}


def _cities_with_fiber(held: dict[str, set[frozenset[str]]]) -> set[str]:
    return {city for pair in _anybodys_fiber(held) for city in pair}


def _circuits_one_peer_may_end(synthesis: dict[str, Any]) -> int:
    peers = synthesis["seat_cap"] - 1
    asked = synthesis["number_of_diverse_circuits"]
    return max(1, -(-asked // peers)) if peers > 0 else 1


def _overstated_ceilings(syntheses: list[dict[str, Any]]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for synthesis in syntheses:
        held = _tenants_fiber(synthesis)
        reached = _cities_with_fiber(held)
        cities = _published_cities(synthesis)
        per_peer = _circuits_one_peer_may_end(synthesis)
        for entry in synthesis["status"].get("diverse_circuits", {}).get("ceilings", []):
            city = str(entry["name"])
            if city not in reached:
                continue
            offered = offered_diverse_circuits(
                held, city, frozenset(cities - {city}), per_peer
            )
            if int(entry["ceiling"]) > offered:
                found.setdefault(synthesis["tenant"], []).append(
                    f"{city} at {entry['ceiling']} against {offered}"
                )
    return found


def test_no_published_networks_ceiling_is_higher_than_the_circuits_its_carriers_can_offer(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert not _overstated_ceilings(published_syntheses)


def _submarine_pairs(synthesis: dict[str, Any]) -> set[frozenset[str]]:
    return {
        frozenset({entry["source_name"], entry["target_name"]})
        for entry in synthesis["paths"]
        if entry["link_kind"] == FIBER and entry["submarine"]
    }


def _runs_under_water(pops: list[str], under_water: set[frozenset[str]]) -> bool:
    return any(
        frozenset({near, far}) in under_water for near, far in zip(pops, pops[1:])
    )


def _circuits_each_site_holds(synthesis: dict[str, Any]) -> dict[str, list[list[str]]]:
    held: dict[str, list[list[str]]] = {}
    for circuit in synthesis["links"]:
        for end in (circuit["path"][0], circuit["path"][-1]):
            held.setdefault(end, []).append(circuit["path"])
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
