from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from itertools import combinations

from synthesizer.ceiling import (
    CircuitProofInputs,
    circuits_per_peer,
    diverse_circuits_by_peer,
)
from synthesizer.flow_cuts import Separation, SeparationQuestion, weakest_separation
from synthesizer.graphs import build_adjacency, reachable_over
from synthesizer.input_graph import FiberSegment
from synthesizer.linear_program import GrowingSegmentProgram, SegmentRow, SegmentSelection

_HELD_OUTRIGHT = 0.5

_TOLERANCE = 1e-6

_EVERY_WAY_OUT: int | None = None

_CIRCUITS_SHARING_NO_POP = 2


@dataclass(frozen=True)
class FiberInputs:
    wan_pop_ids: tuple[str, ...]
    fiber_segments: Mapping[tuple[str, str], FiberSegment]
    number_of_diverse_circuits: int = 3
    max_wan_pop_count: int | None = None


@dataclass(frozen=True)
class FiberSelection:
    segments: frozenset[tuple[str, str]]
    lower_bound_miles: float


@dataclass(frozen=True)
class _Requirement:
    site: str
    peers: frozenset[str]
    spared: frozenset[str]
    required: int
    over: frozenset[tuple[str, str]]


@dataclass(frozen=True)
class _Writing:
    inputs: FiberInputs
    fiber: Mapping[tuple[str, str], float]
    whole: Mapping[tuple[str, str], float]
    per_peer: int
    credited: Mapping[str, Mapping[str, int]]
    land: frozenset[tuple[str, str]]
    land_reach: Mapping[str, frozenset[str]]


@dataclass(frozen=True)
class _DiverseCircuits:
    toward_each: list[_Requirement]
    together: list[_Requirement]
    sparing_every_peer: list[_Requirement]


@dataclass
class _Search:
    order: list[tuple[str, str]]
    column: dict[tuple[str, str], int]
    program: GrowingSegmentProgram
    written: set[tuple[tuple[int, ...], float]]
    selected: frozenset[tuple[str, str]]


def _question(
    requirement: _Requirement, held: Mapping[tuple[str, str], float]
) -> SeparationQuestion:
    return SeparationQuestion(
        requirement.site,
        requirement.peers,
        requirement.spared,
        {segment: share for segment, share in held.items() if segment in requirement.over},
    )


def _carried(requirement: _Requirement, whole: Mapping[tuple[str, str], float]) -> int:
    required = requirement.required
    while required > 0 and weakest_separation(_question(requirement, whole), required):
        required -= 1
    return required


def _shared_out(owed: int, capacity: Mapping[str, int]) -> dict[str, int]:
    shares: dict[str, int] = {}
    left = owed
    for bucket, able in sorted(capacity.items(), key=lambda entry: (-entry[1], entry[0])):
        shares[bucket] = min(able, left)
        left -= shares[bucket]
    return shares


def _lowered(
    rows: list[_Requirement], whole: Mapping[tuple[str, str], float]
) -> list[_Requirement]:
    carried = [replace(row, required=_carried(row, whole)) for row in rows]
    return [row for row in carried if row.required]


def _over_land(
    site: str,
    peers: frozenset[str],
    over: frozenset[tuple[str, str]],
    writing: _Writing,
) -> frozenset[tuple[str, str]]:
    if peers & writing.land_reach.get(site, frozenset()):
        return over & writing.land
    return over


def _peer_fiber(
    site: str, writing: _Writing, capacity: Mapping[str, int]
) -> dict[str, frozenset[tuple[str, str]]]:
    return {
        peer: _over_land(site, frozenset({peer}), frozenset(writing.fiber), writing)
        for peer in capacity
    }


def _together(
    site: str,
    spared: frozenset[str],
    capacity: Mapping[str, int],
    peer_fiber: Mapping[str, frozenset[tuple[str, str]]],
    writing: _Writing,
) -> list[_Requirement]:
    return _lowered(
        [
            _Requirement(
                site,
                frozenset(capacity),
                spared,
                min(writing.inputs.number_of_diverse_circuits, sum(capacity.values())),
                frozenset[tuple[str, str]]().union(*peer_fiber.values()),
            )
        ],
        writing.whole,
    )


def _sparing_every_peer(
    site: str,
    peers: frozenset[str],
    capacity: Mapping[str, int],
    writing: _Writing,
) -> list[_Requirement]:
    return _lowered(
        [
            _Requirement(
                site,
                peers,
                frozenset({site}) | peers,
                min(writing.inputs.number_of_diverse_circuits, sum(capacity.values())),
                _over_land(site, peers, frozenset(writing.fiber), writing),
            )
        ],
        writing.whole,
    )


def _diverse_circuit_rows(site: str, writing: _Writing) -> _DiverseCircuits:
    peers = frozenset(writing.inputs.wan_pop_ids) - {site}
    spared = frozenset({site}) if writing.per_peer == 1 else frozenset({site}) | peers
    capacity = writing.credited[site]
    peer_fiber = _peer_fiber(site, writing, capacity)
    toward_each = _lowered(
        [
            _Requirement(site, frozenset({peer}), spared, share, peer_fiber[peer])
            for peer, share in _shared_out(
                writing.inputs.number_of_diverse_circuits, capacity
            ).items()
            if share
        ],
        writing.whole,
    )
    return _DiverseCircuits(
        toward_each,
        _together(site, spared, capacity, peer_fiber, writing),
        _sparing_every_peer(site, peers, capacity, writing),
    )


def _two_circuits_sharing_no_pop(writing: _Writing) -> list[_Requirement]:
    if writing.inputs.number_of_diverse_circuits < _CIRCUITS_SHARING_NO_POP:
        return []
    asked = [
        _Requirement(
            near,
            frozenset({far}),
            frozenset({near, far}),
            _CIRCUITS_SHARING_NO_POP,
            _over_land(near, frozenset({far}), frozenset(writing.fiber), writing),
        )
        for near, far in combinations(sorted(writing.inputs.wan_pop_ids), 2)
    ]
    return asked if asked == _lowered(asked, writing.whole) else []


def _writing(
    inputs: FiberInputs, fiber: Mapping[tuple[str, str], float], most: int | None
) -> _Writing:
    on_land = {
        key: segment
        for key, segment in inputs.fiber_segments.items()
        if not segment.submarine
    }
    terrestrial = build_adjacency(on_land)
    return _Writing(
        inputs,
        fiber,
        {segment: 1.0 for segment in fiber},
        circuits_per_peer(
            inputs.max_wan_pop_count, len(inputs.wan_pop_ids), inputs.number_of_diverse_circuits
        ),
        diverse_circuits_by_peer(
            CircuitProofInputs(
                inputs.wan_pop_ids,
                build_adjacency(dict(inputs.fiber_segments)),
                inputs.number_of_diverse_circuits,
                inputs.max_wan_pop_count,
                terrestrial,
            ),
            most,
        ),
        frozenset(segment for segment in fiber if segment in on_land),
        reachable_over(terrestrial),
    )


def _asked_of_every_wan_pop(writing: _Writing) -> list[_Requirement]:
    owed_rows = [_diverse_circuit_rows(site, writing) for site in writing.inputs.wan_pop_ids]
    return [
        row
        for owed in owed_rows
        for row in owed.toward_each + owed.together + owed.sparing_every_peer
    ]


def _shortfalls(
    requirements: list[_Requirement], held: Mapping[tuple[str, str], float]
) -> list[tuple[Separation, int]]:
    found: list[tuple[Separation, int]] = []
    for requirement in requirements:
        separation = weakest_separation(_question(requirement, held), requirement.required)
        if separation is not None:
            found.append((separation, requirement.required))
    return found


def _rows(
    shortfalls: list[tuple[Separation, int]], column: Mapping[tuple[str, str], int]
) -> list[SegmentRow]:
    return [
        SegmentRow(
            tuple(sorted(column[segment] for segment in separation.crossing_segments)),
            float(required - len(separation.lost_cities)),
        )
        for separation, required in shortfalls
    ]


def _held(
    fiber: Mapping[tuple[str, str], float], selected: frozenset[tuple[str, str]]
) -> dict[tuple[str, str], float]:
    return {segment: 1.0 if segment in selected else 0.0 for segment in fiber}


def _shares(
    selection: SegmentSelection, order: list[tuple[str, str]]
) -> dict[tuple[str, str], float]:
    return dict(zip(order, selection.held))


def _write(search: _Search, rows: list[SegmentRow]) -> bool:
    fresh = []
    for row in rows:
        already = (row.columns, row.floor)
        if already not in search.written:
            search.written.add(already)
            fresh.append(row)
    search.program.add_rows(tuple(fresh))
    return bool(fresh)


def _solve_search(search: _Search) -> SegmentSelection:
    search.program.hold_whole(
        frozenset(search.column[segment] for segment in search.selected)
    )
    return search.program.solve()


def _tighten(search: _Search, requirements: list[_Requirement]) -> SegmentSelection:
    selection = _solve_search(search)
    shortfalls = _shortfalls(requirements, _shares(selection, search.order))
    while shortfalls and _write(search, _rows(shortfalls, search.column)):
        selection = _solve_search(search)
        shortfalls = _shortfalls(requirements, _shares(selection, search.order))
    return selection


def _round_up(search: _Search, selection: SegmentSelection) -> frozenset[tuple[str, str]]:
    shares = _shares(selection, search.order)
    left = [
        (share, segment) for segment, share in shares.items() if segment not in search.selected
    ]
    fresh = frozenset(
        segment for share, segment in left if share >= _HELD_OUTRIGHT - _TOLERANCE
    )
    return fresh or frozenset({max(left)[1]})


def _search_over(
    fiber: Mapping[tuple[str, str], float], order: list[tuple[str, str]]
) -> _Search:
    return _Search(
        order,
        {segment: index for index, segment in enumerate(order)},
        GrowingSegmentProgram(tuple(fiber[segment] for segment in order)),
        set(),
        frozenset(),
    )


def _floor_under_every_requirement(
    inputs: FiberInputs,
    fiber: Mapping[tuple[str, str], float],
    order: list[tuple[str, str]],
) -> float:
    writing = _writing(inputs, fiber, inputs.number_of_diverse_circuits)
    return _tighten(
        _search_over(fiber, order),
        _asked_of_every_wan_pop(writing) + _two_circuits_sharing_no_pop(writing),
    ).miles


def select_fiber(inputs: FiberInputs) -> FiberSelection:
    fiber = {
        key: segment.distance_miles for key, segment in inputs.fiber_segments.items()
    }
    if not fiber:
        return FiberSelection(frozenset(), 0.0)
    requirements = _asked_of_every_wan_pop(_writing(inputs, fiber, _EVERY_WAY_OUT))
    order = sorted(fiber)
    search = _search_over(fiber, order)
    while True:
        shortfalls = _shortfalls(requirements, _held(fiber, search.selected))
        if not shortfalls:
            break
        _write(search, _rows(shortfalls, search.column))
        search.selected |= _round_up(search, _tighten(search, requirements))
    return FiberSelection(
        search.selected,
        _floor_under_every_requirement(inputs, fiber, order),
    )
