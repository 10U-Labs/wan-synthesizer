from __future__ import annotations

import pytest

import fixtures
from synthesizer.forced import (
    apply_forced_access_homes,
    forced_backbone_pairs,
    removed_backbone_pairs,
)
from synthesizer.overrides import resolve_forced_paths
from synthesizer.model import ForcedPaths, NamedPath, OperatorPaths
from synthesizer.input_graph import segment_key

pop = fixtures.carrier_pop
access = fixtures.access_site

SITES = [pop("P0"), pop("P1"), access("A1")]


def test_backbone_path_resolves_to_a_segment_key() -> None:
    paths = resolve_forced_paths(
        OperatorPaths(backbone=(NamedPath("P0", "P1"),)), SITES, {"P0", "P1"}
    )
    assert paths.backbone == frozenset({segment_key("P0", "P1")})


def test_forced_home_resolves_to_an_ordered_pair() -> None:
    paths = resolve_forced_paths(
        OperatorPaths(access=(NamedPath("A1", "P1"),)), SITES, {"P1"}
    )
    assert paths.access == frozenset({("A1", "P1")})


def test_excluded_backbone_resolves_to_a_removed_pair() -> None:
    paths = resolve_forced_paths(
        OperatorPaths(removed_backbone=(NamedPath("P0", "P1"),)), SITES, {"P0", "P1"}
    )
    assert paths.removed_backbone == frozenset({segment_key("P0", "P1")})


def test_excluded_backbone_endpoint_need_not_be_forced() -> None:
    paths = resolve_forced_paths(
        OperatorPaths(removed_backbone=(NamedPath("P0", "P1"),)), SITES, set()
    )
    assert paths.removed_backbone == frozenset({segment_key("P0", "P1")})


def test_excluded_backbone_unknown_endpoint_is_rejected() -> None:
    with pytest.raises(ValueError):
        resolve_forced_paths(
            OperatorPaths(removed_backbone=(NamedPath("Nowhere", "P1"),)), SITES, set()
        )


def test_removed_backbone_pairs_keeps_only_in_set_pairs() -> None:
    paths = ForcedPaths(
        removed_backbone=frozenset({segment_key("P0", "P1"), segment_key("P0", "P9")})
    )
    assert removed_backbone_pairs({"P0", "P1"}, paths) == frozenset({segment_key("P0", "P1")})


def test_forced_backbone_pairs_keeps_only_in_set_pairs() -> None:
    paths = ForcedPaths(backbone=frozenset({segment_key("P0", "P1"), segment_key("P0", "P9")}))
    assert forced_backbone_pairs({"P0", "P1"}, paths) == frozenset({segment_key("P0", "P1")})


def test_unknown_backbone_endpoint_is_rejected() -> None:
    with pytest.raises(ValueError, match="forced-path"):
        resolve_forced_paths(
            OperatorPaths(backbone=(NamedPath("Nowhere", "P1"),)), SITES, {"P1"}
        )


def test_backbone_endpoint_not_forced_is_rejected() -> None:
    with pytest.raises(ValueError, match="forced-path"):
        resolve_forced_paths(
            OperatorPaths(backbone=(NamedPath("P0", "P1"),)), SITES, {"P0"}
        )


def test_forced_home_target_not_forced_names_the_home_list() -> None:
    with pytest.raises(ValueError, match="forced-home"):
        resolve_forced_paths(
            OperatorPaths(access=(NamedPath("A1", "P1"),)), SITES, set()
        )


def test_forced_home_target_off_the_carrier_graph_names_the_home_list() -> None:
    with pytest.raises(ValueError, match="forced-home"):
        resolve_forced_paths(
            OperatorPaths(access=(NamedPath("A1", "Nowhere"),)), SITES, {"P1"}
        )


def test_forced_home_source_that_is_not_demand_is_rejected() -> None:
    with pytest.raises(ValueError):
        resolve_forced_paths(
            OperatorPaths(access=(NamedPath("Nope", "P1"),)), SITES, {"P1"}
        )


def test_a_mesh_pair_is_not_read_as_a_home() -> None:
    paths = resolve_forced_paths(
        OperatorPaths(backbone=(NamedPath("P0", "P1"),)), SITES, {"P0", "P1"}
    )
    assert paths.access == frozenset()


def test_no_forced_path_returns_homes_unchanged() -> None:
    pop_by_id = {"P0": pop("P0", 40.0, -100.0), "P1": pop("P1", 50.0, -100.0)}
    homes = apply_forced_access_homes(
        access("A1", 40.0, -100.0), ["P0", "P1"], ForcedPaths(), pop_by_id, 2
    )
    assert homes == ["P0", "P1"]


def test_forced_access_home_is_pinned_over_a_nearer_facility() -> None:
    paths = ForcedPaths(access=frozenset({("A1", "P3")}))
    pop_by_id = {
        "P0": pop("P0", 40.0, -100.1),
        "P1": pop("P1", 50.0, -100.0),
        "P3": pop("P3", 41.0, -99.0),
    }
    homes = apply_forced_access_homes(
        access("A1", 40.0, -100.0), ["P0", "P1"], paths, pop_by_id, 2
    )
    assert set(homes) == {"P3", "P0"}
