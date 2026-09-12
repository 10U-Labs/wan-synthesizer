from __future__ import annotations

from test_published_syntheses import offered_diverse_circuits

_ASHBURN = "Ashburn, VA"
_BOSTON = "Boston, MA"
_ALBANY = "Albany, NY"
_STAMFORD = "Stamford, CT"
_NEW_YORK = "New York, NY"
_CHANGES_HANDS = {frozenset({_BOSTON, _ALBANY}), frozenset({_ALBANY, _ASHBURN})}
_TWO_WAYS = {
    frozenset({_BOSTON, _ALBANY}),
    frozenset({_ALBANY, _ASHBURN}),
    frozenset({_BOSTON, _STAMFORD}),
    frozenset({_STAMFORD, _NEW_YORK}),
}
_PAIR = {
    frozenset({_BOSTON, _ALBANY}),
    frozenset({_ALBANY, _ASHBURN}),
    frozenset({_BOSTON, _STAMFORD}),
    frozenset({_STAMFORD, _ASHBURN}),
}


def test_a_city_is_offered_a_diverse_circuit_that_changes_hands() -> None:
    assert offered_diverse_circuits(_CHANGES_HANDS, _BOSTON, frozenset({_ASHBURN}), 1) == 1


def test_a_city_is_offered_a_diverse_circuit_over_each_way_its_fiber_reaches_a_peer() -> None:
    assert offered_diverse_circuits(
        _TWO_WAYS, _BOSTON, frozenset({_ASHBURN, _NEW_YORK}), 1
    ) == 2


def test_one_peer_may_end_more_than_one_circuit_where_there_is_only_one_peer() -> None:
    assert offered_diverse_circuits(_PAIR, _BOSTON, frozenset({_ASHBURN}), 2) == 2


def test_no_more_diverse_circuits_are_counted_than_the_peers_can_end() -> None:
    assert offered_diverse_circuits(_PAIR, _BOSTON, frozenset({_ASHBURN}), 1) == 1


def test_a_city_no_fiber_reaches_is_offered_nothing() -> None:
    assert offered_diverse_circuits(
        _CHANGES_HANDS, "Huntingdon, United Kingdom", frozenset({_ASHBURN}), 1
    ) == 0
