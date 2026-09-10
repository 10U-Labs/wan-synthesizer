from __future__ import annotations

from test_published_syntheses import offered_diverse_circuits

_ASHBURN = "Ashburn, VA"
_BOSTON = "Boston, MA"
_SPLIT = {
    "zayo": {
        frozenset({_BOSTON, "Albany, NY"}),
        frozenset({"Albany, NY", _ASHBURN}),
    },
    "lumen": {frozenset({_BOSTON, "Stamford, CT"})},
}
_NEW_YORK = "New York, NY"
_OWNED = {
    "zayo": {
        frozenset({_BOSTON, "Albany, NY"}),
        frozenset({"Albany, NY", _ASHBURN}),
    },
    "lumen": {
        frozenset({_BOSTON, "Stamford, CT"}),
        frozenset({"Stamford, CT", _NEW_YORK}),
    },
}
_PAIR = {
    "zayo": {
        frozenset({_BOSTON, "Albany, NY"}),
        frozenset({"Albany, NY", _ASHBURN}),
        frozenset({_BOSTON, "Stamford, CT"}),
        frozenset({"Stamford, CT", _ASHBURN}),
    },
}
_BOTH_QUOTE = {
    "zayo": {frozenset({_BOSTON, _ASHBURN}), frozenset({_BOSTON})},
    "lumen": {frozenset({_BOSTON, _ASHBURN})},
}


def test_a_city_whose_second_diverse_circuit_changes_hands_is_offered_only_the_first() -> None:
    assert offered_diverse_circuits(_SPLIT, _BOSTON, frozenset({_ASHBURN}), 1) == 1


def test_a_city_is_offered_a_diverse_circuit_by_each_carrier_that_has_one() -> None:
    assert offered_diverse_circuits(
        _OWNED, _BOSTON, frozenset({_ASHBURN, _NEW_YORK}), 1
    ) == 2


def test_one_peer_may_end_more_than_one_circuit_where_there_is_only_one_peer() -> None:
    assert offered_diverse_circuits(_PAIR, _BOSTON, frozenset({_ASHBURN}), 2) == 2


def test_no_more_diverse_circuits_are_counted_than_the_peers_can_end() -> None:
    assert offered_diverse_circuits(_BOTH_QUOTE, _BOSTON, frozenset({_ASHBURN}), 1) == 1


def test_a_city_no_carrier_has_fiber_at_is_offered_nothing() -> None:
    assert offered_diverse_circuits(
        _SPLIT, "Huntingdon, United Kingdom", frozenset({_ASHBURN}), 1
    ) == 0
