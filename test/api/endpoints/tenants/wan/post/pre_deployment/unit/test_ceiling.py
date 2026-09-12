from __future__ import annotations

import fixtures
from synthesizer.ceiling import (
    CircuitProofInputs,
    diverse_circuit_ceiling,
    diverse_circuits,
    diverse_circuit_ceilings,
    diverse_circuits_by_carrier_and_peer,
)
from synthesizer.graphs import adjacency_by_carrier, build_adjacency
from synthesizer.input_graph import FiberSegment

physical = fixtures.fiber_segments_from


def _miles_along(
    pop_ids: tuple[str, ...], adjacency: dict[str, list[tuple[str, float]]]
) -> float:
    return sum(
        weight
        for left, right in zip(pop_ids, pop_ids[1:])
        for neighbor, weight in adjacency[left]
        if neighbor == right
    )


_TWO_CUTS = build_adjacency(physical({
    ("bos", "alb"): 1.0, ("bos", "stm"): 1.0, ("bos", "x"): 1.0, ("x", "alb"): 1.0,
    ("alb", "n1"): 1.0, ("stm", "n2"): 1.0, ("n1", "n2"): 1.0,
}))
_TWO_CUT_BACKBONE = ("bos", "n1", "n2")


def test_the_ceiling_is_the_number_of_cuts_not_of_fiber_segments() -> None:
    assert diverse_circuit_ceiling("bos", CircuitProofInputs(_TWO_CUT_BACKBONE, _TWO_CUTS)) == 2


_ONE_CUT = build_adjacency(physical({
    ("bos", "alb"): 1.0, ("bos", "x"): 1.0, ("x", "alb"): 1.0,
    ("alb", "n1"): 1.0, ("alb", "n2"): 1.0, ("n1", "n2"): 1.0,
}))


def test_a_wan_pop_behind_one_failure_point_has_a_ceiling_of_one() -> None:
    assert diverse_circuit_ceiling(
        "bos", CircuitProofInputs(("bos", "n1", "n2"), _ONE_CUT)
    ) == 1


_TWIN_CIRCUITS = build_adjacency(physical({
    ("s", "p1"): 1.0, ("s", "p2"): 1.0, ("p1", "t"): 1.0, ("p2", "t"): 1.0,
    ("t", "u"): 1.0,
}))


def test_two_circuits_to_one_peer_count_once() -> None:
    assert diverse_circuit_ceiling(
        "s", CircuitProofInputs(("s", "t", "u"), _TWIN_CIRCUITS)
    ) == 1


_ONE_PEER = ("s", "t")


def test_a_site_with_one_peer_holds_the_circuits_it_was_asked_for() -> None:
    inputs = CircuitProofInputs(_ONE_PEER, _TWIN_CIRCUITS, circuits_wanted=2)
    assert diverse_circuit_ceiling("s", inputs) == 2


def test_the_circuits_to_one_peer_share_no_city_but_that_peer() -> None:
    inner = [
        city
        for pop_ids in diverse_circuits(
            "s", CircuitProofInputs(_ONE_PEER, _TWIN_CIRCUITS, circuits_wanted=2)
        )
        for city in pop_ids[1:-1]
    ]
    assert sorted(inner) == sorted(set(inner))


def test_a_site_with_one_peer_is_still_held_to_one_circuit_when_one_is_asked() -> None:
    inputs = CircuitProofInputs(_ONE_PEER, _TWIN_CIRCUITS, circuits_wanted=1)
    assert diverse_circuit_ceiling("s", inputs) == 1


def test_a_site_selected_below_the_wan_pops_its_config_allows_takes_one_circuit() -> None:
    assert diverse_circuit_ceiling(
        "s", CircuitProofInputs(_ONE_PEER, _TWIN_CIRCUITS, circuits_wanted=2, max_wan_pop_count=6)
    ) == 1


_THREE_CIRCUITS = build_adjacency(physical({
    ("s", "near"): 1.0, ("near", "t"): 1.0,
    ("s", "mid"): 2.0, ("mid", "t"): 2.0,
    ("s", "far"): 3.0, ("far", "t"): 3.0,
}))


def test_no_more_circuits_to_one_peer_are_proved_than_were_asked_for() -> None:
    inputs = CircuitProofInputs(_ONE_PEER, _THREE_CIRCUITS, circuits_wanted=2)
    assert diverse_circuit_ceiling("s", inputs) == 2


def test_the_circuits_proved_to_one_peer_are_the_shortest_of_them() -> None:
    circuits = diverse_circuits(
        "s", CircuitProofInputs(_ONE_PEER, _THREE_CIRCUITS, circuits_wanted=2)
    )
    assert sorted(pop_ids[1] for pop_ids in circuits) == ["mid", "near"]


def test_an_unreachable_wan_pop_has_no_ceiling_at_all() -> None:
    inputs = CircuitProofInputs(("nowhere", "n1", "n2"), _ONE_CUT)
    assert diverse_circuit_ceiling("nowhere", inputs) == 0


def test_the_ceilings_are_computed_for_every_wan_pop() -> None:
    assert diverse_circuit_ceilings(CircuitProofInputs(_TWO_CUT_BACKBONE, _TWO_CUTS)) == {
        "bos": 2, "n1": 2, "n2": 2
    }


_BOS_CIRCUITS = diverse_circuits("bos", CircuitProofInputs(_TWO_CUT_BACKBONE, _TWO_CUTS))


def test_the_counted_circuits_run_from_the_wan_pop_to_distinct_peers() -> None:
    assert sorted((pop_ids[0], pop_ids[-1]) for pop_ids in _BOS_CIRCUITS) == [
        ("bos", "n1"), ("bos", "n2")
    ]


def test_the_counted_circuits_share_no_intermediate_city() -> None:
    inner = [city for pop_ids in _BOS_CIRCUITS for city in pop_ids[1:-1]]
    assert sorted(inner) == sorted(set(inner))


_EXPRESS_SEGMENTS = build_adjacency(physical({
    ("sea", "hil"): 100.0, ("sea", "eug"): 100.0,
    ("sea", "pdx"): 1.0, ("pdx", "hil"): 1.0,
    ("sea", "tac"): 1.0, ("tac", "eug"): 1.0,
}))
_EXPRESS_BACKBONE = ("eug", "hil", "sea")


def test_the_circuits_proved_are_the_shortest_set_of_that_size() -> None:
    assert sum(
        _miles_along(pop_ids, _EXPRESS_SEGMENTS)
        for pop_ids in diverse_circuits(
            "sea", CircuitProofInputs(_EXPRESS_BACKBONE, _EXPRESS_SEGMENTS)
        )
    ) == 4.0


def test_taking_the_shortest_set_costs_the_site_none_of_its_circuits() -> None:
    inputs = CircuitProofInputs(_EXPRESS_BACKBONE, _EXPRESS_SEGMENTS)
    assert diverse_circuit_ceiling("sea", inputs) == 2


_PACIFIC_ADJACENCY = build_adjacency(physical({
    ("sea", "pdx"): 10.0, ("pdx", "hil"): 10.0, ("pdx", "eug"): 10.0,
    ("sea", "tok"): 1000.0, ("tok", "hil"): 1000.0, ("tok", "eug"): 1000.0,
}))
_PACIFIC_BACKBONE = ("eug", "hil", "sea")


def test_a_ceiling_counts_a_diverse_circuit_however_far_it_runs() -> None:
    assert diverse_circuit_ceiling(
        "sea", CircuitProofInputs(_PACIFIC_BACKBONE, _PACIFIC_ADJACENCY)
    ) == 2


_CHANGES_HANDS = fixtures.carrier_fiber_segments({
    ("s", "x"): (1.0, ("lumen",)),
    ("x", "t"): (1.0, ("zayo",)),
    ("s", "y"): (1.0, ("lumen",)),
    ("y", "t"): (1.0, ("zayo",)),
})
_ONE_COMPANY_EACH = fixtures.carrier_fiber_segments({
    ("s", "x"): (1.0, ("lumen",)),
    ("x", "t"): (1.0, ("lumen",)),
    ("s", "y"): (1.0, ("zayo",)),
    ("y", "t"): (1.0, ("zayo",)),
})


def _owned_proof(
    fiber: dict[tuple[str, str], FiberSegment], circuits_wanted: int = 1
) -> CircuitProofInputs:
    return CircuitProofInputs(
        ("s", "t"),
        build_adjacency(fiber),
        circuits_wanted=circuits_wanted,
        fiber_by_carrier=adjacency_by_carrier(fiber),
    )


def test_a_circuit_that_changes_hands_is_no_diverse_circuit() -> None:
    assert not diverse_circuits("s", _owned_proof(_CHANGES_HANDS))


def test_diverse_circuits_may_come_from_different_carriers() -> None:
    assert sorted(diverse_circuits("s", _owned_proof(_ONE_COMPANY_EACH, 2))) == [
        ("s", "x", "t"), ("s", "y", "t"),
    ]


def test_the_same_fiber_joins_the_pair_when_nobody_owns_it() -> None:
    assert diverse_circuits("s", CircuitProofInputs(("s", "t"), build_adjacency(
        physical({("s", "x"): 1.0, ("x", "t"): 1.0, ("s", "y"): 1.0, ("y", "t"): 1.0}),
    ))) == [("s", "x", "t")]


_BOTH_HAVE_IT = fixtures.carrier_fiber_segments({("s", "t"): (1.0, ("lumen", "zayo"))})
_SHARE_A_CITY = fixtures.carrier_fiber_segments({
    ("s", "x"): (1.0, ("lumen", "zayo")),
    ("x", "t"): (1.0, ("lumen",)),
    ("x", "u"): (1.0, ("zayo",)),
    ("u", "t"): (1.0, ("zayo",)),
})


def test_a_circuit_both_carriers_have_is_drawn_once() -> None:
    assert diverse_circuits("s", _owned_proof(_BOTH_HAVE_IT)) == [("s", "t")]


def test_a_circuit_standing_on_a_city_already_spent_is_not_drawn() -> None:
    assert diverse_circuits("s", _owned_proof(_SHARE_A_CITY)) == [("s", "x", "t")]


def test_one_peer_takes_one_circuit_however_many_carriers_offer_one() -> None:
    assert diverse_circuits("s", _owned_proof(_ONE_COMPANY_EACH)) == [("s", "x", "t")]


_UNDER_WATER = fixtures.fiber_segments_under_water(
    {
        ("sea", "pdx"): 10.0, ("pdx", "hil"): 10.0,
        ("sea", "tok"): 1000.0, ("tok", "hil"): 1000.0,
    },
    {("sea", "tok"), ("tok", "hil")},
)
_UNDER_WATER_BACKBONE = ("hil", "sea")


def _on_land(
    fiber: dict[tuple[str, str], FiberSegment]
) -> dict[str, list[tuple[str, float]]]:
    return build_adjacency({
        key: segment for key, segment in fiber.items() if not segment.submarine
    })


def test_a_circuit_under_water_is_no_diverse_circuit_where_the_site_has_one_over_land() -> None:
    assert diverse_circuits(
        "sea",
        CircuitProofInputs(
            _UNDER_WATER_BACKBONE,
            build_adjacency(_UNDER_WATER),
            circuits_wanted=2,
            terrestrial=_on_land(_UNDER_WATER),
        ),
    ) == [("sea", "pdx", "hil")]


_ISLAND = fixtures.fiber_segments_under_water(
    {
        ("sea", "pdx"): 10.0, ("pdx", "hil"): 10.0,
        ("syd", "sea"): 8000.0, ("syd", "hil"): 8000.0,
    },
    {("syd", "sea"), ("syd", "hil")},
)
_ISLAND_BACKBONE = ("hil", "sea", "syd")


def test_a_site_reachable_only_over_water_keeps_the_diverse_circuits_it_has() -> None:
    assert sorted(diverse_circuits(
        "syd",
        CircuitProofInputs(
            _ISLAND_BACKBONE,
            build_adjacency(_ISLAND),
            circuits_wanted=2,
            terrestrial=_on_land(_ISLAND),
        ),
    )) == [("syd", "hil"), ("syd", "sea")]


def _credit_over(
    fiber: dict[tuple[str, str], FiberSegment],
    wan_pop_ids: tuple[str, ...],
    most: int | None,
) -> dict[str, dict[tuple[str, str], int]]:
    return diverse_circuits_by_carrier_and_peer(
        CircuitProofInputs(
            wan_pop_ids,
            build_adjacency(fiber),
            circuits_wanted=2,
            fiber_by_carrier=adjacency_by_carrier(fiber),
        ),
        most,
    )


_ALREADY_NEEDED_CREDIT = _credit_over(
    fixtures.ALREADY_NEEDED_FIBER, fixtures.ALREADY_NEEDED_SITES, None
)
_FLOORED_ABOVE_FIBER = fixtures.carrier_fiber_segments(fixtures.FLOORED_ABOVE_SEGMENTS)


def test_a_wan_pops_ask_is_credited_to_the_carrier_of_fiber_the_wan_already_needs() -> None:
    assert _ALREADY_NEEDED_CREDIT["f"] == {("lumen", "b"): 1}


def test_a_wan_pop_the_wan_shares_no_fiber_with_keeps_its_shortest_circuits_carriers() -> None:
    assert _ALREADY_NEEDED_CREDIT["b"] == {("zayo", "d"): 1, ("lumen", "f"): 1}


def test_every_diverse_circuit_a_wan_pops_carriers_prove_is_credited_when_none_is_asked() -> None:
    assert _credit_over(_FLOORED_ABOVE_FIBER, fixtures.FLOORED_ABOVE_SITES, None)["b"] == {
        ("zayo", "e"): 1, ("cogent", "d"): 1, ("cogent", "f"): 1,
    }


def test_the_credit_is_cut_to_the_diverse_circuits_the_tenant_asked_for() -> None:
    assert _credit_over(_FLOORED_ABOVE_FIBER, fixtures.FLOORED_ABOVE_SITES, 2)["b"] == {
        ("zayo", "e"): 1, ("cogent", "d"): 1,
    }
