from __future__ import annotations

import fixtures
from synthesizer.input_graph import carriers_along
from synthesizer.model import SynthesisPath

_SHORTCUT_CITY = "t"
_SITES = ("a", "b", "c", "d")
ARTIFACTS = fixtures.synthesis_over_owned_fiber(
    _SITES,
    {
        ("a", "b"): (100.0, ("lumen",)),
        ("b", "c"): (100.0, ("lumen",)),
        ("c", "d"): (100.0, ("zayo",)),
        ("d", "a"): (100.0, ("zayo",)),
        ("a", _SHORTCUT_CITY): (10.0, ("lumen",)),
        (_SHORTCUT_CITY, "c"): (10.0, ("zayo",)),
    },
    2,
    transit_ids=(_SHORTCUT_CITY,),
)
_MESH = fixtures.mesh_paths(ARTIFACTS)


def _paths_at(site: str) -> list[SynthesisPath]:
    return [drawn_path for drawn_path in _MESH if site in (drawn_path.source, drawn_path.target)]


def _carriers_at(site: str) -> set[str]:
    return {drawn_path.carrier for drawn_path in _paths_at(site)}


def test_every_drawn_path_is_one_carriers_to_offer() -> None:
    assert all(carriers_along(drawn_path.path, ARTIFACTS.fiber_segments) for drawn_path in _MESH)


def test_every_drawn_path_names_the_carrier_it_is_ordered_from() -> None:
    assert all(drawn_path.carrier in ("lumen", "zayo") for drawn_path in _MESH)


def test_the_short_way_that_changes_hands_is_not_drawn() -> None:
    assert not [drawn_path for drawn_path in _MESH if _SHORTCUT_CITY in drawn_path.path]


def test_a_sites_ways_out_may_be_ordered_from_different_carriers() -> None:
    assert _carriers_at("a") == {"lumen", "zayo"}


def test_every_site_still_holds_the_paths_its_tenant_asked_for() -> None:
    assert all(len(_paths_at(site)) == 2 for site in _SITES)
