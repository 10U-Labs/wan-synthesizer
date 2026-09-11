from __future__ import annotations

import json
from collections import deque
from itertools import combinations
from typing import Any
from urllib.error import HTTPError

from seed import _get
from synthesizer.input_graph import Site, haversine_miles


UNFINISHED = frozenset({"creating", "synthesizing"})

COLLECTIONS = (
    "wan-pops",
    "backbone-circuits",
    "tenant-nodes",
    "provider-nodes",
    "homing-circuits",
    "fiber-segments",
)


def request_paths(tenant: str) -> list[str]:
    return [f"tenants/{tenant}/{name}" for name in ("wan", *COLLECTIONS)]


def _build_state(api: str, path: str) -> dict[str, Any]:
    try:
        state: dict[str, Any] = _get(api, path)
    except HTTPError as refusal:
        state = json.loads(refusal.read())
    return state


def published_synthesis(api: str, tenant: str, config: dict[str, Any]) -> dict[str, Any]:
    state_path, *collection_paths = request_paths(tenant)
    state = _build_state(api, state_path)
    published: dict[str, Any] = (
        {path.rsplit("/", 1)[-1]: _get(api, path) for path in collection_paths}
        if state.get("status") == "success" else {}
    )
    backbone = config["backbone"]
    return {
        "tenant": tenant,
        "target_miles": backbone["coverage_target_miles"],
        "number_of_diverse_circuits": backbone["number_of_diverse_circuits"],
        "homing_degree": config["homing"]["degree"],
        "seat_cap": backbone["wan_pop_count"]["max"],
        "forced": backbone.get("forced", {}).get("wan_pops", []),
        "forced_paths": backbone.get("forced", {}).get("paths", []),
        "status": state,
        "lower_bound_miles": state.get("backbone_lower_bound_miles"),
        "wan_pops": published.get("wan-pops", []),
        "demand": published.get("tenant-nodes", []) + published.get("provider-nodes", []),
        "circuits": published.get("backbone-circuits", []),
        "homings": published.get("homing-circuits", []),
        "fiber": published.get("fiber-segments", []),
    }


def settled(status: dict[str, Any]) -> bool:
    return status.get("status") not in UNFINISHED


def site_from_row(row: dict[str, Any]) -> Site:
    latitude, longitude = row["coords"]
    return Site(row["id"], row["name"], row["kind"], (latitude, longitude))


def worst_haul(synthesis: dict[str, Any]) -> float:
    wan_pop_sites = [site_from_row(row) for row in synthesis["wan_pops"]]
    hauls: list[float] = [
        min(haversine_miles(site_from_row(row), site) for site in wan_pop_sites)
        for row in synthesis["demand"]
        if not row["exempt_from_distance_constraint"]
    ]
    return round(max(hauls, default=0.0), 1)


def _circuits_out_of(
    circuits: list[dict[str, Any]], site: str, names: dict[str, str]
) -> list[tuple[str, frozenset[str]]]:
    return [
        (
            names[circuit["target_id"] if circuit["source_id"] == site else circuit["source_id"]],
            frozenset(circuit["route"]) - {names[site]},
        )
        for circuit in circuits
        if site in (circuit["source_id"], circuit["target_id"])
    ]


def _fail_apart(circuits: tuple[tuple[str, frozenset[str]], ...]) -> bool:
    return all(
        not ((near & far) - ({peer} if peer == other else frozenset()))
        for (peer, near), (other, far) in combinations(circuits, 2)
    )


def diverse_circuit_count(
    circuits: list[dict[str, Any]], site: str, names: dict[str, str]
) -> int:
    out_of_site = _circuits_out_of(circuits, site, names)
    return max(
        (
            size
            for size in range(1, len(out_of_site) + 1)
            if any(_fail_apart(combo) for combo in combinations(out_of_site, size))
        ),
        default=0,
    )


def overbuilt_pairs(synthesis: dict[str, Any]) -> list[tuple[str, int]]:
    drawn: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for drawn_circuit in synthesis["circuits"]:
        pair = tuple(sorted((drawn_circuit["source_id"], drawn_circuit["target_id"])))
        drawn.setdefault(pair, []).append(drawn_circuit)
    names = {row["id"]: row["name"] for row in synthesis["wan_pops"]}
    asked = synthesis["number_of_diverse_circuits"]
    apart = pieces_without_each(synthesis["circuits"])
    overbuilt: list[tuple[str, int]] = []
    for pair, circuits in sorted(drawn.items()):
        if len(circuits) < 2:
            continue
        spare = max(circuits, key=lambda circuit: circuit["distance_miles"])
        kept = [circuit for circuit in synthesis["circuits"] if circuit is not spare]
        if _cuts_deeper(kept, apart):
            continue
        if not any(
            diverse_circuit_count(kept, end, names)
            < min(asked, diverse_circuit_count(synthesis["circuits"], end, names))
            for end in pair
        ):
            overbuilt.append((" <-> ".join(pair), len(circuits)))
    return overbuilt


def _joined_to(pairs: list[tuple[str, str]]) -> dict[str, set[str]]:
    joined: dict[str, set[str]] = {}
    for near, far in pairs:
        joined.setdefault(near, set()).add(far)
        joined.setdefault(far, set()).add(near)
    return joined


def _reached(joined: dict[str, set[str]], start: str) -> set[str]:
    found = {start}
    unswept = [start]
    while unswept:
        here = unswept.pop()
        for there in joined[here] - found:
            found.add(there)
            unswept.append(there)
    return found


def _all_one_network(joined: dict[str, set[str]]) -> bool:
    return all(_reached(joined, start) == set(joined) for start in sorted(joined)[:1])


def _pieces(joined: dict[str, set[str]]) -> int:
    unplaced = set(joined)
    counted = 0
    while unplaced:
        unplaced -= _reached(joined, min(unplaced))
        counted += 1
    return counted


def pieces_without_each(circuits: list[dict[str, Any]]) -> dict[str, int]:
    joined = _cities_the_circuits_cross(circuits)
    return {
        lost: _pieces({
            city: reached - {lost} for city, reached in joined.items() if city != lost
        })
        for lost in joined
    }


def _cuts_deeper(
    kept: list[dict[str, Any]], apart: dict[str, int]
) -> bool:
    return any(
        pieces > apart[lost] for lost, pieces in pieces_without_each(kept).items()
    )


def cut_cities(circuits: list[dict[str, Any]]) -> list[str]:
    joined = _cities_the_circuits_cross(circuits)
    if not _all_one_network(joined):
        return []
    return sorted(
        lost
        for lost in joined
        if not _all_one_network({
            city: reached - {lost} for city, reached in joined.items() if city != lost
        })
    )


def _sites_the_circuits_join(
    circuits: list[dict[str, Any]], sites: list[str]
) -> dict[str, set[str]]:
    alone: dict[str, set[str]] = {site: set() for site in sites}
    return alone | _joined_to(
        [(circuit["source_id"], circuit["target_id"]) for circuit in circuits]
    )


def _cities_the_circuits_cross(circuits: list[dict[str, Any]]) -> dict[str, set[str]]:
    return _joined_to([
        (near, far)
        for circuit in circuits
        for near, far in zip(circuit["route"], circuit["route"][1:])
    ])


def removable_circuits(synthesis: dict[str, Any]) -> list[tuple[str, float]]:
    names = {row["id"]: row["name"] for row in synthesis["wan_pops"]}
    sites = list(names)
    asked = synthesis["number_of_diverse_circuits"]
    pinned = {
        frozenset((pair["source"], pair["target"])) for pair in synthesis["forced_paths"]
    }
    held_diverse_circuits = {
        site: min(asked, diverse_circuit_count(synthesis["circuits"], site, names))
        for site in sites
    }
    apart = pieces_without_each(synthesis["circuits"])
    removable: list[tuple[str, float]] = []
    for spare in synthesis["circuits"]:
        if frozenset((names[spare["source_id"]], names[spare["target_id"]])) in pinned:
            continue
        kept = [circuit for circuit in synthesis["circuits"] if circuit is not spare]
        if any(
            diverse_circuit_count(kept, site, names) < held_diverse_circuits[site] for site in sites
        ):
            continue
        if not _all_one_network(_sites_the_circuits_join(kept, sites)):
            continue
        if _cuts_deeper(kept, apart):
            continue
        removable.append((" -> ".join(spare["route"]), spare["distance_miles"]))
    return sorted(removable, key=lambda found: (-found[1], found[0]))


def _published_fiber(synthesis: dict[str, Any]) -> dict[str, dict[str, float]]:
    fiber: dict[str, dict[str, float]] = {}
    for entry in synthesis["fiber"]:
        fiber.setdefault(entry["source_id"], {})[entry["target_id"]] = entry["distance_miles"]
        fiber.setdefault(entry["target_id"], {})[entry["source_id"]] = entry["distance_miles"]
    return fiber


def wan_pop_groups(synthesis: dict[str, Any]) -> list[list[str]]:
    fiber = _published_fiber(synthesis)
    joined: dict[str, set[str]] = {row["id"]: set() for row in synthesis["wan_pops"]}
    joined |= {city: set(neighbors) for city, neighbors in fiber.items()}
    unplaced = {row["id"] for row in synthesis["wan_pops"]}
    groups: list[list[str]] = []
    while unplaced:
        reached = _reached(joined, min(unplaced))
        groups.append(sorted(unplaced & reached))
        unplaced -= reached
    return groups


def fiber_miles_run_over(synthesis: dict[str, Any]) -> float:
    segments: list[float] = [entry["distance_miles"] for entry in synthesis["fiber"]]
    return sum(segments)


_ARRIVING = "into "
_LEAVING = "out of "
_SINK = "a peer"


def _joined_by(pairs: set[frozenset[str]]) -> dict[str, set[str]]:
    ends = [sorted(pair) for pair in pairs if len(pair) == 2]
    return _joined_to([(both[0], both[1]) for both in ends])


def _capacity(
    joined: dict[str, set[str]], city: str, peers: frozenset[str], per_peer: int
) -> dict[str, dict[str, int]]:
    plenty = len(peers) * per_peer + 1
    left: dict[str, dict[str, int]] = {
        _ARRIVING + place: {_LEAVING + place: plenty if place in peers else 1}
        for place in joined
        if place != city
    }
    for place, neighbours in joined.items():
        left[_LEAVING + place] = {_ARRIVING + neighbour: 1 for neighbour in neighbours}
    for peer in peers:
        if peer in joined:
            left[_LEAVING + peer][_SINK] = per_peer
    left[_SINK] = {}
    for tail, heads in list(left.items()):
        for head in heads:
            left.setdefault(head, {}).setdefault(tail, 0)
    return left


def _walk_to_a_peer(
    left: dict[str, dict[str, int]], source: str
) -> dict[str, str] | None:
    came: dict[str, str] = {source: source}
    queue: deque[str] = deque([source])
    while queue:
        tail = queue.popleft()
        for head, spare in left[tail].items():
            if spare > 0 and head not in came:
                came[head] = tail
                if head == _SINK:
                    return came
                queue.append(head)
    return None


def _offered_over(
    joined: dict[str, set[str]], city: str, peers: frozenset[str], per_peer: int
) -> int:
    left = _capacity(joined, city, peers, per_peer)
    source = _LEAVING + city
    if source not in left:
        return 0
    offered = 0
    came = _walk_to_a_peer(left, source)
    while came is not None:
        head = _SINK
        while head != source:
            tail = came[head]
            left[tail][head] -= 1
            left[head][tail] += 1
            head = tail
        offered += 1
        came = _walk_to_a_peer(left, source)
    return offered


def offered_diverse_circuits(
    fiber_by_carrier: dict[str, set[frozenset[str]]],
    city: str,
    peers: frozenset[str],
    per_peer: int,
) -> int:
    return min(
        sum(
            _offered_over(_joined_by(pairs), city, peers, per_peer)
            for pairs in fiber_by_carrier.values()
        ),
        len(peers) * per_peer,
    )
