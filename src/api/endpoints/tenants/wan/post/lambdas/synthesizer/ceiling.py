from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

from synthesizer.graphs import reachable_over

_Node = tuple[str, str]
_Residual = dict[_Node, dict[_Node, int]]
_Costs = dict[_Node, dict[_Node, float]]
_Arc = tuple[_Node, _Node, int]
_NewArc = tuple[_Node, _Node, float, int]

_SINK: _Node = ("sink", "")


def _add_capacity(residual: _Residual, costs: _Costs, arc: _NewArc) -> None:
    tail, head, miles, units = arc
    residual.setdefault(tail, {})[head] = units
    residual.setdefault(head, {}).setdefault(tail, 0)
    costs.setdefault(tail, {})[head] = miles
    costs.setdefault(head, {})[tail] = -miles


def _unit_site_network(
    site: str,
    backbone_ids: tuple[str, ...],
    adjacency: dict[str, list[tuple[str, float]]],
    per_peer: int = 1,
) -> tuple[_Residual, _Costs, list[_Arc]]:
    peers = {peer for peer in backbone_ids if peer != site and peer in adjacency}
    termini_only = per_peer > 1
    new_arcs: list[_NewArc] = [
        (("in", city), ("out", city), 0.0, 1)
        for city in adjacency
        if city != site and not (termini_only and city in peers)
    ]
    new_arcs += [
        (("out", city), ("in", neighbor), weight, 1)
        for city, neighbors in adjacency.items()
        for neighbor, weight in neighbors
    ]
    new_arcs += [
        (("in" if termini_only else "out", peer), _SINK, 0.0, per_peer)
        for peer in sorted(peers)
    ]
    residual: _Residual = {}
    costs: _Costs = {}
    for arc in new_arcs:
        _add_capacity(residual, costs, arc)
    return residual, costs, [(tail, head, units) for tail, head, _miles, units in new_arcs]


def _cheapest_runs(
    residual: _Residual,
    costs: _Costs,
    potential: dict[_Node, float],
    source: _Node,
) -> tuple[dict[_Node, float], dict[_Node, _Node | None]]:
    distance: dict[_Node, float] = {source: 0.0}
    reached: dict[_Node, _Node | None] = {source: None}
    settled: set[_Node] = set()
    queue: list[tuple[float, _Node]] = [(0.0, source)]
    while queue:
        spent, tail = heapq.heappop(queue)
        if tail in settled:
            continue
        settled.add(tail)
        for head, capacity in residual.get(tail, {}).items():
            if capacity <= 0 or head in settled:
                continue
            step = spent + costs[tail][head] + potential[tail] - potential[head]
            if head not in distance or step < distance[head]:
                distance[head] = step
                reached[head] = tail
                heapq.heappush(queue, (step, head))
    return distance, reached


def _augmenting_path(
    residual: _Residual,
    costs: _Costs,
    potential: dict[_Node, float],
    source: _Node,
) -> list[_Node] | None:
    distance, reached = _cheapest_runs(residual, costs, potential, source)
    for end, run in distance.items():
        potential[end] += run
    if _SINK not in reached:
        return None
    path = [_SINK]
    cursor = reached[_SINK]
    while cursor is not None:
        path.append(cursor)
        cursor = reached[cursor]
    return path


def _spent_arcs(residual: _Residual, arcs: list[_Arc]) -> dict[_Node, list[_Node]]:
    spent: dict[_Node, list[_Node]] = {}
    for tail, head, units in arcs:
        spent.setdefault(tail, []).extend([head] * (units - residual[tail][head]))
    return spent


def _circuits_through(spent: dict[_Node, list[_Node]], source: _Node) -> list[tuple[str, ...]]:
    circuits: list[tuple[str, ...]] = []
    while spent.get(source):
        cities = [source[1]]
        cursor = spent[source].pop(0)
        while cursor != _SINK:
            side, city = cursor
            if side == "in":
                cities.append(city)
            cursor = spent[cursor].pop(0)
        circuits.append(tuple(cities))
    return circuits


def _fiber_segment_miles(
    adjacency: dict[str, list[tuple[str, float]]], left: str, right: str
) -> float:
    return next(
        (weight for neighbor, weight in adjacency.get(left, []) if neighbor == right),
        math.inf,
    )


def _miles_along(
    pop_ids: tuple[str, ...], adjacency: dict[str, list[tuple[str, float]]]
) -> float:
    return sum(
        _fiber_segment_miles(adjacency, left, right) for left, right in zip(pop_ids, pop_ids[1:])
    )


def _proved_circuits(
    site: str,
    backbone_ids: tuple[str, ...],
    adjacency: dict[str, list[tuple[str, float]]],
    per_peer: int = 1,
) -> list[tuple[str, ...]]:
    residual, costs, arcs = _unit_site_network(site, backbone_ids, adjacency, per_peer)
    source: _Node = ("out", site)
    potential: dict[_Node, float] = {end: 0.0 for end in (source, *residual)}
    while True:
        path = _augmenting_path(residual, costs, potential, source)
        if path is None:
            return _circuits_through(_spent_arcs(residual, arcs), source)
        for head, tail in zip(path, path[1:]):
            residual[tail][head] -= 1
            residual[head][tail] += 1


@dataclass(frozen=True)
class CircuitProofInputs:
    backbone_ids: tuple[str, ...]
    adjacency: dict[str, list[tuple[str, float]]]
    circuits_wanted: int = 1
    seat_cap: int | None = None
    fiber_by_carrier: dict[str, dict[str, list[tuple[str, float]]]] = field(
        default_factory=dict
    )
    terrestrial: dict[str, list[tuple[str, float]]] = field(default_factory=dict)


def circuits_per_peer(seat_cap: int | None, seats: int, circuits_wanted: int) -> int:
    peers = (seat_cap if seat_cap is not None else seats) - 1
    return max(1, -(-circuits_wanted // peers)) if peers > 0 else 1


def _no_city_twice(
    site: str,
    found: list[tuple[str, ...]],
    inputs: CircuitProofInputs,
    per_peer: int,
) -> list[tuple[str, ...]]:
    peers = {peer for peer in inputs.backbone_ids if peer != site}
    termini_only = per_peer > 1
    spent: set[str] = set()
    ends: dict[str, int] = {}
    seen: set[tuple[str, ...]] = set()
    kept: list[tuple[str, ...]] = []
    ordered = sorted(found, key=lambda one: (_miles_along(one, inputs.adjacency), one))
    for pop_ids in ordered:
        if pop_ids in seen:
            continue
        seen.add(pop_ids)
        interior = set(pop_ids[1:-1])
        end = pop_ids[-1]
        if interior & spent or (termini_only and interior & peers):
            continue
        if end in spent or (termini_only and ends.get(end, 0) >= per_peer):
            continue
        spent |= interior
        if termini_only:
            ends[end] = ends.get(end, 0) + 1
        else:
            spent.add(end)
        kept.append(pop_ids)
    return kept


def independent_circuits(site: str, inputs: CircuitProofInputs) -> list[tuple[str, ...]]:
    return [pop_ids for _carrier, pop_ids in _ways_out_and_their_carriers(site, inputs)]


def _peers_over_land(site: str, inputs: CircuitProofInputs) -> frozenset[str]:
    joined = reachable_over(inputs.terrestrial).get(site, frozenset())
    return joined & frozenset(peer for peer in inputs.backbone_ids if peer != site)


def _over_land(
    site: str, inputs: CircuitProofInputs, adjacency: dict[str, list[tuple[str, float]]]
) -> dict[str, list[tuple[str, float]]]:
    if not _peers_over_land(site, inputs):
        return adjacency
    on_land = {
        city: {neighbor for neighbor, _weight in neighbors}
        for city, neighbors in inputs.terrestrial.items()
    }
    kept = {
        city: [
            (neighbor, weight)
            for neighbor, weight in neighbors
            if neighbor in on_land.get(city, frozenset())
        ]
        for city, neighbors in adjacency.items()
    }
    return {city: neighbors for city, neighbors in kept.items() if neighbors}


def _circuits_over_each_carrier(
    site: str, inputs: CircuitProofInputs, per_peer: int
) -> dict[str, list[tuple[str, ...]]]:
    if not inputs.fiber_by_carrier:
        return {
            "": _proved_circuits(
                site,
                inputs.backbone_ids,
                _over_land(site, inputs, inputs.adjacency),
                per_peer,
            )
        }
    return {
        carrier: _proved_circuits(
            site, inputs.backbone_ids, _over_land(site, inputs, adjacency), per_peer
        )
        for carrier, adjacency in sorted(inputs.fiber_by_carrier.items())
        if site in adjacency
    }


def _per_peer(inputs: CircuitProofInputs) -> int:
    return circuits_per_peer(
        inputs.seat_cap, len(inputs.backbone_ids), inputs.circuits_wanted
    )


def _kept_with_their_carriers(
    site: str,
    inputs: CircuitProofInputs,
    by_carrier: dict[str, list[tuple[str, ...]]],
    per_peer: int,
) -> list[tuple[str, tuple[str, ...]]]:
    offered_by: dict[tuple[str, ...], str] = {}
    for carrier, circuits in sorted(by_carrier.items()):
        for pop_ids in circuits:
            offered_by.setdefault(pop_ids, carrier)
    if not inputs.fiber_by_carrier:
        return [("", pop_ids) for pop_ids in by_carrier[""]]
    found = [pop_ids for _carrier, circuits in sorted(by_carrier.items()) for pop_ids in circuits]
    return [
        (offered_by[pop_ids], pop_ids)
        for pop_ids in _no_city_twice(site, found, inputs, per_peer)
    ]


def _ways_out_and_their_carriers(
    site: str, inputs: CircuitProofInputs
) -> list[tuple[str, tuple[str, ...]]]:
    per_peer = _per_peer(inputs)
    return _kept_with_their_carriers(
        site, inputs, _circuits_over_each_carrier(site, inputs, per_peer), per_peer
    )


def ways_out_by_carrier_and_peer(
    site: str, inputs: CircuitProofInputs
) -> dict[tuple[str, str], int]:
    per_peer = _per_peer(inputs)
    by_carrier = _circuits_over_each_carrier(site, inputs, per_peer)
    counted: dict[tuple[str, str], int] = {}
    for carrier, pop_ids in _kept_with_their_carriers(site, inputs, by_carrier, per_peer):
        counted[(carrier, pop_ids[-1])] = counted.get((carrier, pop_ids[-1]), 0) + 1
    return counted


def independent_circuit_ceiling(site: str, inputs: CircuitProofInputs) -> int:
    return len(independent_circuits(site, inputs))


def diverse_circuit_ceilings(inputs: CircuitProofInputs) -> dict[str, int]:
    return {
        site: independent_circuit_ceiling(site, inputs)
        for site in inputs.backbone_ids
        if site in inputs.adjacency
    }
