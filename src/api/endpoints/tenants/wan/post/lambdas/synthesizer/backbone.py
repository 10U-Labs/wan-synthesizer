from __future__ import annotations

import math
from dataclasses import dataclass, replace
from itertools import combinations

from synthesizer.ceiling import CircuitProofInputs, independent_circuits
from synthesizer.input_graph import FiberSegment, carriers_along, segment_key
from synthesizer.graphs import (
    adjacency_by_carrier,
    articulation_points,
    build_adjacency,
    connected_components,
    dijkstra,
    fiber_segments_along,
    reachable_over,
    reconstruct_path,
    undirected_adjacency,
)
from synthesizer.model import (
    CIRCUIT_FOR_PIN,
    CIRCUIT_FOR_RELIEF,
    CIRCUIT_FOR_TARGET,
    SynthesisCircuit,
)
from synthesizer.survivable import FiberInputs, select_fiber
from synthesizer.validation import diverse_circuit_count


def miles_along(
    pop_ids: tuple[str, ...],
    fiber_segments: dict[tuple[str, str], FiberSegment],
) -> float:
    return sum(
        fiber_segments[segment_key(pop_ids[index], pop_ids[index + 1])].distance_miles
        for index in range(len(pop_ids) - 1)
    )


@dataclass(frozen=True)
class BackboneConstraints:
    removed_pairs: frozenset[tuple[str, str]] = frozenset()
    number_of_diverse_circuits: int = 3
    forced_pairs: frozenset[tuple[str, str]] = frozenset()
    seat_cap: int | None = None


@dataclass(frozen=True)
class BackboneMesh:
    circuits: list[SynthesisCircuit]
    lower_bound_miles: float


@dataclass(frozen=True)
class _DrawnFiber:
    backbone_ids: tuple[str, ...]
    distances: dict[str, dict[str, float]]
    selected: dict[tuple[str, str], FiberSegment]
    selected_by_carrier: dict[str, dict[str, list[tuple[str, float]]]]
    whole: dict[tuple[str, str], FiberSegment]
    constraints: BackboneConstraints


def _fiber_of(circuits: list[SynthesisCircuit]) -> tuple[set[str], set[tuple[str, str]]]:
    segments: set[tuple[str, str]] = set()
    for drawn_circuit in circuits:
        segments |= fiber_segments_along(drawn_circuit.pop_ids)
    return {city for segment in segments for city in segment}, segments


def _one_network(circuits: list[SynthesisCircuit], backbone_ids: tuple[str, ...]) -> bool:
    cities, segments = _fiber_of(circuits)
    return len(connected_components(cities | set(backbone_ids), segments)) == 1


def _cut_cities(
    circuits: list[SynthesisCircuit], backbone_ids: tuple[str, ...]
) -> set[str]:
    cities, segments = _fiber_of(circuits)
    return articulation_points(cities | set(backbone_ids), segments)


def _pieces_without_each(
    circuits: list[SynthesisCircuit], backbone_ids: tuple[str, ...]
) -> dict[str, int]:
    cities, segments = _fiber_of(circuits)
    sites = cities | set(backbone_ids)
    return {
        lost: len(connected_components(sites - {lost}, segments))
        for lost in sorted(sites)
    }


def _pinned_circuit(
    pair: tuple[str, str],
    by_carrier: dict[str, dict[str, list[tuple[str, float]]]],
    fiber_segments: dict[tuple[str, str], FiberSegment],
) -> SynthesisCircuit | None:
    near, far = pair
    maps = by_carrier or {"": build_adjacency(fiber_segments)}
    drawn: list[tuple[str, ...]] = []
    for _carrier, adjacency in sorted(maps.items()):
        _distances, predecessors = dijkstra(adjacency, near)
        pop_ids = reconstruct_path(near, far, predecessors)
        if pop_ids:
            drawn.append(pop_ids)
    if not drawn:
        return None
    pop_ids = min(drawn, key=lambda one: (miles_along(one, fiber_segments), one))
    return SynthesisCircuit(
        "backbone_mesh", near, far, pop_ids,
        miles_along(pop_ids, fiber_segments), CIRCUIT_FOR_PIN,
        carrier=_carrier_of(pop_ids, fiber_segments),
    )


def _carrier_of(
    pop_ids: tuple[str, ...], fiber_segments: dict[tuple[str, str], FiberSegment]
) -> str:
    owners = carriers_along(pop_ids, fiber_segments)
    return min(owners) if owners else ""


def _proved_over(
    site: str,
    fiber: dict[tuple[str, str], FiberSegment],
    by_carrier: dict[str, dict[str, list[tuple[str, float]]]],
    drawn: _DrawnFiber,
) -> list[tuple[str, ...]]:
    constraints = drawn.constraints
    peers = tuple(
        peer
        for peer in drawn.backbone_ids
        if peer == site or segment_key(site, peer) not in constraints.removed_pairs
    )
    proof = CircuitProofInputs(
        peers, build_adjacency(fiber),
        constraints.number_of_diverse_circuits, constraints.seat_cap, by_carrier,
    )
    return sorted(
        independent_circuits(site, proof),
        key=lambda pop_ids: (miles_along(pop_ids, fiber), pop_ids),
    )[: constraints.number_of_diverse_circuits]


def _ways_out_of(site: str, drawn: _DrawnFiber) -> list[tuple[str, ...]]:
    return _proved_over(site, drawn.selected, drawn.selected_by_carrier, drawn)


def _laid(drawn: _DrawnFiber, pinned: list[SynthesisCircuit]) -> list[SynthesisCircuit]:
    laid: dict[tuple[str, ...], SynthesisCircuit] = {
        min(drawn_circuit.pop_ids, drawn_circuit.pop_ids[::-1]): drawn_circuit
        for drawn_circuit in pinned
    }
    for site in sorted(drawn.backbone_ids):
        for pop_ids in _ways_out_of(site, drawn):
            key = min(pop_ids, pop_ids[::-1])
            held = laid.get(key)
            if held is None:
                laid[key] = SynthesisCircuit(
                    "backbone_mesh", pop_ids[0], pop_ids[-1], pop_ids,
                    miles_along(pop_ids, drawn.whole), CIRCUIT_FOR_TARGET, (site,),
                    _carrier_of(pop_ids, drawn.whole),
                )
            elif held.reason == CIRCUIT_FOR_TARGET and site not in held.requested_by:
                laid[key] = replace(
                    held, requested_by=tuple(sorted((*held.requested_by, site)))
                )
    return [laid[key] for key in sorted(laid)]


def _pairs_across(
    city: str, circuits: list[SynthesisCircuit], drawn: _DrawnFiber
) -> list[tuple[str, str]]:
    cities, segments = _fiber_of(circuits)
    sites = cities | set(drawn.backbone_ids)
    apart = {
        site: index
        for index, piece in enumerate(connected_components(sites - {city}, segments))
        for site in piece
    }
    sides: dict[int, list[str]] = {}
    for site in sorted(set(drawn.backbone_ids) - {city}):
        sides.setdefault(apart[site], []).append(site)
    split = sorted({apart[near] for near in undirected_adjacency(sites, segments)[city]})
    pairs = [
        (near, far)
        for left, right in combinations(split, 2)
        for near in sides.get(left, [])
        for far in sides.get(right, [])
    ]
    return sorted(
        pairs,
        key=lambda ends: (drawn.distances.get(ends[0], {}).get(ends[1], math.inf), ends),
    )


def _on_land(
    fiber: dict[tuple[str, str], FiberSegment]
) -> dict[tuple[str, str], FiberSegment]:
    return {key: segment for key, segment in fiber.items() if not segment.submarine}


def _circuit_around(
    city: str, circuits: list[SynthesisCircuit], drawn: _DrawnFiber
) -> SynthesisCircuit | None:
    fiber = {
        key: segment for key, segment in drawn.whole.items() if city not in key
    }
    by_carrier = adjacency_by_carrier(fiber)
    land = _on_land(fiber)
    land_by_carrier = adjacency_by_carrier(land)
    reach = reachable_over(build_adjacency(_on_land(drawn.whole)))
    for near, far in _pairs_across(city, circuits, drawn):
        joined = far in reach.get(near, frozenset())
        found = _pinned_circuit(
            (near, far),
            land_by_carrier if joined else by_carrier,
            land if joined else fiber,
        )
        if found is None:
            continue
        return replace(found, reason=CIRCUIT_FOR_RELIEF)
    return None


def _relieved(circuits: list[SynthesisCircuit], drawn: _DrawnFiber) -> list[SynthesisCircuit]:
    relieved = list(circuits)
    if drawn.constraints.number_of_diverse_circuits < 2:
        return relieved
    beyond_help: set[str] = set()
    while True:
        cut = sorted(_cut_cities(relieved, drawn.backbone_ids) - beyond_help)
        if not cut:
            return relieved
        added = _circuit_around(cut[0], relieved, drawn)
        if added is None:
            beyond_help.add(cut[0])
            continue
        relieved.append(added)


def _needed(
    circuits: list[SynthesisCircuit], backbone_ids: tuple[str, ...], target: int
) -> list[SynthesisCircuit]:
    kept = list(circuits)
    held = {site: min(target, diverse_circuit_count(kept, site)) for site in backbone_ids}
    apart = _pieces_without_each(kept, backbone_ids)
    for spare in sorted(
        circuits, key=lambda drawn_circuit: (-drawn_circuit.distance_miles, drawn_circuit.pop_ids)
    ):
        if spare.reason == CIRCUIT_FOR_PIN:
            continue
        left = [drawn_circuit for drawn_circuit in kept if drawn_circuit is not spare]
        if any(
            min(target, diverse_circuit_count(left, site)) < held[site] for site in backbone_ids
        ):
            continue
        if not _one_network(left, backbone_ids):
            continue
        if any(
            pieces > apart[lost]
            for lost, pieces in _pieces_without_each(left, backbone_ids).items()
        ):
            continue
        kept = left
    return kept


def _selected_fiber(
    backbone_ids: tuple[str, ...],
    fiber_segments: dict[tuple[str, str], FiberSegment],
    constraints: BackboneConstraints,
    by_carrier: dict[str, dict[str, list[tuple[str, float]]]],
) -> tuple[frozenset[tuple[str, str]], float, list[SynthesisCircuit]]:
    selection = select_fiber(FiberInputs(
        backbone_ids, fiber_segments,
        constraints.number_of_diverse_circuits, constraints.seat_cap,
        by_carrier,
    ))
    drawn = (
        _pinned_circuit(pair, by_carrier, fiber_segments)
        for pair in sorted(constraints.forced_pairs)
    )
    pinned = [drawn_circuit for drawn_circuit in drawn if drawn_circuit is not None]
    segments = set(selection.segments)
    for drawn_circuit in pinned:
        segments |= fiber_segments_along(drawn_circuit.pop_ids)
    return frozenset(segments), selection.lower_bound_miles, pinned


def backbone_mesh(
    backbone_ids: tuple[str, ...],
    all_distances: dict[str, dict[str, float]],
    fiber_segments: dict[tuple[str, str], FiberSegment],
    constraints: BackboneConstraints = BackboneConstraints(),
) -> BackboneMesh:
    whole_by_carrier = adjacency_by_carrier(fiber_segments)
    segments, floor, pinned = _selected_fiber(
        backbone_ids, fiber_segments, constraints, whole_by_carrier
    )
    selected = {segment: fiber_segments[segment] for segment in sorted(segments)}
    drawn = _DrawnFiber(
        backbone_ids, all_distances, selected, adjacency_by_carrier(selected),
        fiber_segments, constraints,
    )
    laid = _relieved(_laid(drawn, pinned), drawn)
    return BackboneMesh(
        _needed(laid, backbone_ids, constraints.number_of_diverse_circuits), floor
    )
