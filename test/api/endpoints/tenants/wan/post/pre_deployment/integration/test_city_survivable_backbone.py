from __future__ import annotations

import fixtures

_SITES = ("a", "b", "c", "d")
_ASKED_FOR = 2
_SEGMENTS = {
    ("a", "b"): 10.0, ("a", "mid"): 15.0, ("b", "mid"): 5.0,
    ("c", "d"): 10.0, ("c", "mid"): 5.0, ("d", "mid"): 15.0,
    ("b", "w"): 20.0, ("w", "c"): 20.0,
}
_TRANSIT = ("mid", "w")
ARTIFACTS = fixtures.synthesis_over_segments(_SITES, _SEGMENTS, _ASKED_FOR, _TRANSIT)


def test_the_published_backbone_survives_the_loss_of_any_one_city() -> None:
    assert ARTIFACTS.validation["backbone_mesh_survives_any_one_site_loss"] is True


def test_the_floor_it_publishes_prices_what_surviving_that_loss_took() -> None:
    assert round(ARTIFACTS.synthesis.metrics.backbone_lower_bound_miles, 3) == 90.0


def test_the_report_tells_the_circuit_that_keeps_it_whole_from_a_peers_own_ask() -> None:
    assert fixtures.reasons_past_the_number(ARTIFACTS.validation) == {
        "peer_target", "pop_loss_relief",
    }
