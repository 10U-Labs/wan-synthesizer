from __future__ import annotations

import fixtures
from synthesizer.input_graph import FiberSegment, segment_key
from synthesizer.model import PATH_FOR_PIN, PATH_FOR_TARGET, SynthesisPath
from synthesizer.backbone import (
    BackboneConstraints,
    BackboneMesh,
    _needed,
    backbone_mesh,
    path_geometry_miles,
)
from synthesizer.survivable import FiberInputs, select_fiber
from synthesizer.synthesize import all_pairs_shortest
from synthesizer.graphs import (
    adjacency_by_carrier,
    articulation_points,
    build_adjacency,
    path_segment_keys,
)

pop = fixtures.carrier_pop
physical = fixtures.fiber_segments_from


def _distances(
    fiber: dict[tuple[str, str], FiberSegment],
) -> dict[str, dict[str, float]]:
    cities = sorted({city for pair in fiber for city in pair})
    distances, _predecessors = all_pairs_shortest(
        [pop(city) for city in cities], build_adjacency(fiber)
    )
    return distances


def _drawn(
    sites: tuple[str, ...],
    fiber: dict[tuple[str, str], FiberSegment],
    constraints: BackboneConstraints,
) -> BackboneMesh:
    return backbone_mesh(sites, _distances(fiber), fiber, constraints)


def _selected(
    fiber: dict[tuple[str, str], FiberSegment],
    sites: tuple[str, ...],
    constraints: BackboneConstraints,
) -> frozenset[tuple[str, str]]:
    return select_fiber(FiberInputs(
        sites, fiber, constraints.number_of_diverse_paths,
        constraints.seat_cap, adjacency_by_carrier(fiber),
    )).segments


def _asking(asked_for: int = 2) -> BackboneConstraints:
    return BackboneConstraints(number_of_diverse_paths=asked_for, seat_cap=4)


def _pairs(mesh: BackboneMesh) -> set[tuple[str, str]]:
    return {segment_key(drawn_path.source, drawn_path.target) for drawn_path in mesh.paths}


def _mesh_miles(mesh: BackboneMesh) -> float:
    return sum(drawn_path.distance_miles for drawn_path in mesh.paths)


def _cut(mesh: BackboneMesh) -> set[str]:
    segments = {key for drawn_path in mesh.paths for key in path_segment_keys(drawn_path.path)}
    return articulation_points({city for pair in segments for city in pair}, segments)


def _joining(mesh: BackboneMesh, left: str, right: str) -> SynthesisPath:
    return next(
        drawn_path
        for drawn_path in mesh.paths
        if segment_key(drawn_path.source, drawn_path.target) == segment_key(left, right)
    )


_SQUARE_SITES = ("w", "x", "y", "z")
_SQUARE_FIBER = physical({
    ("w", "x"): 100.0, ("x", "y"): 100.0, ("y", "z"): 100.0, ("z", "w"): 100.0,
    ("w", "y"): 250.0, ("x", "z"): 250.0,
})
_TWO_WAYS_OUT = BackboneConstraints(number_of_diverse_paths=2, seat_cap=4)
_SQUARE = _drawn(_SQUARE_SITES, _SQUARE_FIBER, _TWO_WAYS_OUT)


def test_the_square_is_drawn_with_one_path_a_pair_round_the_ring() -> None:
    assert _pairs(_SQUARE) == {
        segment_key("w", "x"), segment_key("x", "y"), segment_key("y", "z"), segment_key("z", "w"),
    }


def test_the_square_selects_neither_of_the_chords() -> None:
    assert _SQUARE_FIBER.keys() - {
        segment_key(*pair)
        for drawn_path in _SQUARE.paths
        for pair in zip(drawn_path.path, drawn_path.path[1:])
    } == {segment_key("w", "y"), segment_key("x", "z")}


def test_the_square_runs_the_fewest_miles_its_fiber_allows() -> None:
    assert _mesh_miles(_SQUARE) == 400.0


def test_the_square_publishes_the_floor_it_was_judged_against() -> None:
    assert round(_SQUARE.lower_bound_miles, 3) == 400.0


def test_the_square_runs_no_further_than_twice_the_floor() -> None:
    assert _mesh_miles(_SQUARE) <= 2 * _SQUARE.lower_bound_miles


def test_every_path_the_square_draws_says_a_site_reached_for_it() -> None:
    assert {drawn_path.reason for drawn_path in _SQUARE.paths} == {PATH_FOR_TARGET}


def test_a_path_names_both_of_the_sites_that_reached_for_it() -> None:
    assert _joining(_SQUARE, "w", "x").requested_by == ("w", "x")


def test_no_path_the_square_holds_could_be_taken_back_out() -> None:
    assert _needed(_SQUARE.paths, _SQUARE_SITES, 2) == _SQUARE.paths


_EGRESS_SITES = ("hub", "p", "q")
_EGRESS_FIBER = physical({
    ("hub", "m"): 10.0, ("m", "p"): 10.0, ("m", "q"): 10.0,
    ("hub", "n"): 11.0, ("n", "q"): 11.0, ("p", "q"): 10.0,
})
_EGRESS = _drawn(_EGRESS_SITES, _EGRESS_FIBER, BackboneConstraints(
    number_of_diverse_paths=2, seat_cap=3,
))


def test_the_longer_way_round_a_shared_city_is_the_one_drawn() -> None:
    assert ("hub", "n", "q") in {drawn_path.path for drawn_path in _EGRESS.paths}


def test_the_shorter_way_round_that_shared_city_is_not_selected_at_all() -> None:
    assert segment_key("m", "q") not in {
        segment_key(*pair)
        for drawn_path in _EGRESS.paths
        for pair in zip(drawn_path.path, drawn_path.path[1:])
    }


def test_the_shared_egress_graph_joins_all_three_pairs_once() -> None:
    assert len(_EGRESS.paths) == 3


def test_the_shared_egress_synthesis_runs_the_miles_its_five_segments_cost() -> None:
    assert _mesh_miles(_EGRESS) == 52.0


def test_no_path_the_shared_egress_synthesis_holds_could_be_taken_back_out() -> None:
    assert _needed(_EGRESS.paths, _EGRESS_SITES, 2) == _EGRESS.paths


_LOBE_SITES = ("a", "b", "c", "d")
_LOBE_LOBES: dict[tuple[str, str], tuple[float, tuple[str, ...]]] = {
    ("a", "b"): (10.0, ("lumen",)),
    ("a", "mid"): (15.0, ("lumen",)),
    ("b", "mid"): (5.0, ("lumen",)),
    ("c", "d"): (10.0, ("lumen",)),
    ("c", "mid"): (5.0, ("lumen",)),
    ("d", "mid"): (15.0, ("lumen",)),
}
_LOBE_FIBER = fixtures.carrier_fiber_segments({
    **_LOBE_LOBES, ("b", "w"): (20.0, ("zayo",)), ("w", "c"): (20.0, ("zayo",)),
})
_TWO_LOBES = _drawn(_LOBE_SITES, _LOBE_FIBER, _asking())
_BOWTIE_FIBER = fixtures.carrier_fiber_segments(_LOBE_LOBES)
_BOWTIE = _drawn(_LOBE_SITES, _BOWTIE_FIBER, _asking())
_ONE_WAY_OUT_LOBES = _drawn(_LOBE_SITES, _LOBE_FIBER, _asking(1))


def test_a_city_every_drawn_path_crosses_is_given_a_way_round_it() -> None:
    assert _cut(_TWO_LOBES) == set()


def test_the_path_drawn_round_that_city_is_one_company_can_offer() -> None:
    assert [
        drawn_path.carrier
        for drawn_path in _TWO_LOBES.paths
        if segment_key("b", "w") in path_segment_keys(drawn_path.path)
    ] == ["zayo"]


def test_a_city_no_fiber_goes_round_still_leaves_every_seat_its_paths() -> None:
    assert {
        end for drawn_path in _BOWTIE.paths for end in (drawn_path.source, drawn_path.target)
    } == set(_LOBE_SITES)


def test_a_tenant_that_asked_for_one_way_out_is_not_given_a_way_round_anything() -> None:
    assert [
        drawn_path.path
        for drawn_path in _ONE_WAY_OUT_LOBES.paths
        if segment_key("b", "w") in path_segment_keys(drawn_path.path)
    ] == []


_OFFERED_TERMS = BackboneConstraints(number_of_diverse_paths=2, seat_cap=2)
_OFFERED_MESH = _drawn(
    fixtures.OFFERED_WAYS_SITES, fixtures.OFFERED_WAYS_FIBER, _OFFERED_TERMS
)


def _run_over(mesh: BackboneMesh) -> set[tuple[str, str]]:
    return {key for drawn_path in mesh.paths for key in path_segment_keys(drawn_path.path)}


def test_a_site_is_drawn_over_fiber_one_carrier_could_offer_it() -> None:
    assert _run_over(_OFFERED_MESH) <= _selected(
        fixtures.OFFERED_WAYS_FIBER, fixtures.OFFERED_WAYS_SITES, _OFFERED_TERMS
    )


_PRUNED = _drawn(_SQUARE_SITES, _SQUARE_FIBER, BackboneConstraints(
    removed_pairs=frozenset({segment_key("w", "x")}), number_of_diverse_paths=2, seat_cap=4,
))
_PINNED_CHORD = _drawn(_SQUARE_SITES, _SQUARE_FIBER, BackboneConstraints(
    number_of_diverse_paths=2, forced_pairs=frozenset({segment_key("w", "y")}), seat_cap=4,
))
_PINNED_SEGMENT = _drawn(_SQUARE_SITES, _SQUARE_FIBER, BackboneConstraints(
    number_of_diverse_paths=2, forced_pairs=frozenset({segment_key("w", "x")}), seat_cap=4,
))


def test_a_pruned_pair_is_never_joined_by_a_drawn_path() -> None:
    assert segment_key("w", "x") not in _pairs(_PRUNED)


def test_a_pruned_pair_leaves_the_rest_of_the_backbone_drawn() -> None:
    assert segment_key("y", "z") in _pairs(_PRUNED)


def test_a_pinned_pair_is_joined_however_the_fiber_was_selected() -> None:
    assert segment_key("w", "y") in _pairs(_PINNED_CHORD)


def test_a_pinned_path_says_the_operator_is_what_put_it_there() -> None:
    assert _joining(_PINNED_CHORD, "w", "y").reason == PATH_FOR_PIN


def test_a_pinned_path_is_never_taken_back_out_as_unneeded() -> None:
    assert len(_PINNED_CHORD.paths) == 5


def test_a_pin_over_fiber_the_synthesis_would_have_selected_anyway_is_still_a_pin() -> None:
    assert _joining(_PINNED_SEGMENT, "w", "x").reason == PATH_FOR_PIN


_ISLANDS = physical({("a", "b"): 1.0, ("c", "d"): 1.0})
_ISLAND_PIN = _drawn(("a", "c"), _ISLANDS, BackboneConstraints(
    forced_pairs=frozenset({segment_key("a", "c")}),
))


def test_a_backbone_the_fiber_never_joins_is_drawn_with_no_paths() -> None:
    assert not _ISLAND_PIN.paths


def test_a_backbone_the_fiber_never_joins_is_floored_at_nothing() -> None:
    assert _ISLAND_PIN.lower_bound_miles == 0.0


def test_a_site_the_fiber_does_not_carry_costs_the_others_nothing() -> None:
    fiber = physical({("a", "b"): 1.0})
    mesh = _drawn(("a", "b", "zed"), fiber, BackboneConstraints(number_of_diverse_paths=1))
    assert _pairs(mesh) == {segment_key("a", "b")}


def test_path_geometry_miles_adds_up_the_segments_a_path_crosses() -> None:
    assert path_geometry_miles(("w", "x", "y"), _SQUARE_FIBER) == 200.0


def _use(source: str, target: str, path: tuple[str, ...], miles: float) -> SynthesisPath:
    return SynthesisPath("backbone_mesh", source, target, path, miles)


_RING_PLUS_CHORD = [
    _use("w", "x", ("w", "x"), 100.0),
    _use("x", "y", ("x", "y"), 100.0),
    _use("y", "z", ("y", "z"), 100.0),
    _use("z", "w", ("z", "w"), 100.0),
    _use("w", "y", ("w", "y"), 250.0),
]
_TRIANGLE = [
    _use("a", "b", ("a", "b"), 1.0),
    _use("b", "c", ("b", "c"), 1.0),
    _use("a", "c", ("a", "c"), 1.0),
]
_CHAIN = [
    _use("a", "b", ("a", "b"), 1.0),
    _use("b", "c", ("b", "c"), 1.0),
    _use("c", "d", ("c", "d"), 1.0),
]


def test_a_path_nobody_needs_is_taken_back_out() -> None:
    assert _needed(_RING_PLUS_CHORD, _SQUARE_SITES, 2) == _RING_PLUS_CHORD[:4]


def test_a_path_a_site_would_lose_a_way_out_by_is_kept() -> None:
    assert _needed(_RING_PLUS_CHORD[:4], _SQUARE_SITES, 2) == _RING_PLUS_CHORD[:4]


def test_a_path_whose_loss_would_leave_a_city_carrying_the_network_is_kept() -> None:
    assert _needed(_TRIANGLE, ("a", "b", "c"), 1) == _TRIANGLE


def test_a_path_whose_loss_would_break_the_backbone_in_two_is_kept() -> None:
    assert _needed(_CHAIN, ("a", "b", "c", "d"), 1) == _CHAIN


def test_a_synthesis_that_never_survived_a_city_loss_is_not_held_to_surviving_one() -> None:
    doubled = [*_CHAIN, _use("a", "b", ("a", "b"), 9.0)]
    assert _needed(doubled, ("a", "b", "c", "d"), 1) == _CHAIN


_SPLIT_SQUARE = fixtures.carrier_fiber_segments({
    ("w", "x"): (100.0, ("lumen",)),
    ("x", "y"): (100.0, ("zayo",)),
    ("w", "z"): (100.0, ("lumen",)),
    ("z", "y"): (100.0, ("zayo",)),
})
_WHOLE_SQUARE = fixtures.carrier_fiber_segments({
    ("w", "x"): (100.0, ("lumen",)),
    ("x", "y"): (100.0, ("lumen",)),
    ("w", "z"): (100.0, ("zayo",)),
    ("z", "y"): (100.0, ("zayo",)),
})
_PIN_WY = BackboneConstraints(
    number_of_diverse_paths=2, forced_pairs=frozenset({segment_key("w", "y")}), seat_cap=4,
)


def test_a_pin_no_carrier_can_join_draws_no_path() -> None:
    mesh = _drawn(("w", "x", "y", "z"), _SPLIT_SQUARE, _PIN_WY)
    assert not [drawn_path for drawn_path in mesh.paths if drawn_path.reason == PATH_FOR_PIN]


def test_a_pin_one_carrier_can_join_is_drawn_over_that_carriers_fiber() -> None:
    mesh = _drawn(("w", "x", "y", "z"), _WHOLE_SQUARE, _PIN_WY)
    assert [drawn_path.path for drawn_path in mesh.paths if drawn_path.reason == PATH_FOR_PIN] == [
        ("w", "x", "y"),
    ]


def test_a_drawn_path_names_the_carrier_it_is_ordered_from() -> None:
    mesh = _drawn(("w", "x", "y", "z"), _WHOLE_SQUARE, _PIN_WY)
    assert all(drawn_path.carrier in ("lumen", "zayo") for drawn_path in mesh.paths)
