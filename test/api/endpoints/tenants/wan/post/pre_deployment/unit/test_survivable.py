from __future__ import annotations

import pytest

import fixtures
from synthesizer.ceiling import CircuitProofInputs, diverse_circuit_ceilings
from synthesizer.graphs import adjacency_by_carrier, build_adjacency
from synthesizer.input_graph import FiberSegment
from synthesizer.survivable import (
    FiberInputs,
    FiberSelection,
    _EVERY_WAY_OUT,
    _Requirement,
    _asked_of_every_node,
    _carried,
    _held,
    _shortfalls,
    _diverse_circuit_rows,
    _writing,
    select_fiber,
)

physical = fixtures.fiber_segments_from

_DIVERSE_CIRCUITS = 2
_SLACK = 1e-6


def _asking(
    fiber: dict[tuple[str, str], FiberSegment],
    backbone_ids: tuple[str, ...],
    seat_cap: int | None = None,
    number_of_diverse_circuits: int = _DIVERSE_CIRCUITS,
) -> FiberInputs:
    return FiberInputs(
        backbone_ids, fiber, number_of_diverse_circuits, seat_cap, adjacency_by_carrier(fiber),
    )


def _selected(
    fiber: dict[tuple[str, str], FiberSegment],
    backbone_ids: tuple[str, ...],
    seat_cap: int | None = None,
    number_of_diverse_circuits: int = _DIVERSE_CIRCUITS,
) -> FiberSelection:
    return select_fiber(_asking(fiber, backbone_ids, seat_cap, number_of_diverse_circuits))


def _owed(
    fiber: dict[tuple[str, str], FiberSegment],
    backbone_ids: tuple[str, ...],
    site: str,
    seat_cap: int | None = None,
) -> int:
    inputs = _asking(fiber, backbone_ids, seat_cap)
    miles_by_key = _whole(inputs)
    return sum(
        row.required
        for row in _diverse_circuit_rows(
            site, _writing(inputs, miles_by_key, _EVERY_WAY_OUT)
        ).across_the_carriers
    )


def _whole(inputs: FiberInputs) -> dict[tuple[str, str], float]:
    return {
        key: segment.distance_miles for key, segment in inputs.fiber_segments.items()
    }


def _selected_miles(
    selection: FiberSelection, fiber: dict[tuple[str, str], FiberSegment]
) -> float:
    return sum(fiber[key].distance_miles for key in selection.segments)


_CROSSING_SITES = ("eug", "hil", "sea")
_OVERLAND = frozenset({("eug", "pdx"), ("hil", "pdx"), ("pdx", "sea")})
_UNDER_WATER_SELECTION = _selected(fixtures.CROSSING_SUBMARINE_FIBER, _CROSSING_SITES)


def test_no_submarine_fiber_is_selected_where_a_way_round_over_land_exists() -> None:
    assert _UNDER_WATER_SELECTION.segments == _OVERLAND


_NO_FIBER = _selected(physical({}), ("a", "b"))
_NO_SITES = _selected(physical({("a", "b"): 1.0}), ())


def test_a_backbone_with_no_fiber_at_all_buys_nothing_and_is_floored_at_nothing() -> None:
    assert _NO_FIBER == FiberSelection(frozenset(), 0.0)


def test_a_backbone_with_no_sites_selects_none_of_the_fiber_in_front_of_it() -> None:
    assert not _NO_SITES.segments


def test_a_backbone_with_no_sites_is_floored_at_nothing_rather_than_at_what_is_on_offer() -> None:
    assert _NO_SITES.lower_bound_miles == pytest.approx(0.0)


_RING_PAIRS = {("a", "b"): 1.0, ("b", "c"): 1.0, ("c", "d"): 1.0, ("a", "d"): 1.0}
_RING_SITES = ("a", "b", "c", "d")
_RING_SEGMENTS = frozenset(_RING_PAIRS)
_RING = physical(_RING_PAIRS)
_CHORD = physical({**_RING_PAIRS, ("a", "c"): 10.0})
_RING_SELECTION = _selected(_RING, _RING_SITES)
_CHORD_SELECTION = _selected(_CHORD, _RING_SITES)


def test_a_ring_is_selected_whole_because_nothing_short_of_it_gives_two_diverse_circuits() -> None:
    assert _RING_SELECTION.segments == _RING_SEGMENTS


def test_the_floor_under_the_ring_is_the_mileage_of_the_ring_itself() -> None:
    assert _RING_SELECTION.lower_bound_miles == pytest.approx(4.0)


def test_fiber_no_requirement_turns_on_is_left_where_it_is() -> None:
    assert _CHORD_SELECTION.segments == _RING_SEGMENTS


_CHAIN = physical({("a", "b"): 1.0, ("b", "c"): 1.0})
_CHAIN_SELECTION = _selected(_CHAIN, ("a", "b", "c"))


def test_a_site_behind_a_single_point_of_failure_is_asked_for_what_its_fiber_can_carry() -> None:
    assert _CHAIN_SELECTION.segments == frozenset(_CHAIN)


_PAIR_PRICED = physical({
    ("a", "b"): 20.0, ("b", "e"): 22.0,
    ("a", "f"): 32.0, ("b", "f"): 32.0,
    ("b", "g"): 32.0, ("e", "g"): 32.0,
})
_PAIR_PRICED_SELECTION = _selected(_PAIR_PRICED, ("a", "b", "e"))


def test_no_fiber_is_selected_for_a_circuit_no_backbone_node_is_owed() -> None:
    assert _PAIR_PRICED_SELECTION.segments == frozenset({("a", "b"), ("b", "e")})


def test_the_floor_prices_the_diverse_circuits_owed_and_nothing_between_a_pair() -> None:
    assert _PAIR_PRICED_SELECTION.lower_bound_miles == pytest.approx(42.0)


_ASKED_TWO_OVER_ONE = _Requirement(
    "a", frozenset({"b"}), frozenset({"a"}), _DIVERSE_CIRCUITS, frozenset({("a", "b")})
)


def test_a_requirement_is_lowered_to_the_circuits_the_whole_fiber_can_carry() -> None:
    assert _carried(_ASKED_TWO_OVER_ONE, {("a", "b"): 1.0}) == 1


_UNDER_WATER_PAIRS = {
    ("a", "p"): 10.0, ("b", "p"): 10.0, ("a", "q"): 20.0, ("b", "q"): 20.0,
}
_UNDER_WATER_ONLY = fixtures.fiber_segments_under_water(
    _UNDER_WATER_PAIRS, set(_UNDER_WATER_PAIRS)
)
_UNDER_WATER_ONLY_SELECTION = _selected(_UNDER_WATER_ONLY, ("a", "b"), seat_cap=2)


def test_submarine_fiber_is_selected_where_a_peer_is_reachable_no_other_way() -> None:
    assert _UNDER_WATER_ONLY_SELECTION.segments == frozenset(_UNDER_WATER_ONLY)


_TWIN_WAYS = physical({
    ("a", "p"): 1.0, ("b", "p"): 1.0, ("a", "q"): 1.0, ("b", "q"): 1.0,
})
_TWIN_SELECTION = _selected(_TWIN_WAYS, ("a", "b"), seat_cap=2)


def test_a_pair_allowed_two_ways_between_them_is_given_both_ways_round() -> None:
    assert _TWIN_SELECTION.segments == frozenset(_TWIN_WAYS)


_TWIN_SPLIT = fixtures.carrier_fiber_segments({
    ("a", "p"): (1.0, ("zayo",)),
    ("b", "p"): (1.0, ("zayo",)),
    ("a", "q"): (1.0, ("zayo",)),
    ("b", "q"): (1.0, ("lumen",)),
})
_TWIN_OWNED = fixtures.carrier_fiber_segments({
    ("a", "p"): (1.0, ("zayo",)),
    ("b", "p"): (1.0, ("zayo",)),
    ("a", "q"): (1.0, ("lumen",)),
    ("b", "q"): (1.0, ("lumen",)),
})
_TWIN_SPLIT_SELECTION = _selected(_TWIN_SPLIT, ("a", "b"), seat_cap=2)
_TWIN_SPLIT_ASKED_ONE = _selected(_TWIN_SPLIT, ("a", "b"), seat_cap=2, number_of_diverse_circuits=1)


def test_a_site_is_owed_only_the_diverse_circuits_one_carrier_can_offer() -> None:
    assert _owed(_TWIN_SPLIT, ("a", "b"), "a", seat_cap=2) == 1


def test_a_site_is_owed_both_diverse_circuits_where_one_carrier_has_each() -> None:
    assert _owed(_TWIN_OWNED, ("a", "b"), "a", seat_cap=2) == 2


def test_fiber_nobody_owns_is_owed_to_every_carrier() -> None:
    assert _owed(_TWIN_WAYS, ("a", "b"), "a", seat_cap=2) == 2


def test_the_floor_is_measured_over_the_requirements_the_build_is_held_to() -> None:
    assert _TWIN_SPLIT_SELECTION.lower_bound_miles == pytest.approx(
        _TWIN_SPLIT_ASKED_ONE.lower_bound_miles
    )


_SHARED_TRANSIT_SELECTION = _selected(
    fixtures.SHARED_TRANSIT_FIBER, fixtures.SHARED_TRANSIT_SITES, seat_cap=2
)


def _shared_transit_ceilings(segments: frozenset[tuple[str, str]]) -> dict[str, int]:
    held = {segment: fixtures.SHARED_TRANSIT_FIBER[segment] for segment in segments}
    return diverse_circuit_ceilings(CircuitProofInputs(
        fixtures.SHARED_TRANSIT_SITES,
        build_adjacency(held),
        _DIVERSE_CIRCUITS,
        2,
        adjacency_by_carrier(held),
    ))


def test_the_fiber_selected_where_two_carriers_share_a_pop_carries_both_diverse_circuits() -> None:
    assert _shared_transit_ceilings(_SHARED_TRANSIT_SELECTION.segments) == {"a": 2, "b": 2}


def test_the_floor_prices_the_way_round_the_pop_two_carriers_share() -> None:
    assert _SHARED_TRANSIT_SELECTION.lower_bound_miles >= (
        fixtures.SHARED_TRANSIT_MILES - _SLACK
    )


_TWO_TRIANGLES = physical({
    ("a", "b"): 1.0, ("b", "c"): 1.0, ("a", "c"): 1.0,
    ("d", "e"): 1.0, ("e", "f"): 1.0, ("d", "f"): 1.0,
    ("c", "d"): 1.0,
})
_TRIANGLE_SITES = ("a", "b", "c", "d", "e", "f")
_TRIANGLES_SELECTION = _selected(_TWO_TRIANGLES, _TRIANGLE_SITES)


def test_the_segment_the_first_answer_missed_is_selected_once_it_is_written_down() -> None:
    assert ("c", "d") in _TRIANGLES_SELECTION.segments


_OFFERED = frozenset({("a", "r"), ("b", "r")})


def test_the_fiber_selected_is_fiber_one_carrier_can_offer_a_whole_circuit_over() -> None:
    assert _selected(
        fixtures.OFFERED_WAYS_FIBER, fixtures.OFFERED_WAYS_SITES, seat_cap=2
    ).segments == _OFFERED


_DISTANT_PEER_SITES = ("hil", "sea", "syd")
_DISTANT_PEER_SELECTION = select_fiber(FiberInputs(
    _DISTANT_PEER_SITES, fixtures.DISTANT_PEER_FIBER, _DIVERSE_CIRCUITS, None,
    adjacency_by_carrier(fixtures.DISTANT_PEER_FIBER),
))


def _distant_peer_ceilings(segments: frozenset[tuple[str, str]]) -> dict[str, int]:
    return diverse_circuit_ceilings(CircuitProofInputs(
        _DISTANT_PEER_SITES,
        build_adjacency({
            segment: fixtures.DISTANT_PEER_FIBER[segment] for segment in segments
        }),
        _DIVERSE_CIRCUITS,
    ))


def test_the_fiber_selected_for_a_site_carries_every_way_out_its_fiber_carries() -> None:
    assert _distant_peer_ceilings(_DISTANT_PEER_SELECTION.segments) == _distant_peer_ceilings(
        frozenset(fixtures.DISTANT_PEER_FIBER)
    ) == {"hil": 2, "sea": 2, "syd": 2}


_MANY_PASS = physical(fixtures.MANY_PASS_SEGMENTS)
_MANY_PASS_INPUTS = _asking(_MANY_PASS, fixtures.MANY_PASS_SITES)
_MANY_PASS_SELECTION = _selected(_MANY_PASS, fixtures.MANY_PASS_SITES)
_MANY_PASS_FIBER = _whole(_MANY_PASS_INPUTS)


def test_a_search_that_runs_long_enough_buys_the_shortest_synthesis_there_is() -> None:
    assert _selected_miles(_MANY_PASS_SELECTION, _MANY_PASS) == pytest.approx(
        _MANY_PASS_SELECTION.lower_bound_miles
    )


def test_the_fiber_a_long_search_settles_on_meets_every_requirement_asked_of_it() -> None:
    assert not _shortfalls(
        _asked_of_every_node(_writing(_MANY_PASS_INPUTS, _MANY_PASS_FIBER, _EVERY_WAY_OUT)),
        _held(_MANY_PASS_FIBER, _MANY_PASS_SELECTION.segments),
    )


_CASES: tuple[tuple[str, FiberSelection, dict[tuple[str, str], FiberSegment]], ...] = (
    ("ring", _RING_SELECTION, _RING),
    ("ring and chord", _CHORD_SELECTION, _CHORD),
    ("chain", _CHAIN_SELECTION, _CHAIN),
    ("two triangles", _TRIANGLES_SELECTION, _TWO_TRIANGLES),
    ("pair with two ways round", _TWIN_SELECTION, _TWIN_WAYS),
    ("pair whose second way round changes hands", _TWIN_SPLIT_SELECTION, _TWIN_SPLIT),
    ("twelve cities and five seats", _MANY_PASS_SELECTION, _MANY_PASS),
)


def test_no_selection_is_floored_above_the_fiber_it_actually_holds() -> None:
    assert [
        name
        for name, selection, fiber in _CASES
        if selection.lower_bound_miles > _selected_miles(selection, fiber) + _SLACK
    ] == []


_SHORT_AND_LONG_SELECTION = _selected(
    fixtures.SHORT_AND_LONG_FIBER, fixtures.SHORT_AND_LONG_SITES
)
_ONLY_LONG_SELECTION = _selected(fixtures.ONLY_LONG_FIBER, fixtures.SHORT_AND_LONG_SITES)


def test_the_shorter_of_two_ways_round_is_the_one_selected() -> None:
    assert not _SHORT_AND_LONG_SELECTION.segments & fixtures.THE_LONG_WAY


def test_the_only_way_round_there_is_gets_selected_however_far_it_runs() -> None:
    assert fixtures.THE_LONG_WAY <= _ONLY_LONG_SELECTION.segments


_ALREADY_NEEDED_SELECTION = _selected(
    fixtures.ALREADY_NEEDED_FIBER, fixtures.ALREADY_NEEDED_SITES
)


def test_the_floor_prices_the_fiber_the_rest_of_the_wan_already_needs() -> None:
    assert _ALREADY_NEEDED_SELECTION.lower_bound_miles == pytest.approx(
        fixtures.ALREADY_NEEDED_MILES
    )


def test_no_fiber_is_selected_for_the_carrier_of_a_nodes_shortest_circuit_alone() -> None:
    assert not _ALREADY_NEEDED_SELECTION.segments & fixtures.THE_SHORTEST_CREDIT_ALONE


_ON_ONE_POP = {
    ("a", "b"): 10.0, ("a", "p"): 10.0, ("b", "p"): 10.0,
    ("c", "d"): 10.0, ("c", "p"): 10.0, ("d", "p"): 10.0,
}
_PAST_THE_POP = {**_ON_ONE_POP, ("a", "c"): 200.0}
_ON_ONE_POP_SITES = ("a", "b", "c", "d")
_HELD_AT_ONE_POP = _selected(physical(_ON_ONE_POP), _ON_ONE_POP_SITES)
_PAST_THE_POP_SELECTION = _selected(physical(_PAST_THE_POP), _ON_ONE_POP_SITES)
_PAST_THE_POP_ASKED_ONE = _selected(
    physical(_PAST_THE_POP), _ON_ONE_POP_SITES, number_of_diverse_circuits=1
)


def test_the_floor_prices_the_circuits_that_keep_one_pop_from_splitting_the_wan() -> None:
    assert _PAST_THE_POP_SELECTION.lower_bound_miles == pytest.approx(240.0)


def test_no_such_circuit_is_priced_over_fiber_that_offers_no_way_past_the_pop() -> None:
    assert _HELD_AT_ONE_POP.lower_bound_miles == pytest.approx(60.0)


def test_a_backbone_asked_for_one_circuit_is_priced_no_way_past_any_pop() -> None:
    assert _PAST_THE_POP_ASKED_ONE.lower_bound_miles == pytest.approx(30.0)


def test_the_fiber_selected_holds_none_of_the_circuits_only_a_lost_pop_calls_for() -> None:
    assert _PAST_THE_POP_SELECTION.segments == frozenset(physical(_ON_ONE_POP))


_ONE_CIRCUIT_SEAT = {**_PAST_THE_POP, ("d", "m"): 5.0}
_ONE_CIRCUIT_SEAT_SELECTION = _selected(
    physical(_ONE_CIRCUIT_SEAT), (*_ON_ONE_POP_SITES, "m")
)


def test_a_seat_the_carriers_can_give_one_circuit_leaves_the_rest_still_priced() -> None:
    assert _ONE_CIRCUIT_SEAT_SELECTION.lower_bound_miles == pytest.approx(245.0)
