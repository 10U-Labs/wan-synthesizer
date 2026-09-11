from __future__ import annotations

from typing import Any

from test_published_syntheses import fiber_miles_run_over


def _segment(near: str, far: str, miles: float) -> dict[str, Any]:
    return {"source_id": near, "target_id": far, "distance_miles": miles}


_LAID: list[dict[str, Any]] = [
    _segment("west", "hub", 120.5),
    _segment("hub", "east", 240.25),
]


def test_the_miles_are_the_carrier_fiber_the_wan_runs_over() -> None:
    assert fiber_miles_run_over({"fiber": _LAID}) == 360.75


def test_a_wan_carrying_no_circuits_runs_over_no_fiber() -> None:
    assert fiber_miles_run_over({"fiber": []}) == 0
