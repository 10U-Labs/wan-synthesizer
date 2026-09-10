from __future__ import annotations

from typing import Any

from test_published_syntheses import overbuilt_pairs


def _circuit(source: str, target: str, *transit: str) -> dict[str, Any]:
    return {
        "source_id": source,
        "target_id": target,
        "path": [source, *transit, target],
        "distance_miles": 100.0 * (len(transit) + 1),
    }


def _synthesis(circuits: list[dict[str, Any]], allowed: int = 2) -> dict[str, Any]:
    sites = sorted({circuit[end] for circuit in circuits for end in ("source_id", "target_id")})
    return {
        "number_of_diverse_circuits": allowed,
        "backbone": [{"id": site, "name": site} for site in sites],
        "links": circuits,
    }


_SPARE_CIRCUIT = [
    _circuit("west", "east", "m1"),
    _circuit("west", "east", "m2"),
    _circuit("west", "north", "m3"),
    _circuit("east", "north", "m4"),
]


def test_a_pair_holding_a_circuit_neither_end_needs_is_reported_with_its_count() -> None:
    assert overbuilt_pairs(_synthesis(_SPARE_CIRCUIT)) == [("east <-> west", 2)]


def test_a_pair_whose_second_circuit_is_a_ways_out_is_not_reported() -> None:
    synthesis = _synthesis([_circuit("west", "east", "m1"), _circuit("west", "east", "m2")])
    assert not overbuilt_pairs(synthesis)


def test_a_second_circuit_crossing_the_same_city_as_the_first_is_reported() -> None:
    synthesis = _synthesis([
        _circuit("west", "east", "m1"),
        _circuit("west", "east", "m1", "x"),
        _circuit("west", "north", "m3"),
        _circuit("east", "north", "m4"),
    ])
    assert overbuilt_pairs(synthesis) == [("east <-> west", 2)]


_ROUND_A_CUT_CITY = [
    _circuit("east", "north", "m2"),
    _circuit("west", "north", "m2", "m3"),
    _circuit("east", "west", "m3"),
    _circuit("west", "north", "m3"),
]


def test_a_second_circuit_holding_a_pop_from_splitting_the_wan_is_not_reported() -> None:
    assert not overbuilt_pairs(_synthesis(_ROUND_A_CUT_CITY))


def test_a_pair_joined_once_is_not_reported() -> None:
    assert not overbuilt_pairs(_synthesis([_circuit("west", "east", "m1")]))


def test_circuits_served_under_either_order_of_the_two_ends_count_as_one_pair() -> None:
    synthesis = _synthesis([
        _circuit("west", "east", "m1"),
        _circuit("east", "west", "m2"),
        _circuit("west", "east", "m5"),
        _circuit("west", "north", "m3"),
        _circuit("east", "north", "m4"),
    ])
    assert overbuilt_pairs(synthesis) == [("east <-> west", 3)]


def test_circuits_between_different_pairs_are_counted_apart() -> None:
    synthesis = _synthesis([_circuit("west", "east", "m1"), _circuit("west", "north", "m3")])
    assert not overbuilt_pairs(synthesis)


def test_every_overbuilt_pair_is_reported_not_only_the_first() -> None:
    synthesis = _synthesis([
        *_SPARE_CIRCUIT,
        _circuit("north", "south", "m6"),
        _circuit("north", "south", "m7"),
        _circuit("west", "south", "m8"),
    ])
    assert [pair for pair, _count in overbuilt_pairs(synthesis)] == [
        "east <-> west", "north <-> south"
    ]


def test_a_network_carrying_no_circuits_reports_nothing() -> None:
    assert not overbuilt_pairs(_synthesis([]))
