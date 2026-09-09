from __future__ import annotations

import pytest

import fixtures
from synthesizer import linear_program
from synthesizer.graphs import adjacency_by_carrier
from synthesizer.model import SynthesisArtifacts
from synthesizer.survivable import FiberInputs, select_fiber

_SITES = ("w", "x", "y", "z")
_ASKED_FOR = 2
_SEGMENTS = {
    ("w", "x"): 100.0, ("x", "y"): 100.0, ("y", "z"): 100.0, ("z", "w"): 100.0,
    ("w", "y"): 250.0, ("x", "z"): 250.0,
}
ARTIFACTS = fixtures.synthesis_over_segments(_SITES, _SEGMENTS, _ASKED_FOR)
_MESH = fixtures.mesh_circuits(ARTIFACTS)


def test_the_delivered_synthesis_orders_the_four_hundred_miles_the_ring_costs() -> None:
    assert ARTIFACTS.synthesis.metrics.physical_miles == 400.0


def test_the_delivered_synthesis_draws_one_circuit_a_pair_round_the_ring() -> None:
    assert sum(drawn_circuit.distance_miles for drawn_circuit in _MESH) == 400.0


def test_the_delivered_synthesis_publishes_the_floor_it_is_judged_against() -> None:
    assert round(ARTIFACTS.synthesis.metrics.backbone_lower_bound_miles, 3) == 400.0


def test_the_delivered_synthesis_runs_no_further_than_twice_that_floor() -> None:
    assert (
        ARTIFACTS.synthesis.metrics.physical_miles
        <= 2 * ARTIFACTS.synthesis.metrics.backbone_lower_bound_miles
    )


def test_every_site_still_holds_the_two_ways_out_it_was_owed() -> None:
    assert ARTIFACTS.validation["backbone_mesh_independence_deficient"] == []


def _many_pass_artifacts() -> SynthesisArtifacts:
    return fixtures.synthesis_over_segments(
        fixtures.MANY_PASS_SITES,
        fixtures.MANY_PASS_SEGMENTS,
        _ASKED_FOR,
        transit_ids=fixtures.MANY_PASS_TRANSIT,
    )


MANY_PASS_ARTIFACTS = _many_pass_artifacts()


def test_a_synthesis_whose_search_takes_many_passes_orders_the_fewest_miles_there_are() -> None:
    assert MANY_PASS_ARTIFACTS.synthesis.metrics.physical_miles == fixtures.MANY_PASS_MILES


def test_that_synthesis_orders_exactly_the_floor_it_publishes_rather_than_twice_it() -> None:
    assert MANY_PASS_ARTIFACTS.synthesis.metrics.physical_miles == pytest.approx(
        MANY_PASS_ARTIFACTS.synthesis.metrics.backbone_lower_bound_miles
    )


def test_every_seat_on_that_synthesis_holds_the_two_ways_out_it_was_owed() -> None:
    assert MANY_PASS_ARTIFACTS.validation["backbone_mesh_independence_deficient"] == []


def test_that_synthesis_is_the_same_synthesis_when_every_pass_of_its_search_gives_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(linear_program, "_SECONDS_A_PASS_MAY_RUN", 0.0)
    assert _many_pass_artifacts().synthesis.metrics.physical_miles == fixtures.MANY_PASS_MILES


_SPLIT_SITES = ("w", "x")
_SPLIT_TRANSIT = ("p", "q")
_SPLIT_SEGMENTS: dict[tuple[str, str], tuple[float, tuple[str, ...]]] = {
    ("w", "p"): (100.0, ("lumen",)),
    ("p", "x"): (100.0, ("lumen",)),
    ("w", "q"): (150.0, ("zayo",)),
    ("q", "x"): (150.0, ("lumen",)),
}
SPLIT_ARTIFACTS = fixtures.synthesis_over_owned_fiber(
    _SPLIT_SITES, _SPLIT_SEGMENTS, _ASKED_FOR, _SPLIT_TRANSIT
)
SPLIT_ASKED_ONE_ARTIFACTS = fixtures.synthesis_over_owned_fiber(
    _SPLIT_SITES, _SPLIT_SEGMENTS, 1, _SPLIT_TRANSIT
)
_SLACK = 1e-6


def test_no_synthesis_runs_fewer_miles_than_the_floor_it_publishes() -> None:
    assert SPLIT_ARTIFACTS.synthesis.metrics.physical_miles >= (
        SPLIT_ARTIFACTS.synthesis.metrics.backbone_lower_bound_miles - _SLACK
    )


def test_a_site_whose_ways_out_are_split_between_carriers_is_floored_at_what_it_can_buy(
) -> None:
    assert SPLIT_ARTIFACTS.synthesis.metrics.backbone_lower_bound_miles == pytest.approx(
        SPLIT_ASKED_ONE_ARTIFACTS.synthesis.metrics.backbone_lower_bound_miles
    )


OFFERED_ARTIFACTS = fixtures.synthesis_over_owned_fiber(
    fixtures.OFFERED_WAYS_SITES,
    fixtures.OFFERED_WAYS_SEGMENTS,
    _ASKED_FOR,
    fixtures.OFFERED_WAYS_TRANSIT,
)


def _fiber_the_selection_holds() -> frozenset[tuple[str, str]]:
    return select_fiber(FiberInputs(
        fixtures.OFFERED_WAYS_SITES, fixtures.OFFERED_WAYS_FIBER,
        _ASKED_FOR, len(fixtures.OFFERED_WAYS_SITES),
        adjacency_by_carrier(fixtures.OFFERED_WAYS_FIBER),
    )).segments


def test_the_delivered_synthesis_orders_only_fiber_selected_for_it() -> None:
    assert set(OFFERED_ARTIFACTS.synthesis.fiber_segment_keys) <= _fiber_the_selection_holds()


SHORT_AND_LONG_ARTIFACTS = fixtures.synthesis_over_segments(
    fixtures.SHORT_AND_LONG_SITES,
    fixtures.SHORT_AND_LONG_SEGMENTS,
    _ASKED_FOR,
    fixtures.SHORT_AND_LONG_TRANSIT,
)


def test_the_delivered_synthesis_holds_the_shorter_of_two_ways_round() -> None:
    assert not set(
        SHORT_AND_LONG_ARTIFACTS.synthesis.fiber_segment_keys
    ) & fixtures.THE_LONG_WAY


def _floor_sits_under_the_miles_run(artifacts: SynthesisArtifacts) -> bool:
    return artifacts.synthesis.metrics.physical_miles >= (
        artifacts.synthesis.metrics.backbone_lower_bound_miles - _SLACK
    )


_SHARED_HOP_SITES = ("w", "x")
_SHARED_HOP_TRANSIT = ("p", "q", "r")
_SHARED_HOP_SEGMENTS: dict[tuple[str, str], tuple[float, tuple[str, ...]]] = {
    ("w", "p"): (100.0, ("lumen", "zayo")),
    ("p", "x"): (100.0, ("lumen", "zayo")),
    ("w", "q"): (100.0, ("lumen",)),
    ("q", "x"): (100.0, ("lumen",)),
    ("w", "r"): (400.0, ("zayo",)),
    ("r", "x"): (400.0, ("zayo",)),
}
SHARED_HOP_ARTIFACTS = fixtures.synthesis_over_owned_fiber(
    _SHARED_HOP_SITES, _SHARED_HOP_SEGMENTS, _ASKED_FOR, _SHARED_HOP_TRANSIT
)


def test_a_first_hop_both_carriers_own_is_not_floored_above_the_miles_run() -> None:
    assert _floor_sits_under_the_miles_run(SHARED_HOP_ARTIFACTS)


_HANDOVER_SITES = ("w", "x")
_HANDOVER_TRANSIT = ("p", "q", "r")
_HANDOVER_SEGMENTS: dict[tuple[str, str], tuple[float, tuple[str, ...]]] = {
    ("w", "p"): (100.0, ("lumen",)),
    ("p", "x"): (100.0, ("lumen",)),
    ("w", "q"): (100.0, ("lumen",)),
    ("q", "x"): (100.0, ("lumen",)),
    ("w", "r"): (400.0, ("lumen", "zayo")),
    ("r", "x"): (400.0, ("zayo",)),
}
HANDOVER_ARTIFACTS = fixtures.synthesis_over_owned_fiber(
    _HANDOVER_SITES, _HANDOVER_SEGMENTS, _ASKED_FOR, _HANDOVER_TRANSIT
)


def test_a_second_carriers_way_round_is_not_floored_above_the_miles_run() -> None:
    assert _floor_sits_under_the_miles_run(HANDOVER_ARTIFACTS)


_SPURRED_SITES = ("a", "b", "c")
_SPURRED_TRANSIT = ("t", "u")
_SPURRED_SEGMENTS = {
    ("a", "b"): 10.0, ("b", "c"): 10.0, ("a", "c"): 10.0,
    ("a", "t"): 500.0, ("t", "c"): 500.0,
    ("b", "u"): 500.0, ("u", "c"): 500.0,
}
SPURRED_ARTIFACTS = fixtures.synthesis_over_segments(
    _SPURRED_SITES, _SPURRED_SEGMENTS, _ASKED_FOR, _SPURRED_TRANSIT
)


def test_three_seats_over_long_spurs_are_not_floored_above_the_miles_run() -> None:
    assert _floor_sits_under_the_miles_run(SPURRED_ARTIFACTS)


_CHORDED_SITES = ("a", "b", "c", "d")
_CHORDED_SEGMENTS = {
    ("a", "b"): 10.0, ("b", "c"): 10.0, ("c", "d"): 10.0, ("d", "a"): 10.0,
    ("a", "c"): 1000.0, ("b", "d"): 1000.0,
}
CHORDED_ARTIFACTS = fixtures.synthesis_over_segments(
    _CHORDED_SITES, _CHORDED_SEGMENTS, _ASKED_FOR
)


def test_four_seats_over_long_chords_are_not_floored_above_the_miles_run() -> None:
    assert _floor_sits_under_the_miles_run(CHORDED_ARTIFACTS)


_STARRED_SITES = ("a", "b", "c")
_STARRED_TRANSIT = ("t",)
_STARRED_SEGMENTS: dict[tuple[str, str], tuple[float, tuple[str, ...]]] = {
    ("a", "b"): (10.0, ("lumen",)),
    ("b", "c"): (10.0, ("lumen",)),
    ("a", "c"): (10.0, ("lumen",)),
    ("a", "t"): (400.0, ("zayo",)),
    ("b", "t"): (400.0, ("zayo",)),
    ("c", "t"): (400.0, ("zayo",)),
}
STARRED_ARTIFACTS = fixtures.synthesis_over_owned_fiber(
    _STARRED_SITES, _STARRED_SEGMENTS, _ASKED_FOR, _STARRED_TRANSIT
)


def test_three_seats_a_second_carrier_stars_are_not_floored_above_the_miles_run() -> None:
    assert _floor_sits_under_the_miles_run(STARRED_ARTIFACTS)
