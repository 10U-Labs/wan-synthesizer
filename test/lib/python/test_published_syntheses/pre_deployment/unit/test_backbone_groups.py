from __future__ import annotations

from typing import Any

from test_published_syntheses import wan_pop_groups


def _seat(site_id: str) -> dict[str, Any]:
    return {"id": site_id}


def _segment(near: str, far: str) -> dict[str, Any]:
    return {"source_id": near, "target_id": far, "distance_miles": 10.0}


_JOINED = [
    _segment("west", "hub"),
    _segment("hub", "east"),
]
_SPLIT: dict[str, Any] = {
    "wan_pops": [_seat("west"), _seat("east"), _seat("hub"), _seat("salt"), _seat("lake")],
    "fiber": [*_JOINED, _segment("salt", "lake")],
}


def test_a_network_whose_fiber_joins_every_seat_is_one_group() -> None:
    assert wan_pop_groups({"wan_pops": _SPLIT["wan_pops"][:3], "fiber": _JOINED}) == [
        ["east", "hub", "west"]
    ]


def test_seats_the_fiber_leaves_in_two_groups_come_back_as_two_lists() -> None:
    assert wan_pop_groups(_SPLIT) == [["east", "hub", "west"], ["lake", "salt"]]


def test_a_seat_no_fiber_touches_at_all_is_a_group_of_one() -> None:
    assert wan_pop_groups({
        "wan_pops": [*_SPLIT["wan_pops"][:3], _seat("alone")],
        "fiber": _JOINED,
    }) == [["alone"], ["east", "hub", "west"]]


def test_a_tenant_with_no_published_backbone_has_no_group() -> None:
    assert not wan_pop_groups({"wan_pops": [], "fiber": []})
