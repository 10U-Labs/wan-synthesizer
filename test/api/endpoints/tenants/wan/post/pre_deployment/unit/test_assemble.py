from __future__ import annotations

from dataclasses import replace

import fixtures
from fixtures import (
    TRIANGLE,
    TWO_POCKET_FIBER,
    TWO_POCKET_IDS,
    synthesis_inputs_from_fiber,
    search_plan,
)
from synthesizer.model import AccessPath, SynthesisInputs, ForcedPaths
from synthesizer.assemble import (
    assign_access,
    backbone_physically_biconnectable,
    build_synthesis_for_backbone,
    forced_backbone_resilience_error,
)

pop = fixtures.carrier_pop
physical = fixtures.fiber_segments_from
access = fixtures.access_site


def _dual_inputs(s_coord: tuple[float, float] = (0.0, 0.05)) -> SynthesisInputs:
    return synthesis_inputs_from_fiber(
        ["c1", "c2"], DUAL_FIBER, {"c1", "c2"},
        [access("s", *s_coord)], {"c1": (0.0, 0.0), "c2": (0.0, 0.1)},
    )


def _access_homing_counts(access_paths: list[AccessPath]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for access_path in access_paths:
        counts[access_path.source] = counts.get(access_path.source, 0) + 1
    return counts


def test_assign_access_homes_a_demand_site_to_two_backbone_nodes() -> None:
    result = assign_access(("c1", "c2"), _dual_inputs(), search_plan([]))
    assert result is not None and _access_homing_counts(result) == {"s": 2}


def test_assign_access_returns_none_when_backbone_smaller_than_the_homing_degree() -> None:
    assert assign_access(("c1",), _dual_inputs(), search_plan([], access_homing_degree=2)) is None


def test_assign_access_homes_to_the_configured_count() -> None:
    triple_fiber = physical(
        {
            ("c1", "c2"): 1.0, ("c2", "c3"): 1.0, ("c1", "c3"): 1.0,
            ("s", "c1"): 1.0, ("s", "c2"): 1.0, ("s", "c3"): 1.0,
        }
    )
    inputs = synthesis_inputs_from_fiber(
        ["c1", "c2", "c3"], triple_fiber, {"c1", "c2", "c3"},
        [access("s", 0.0, 0.05)], {"c1": (0.0, 0.0), "c2": (0.0, 0.1), "c3": (0.0, 0.2)},
    )
    result = assign_access(("c1", "c2", "c3"), inputs, search_plan([], access_homing_degree=3))
    assert result is not None and _access_homing_counts(result) == {"s": 3}


def test_assign_access_leads_with_a_forced_home() -> None:
    plan = replace(search_plan([]), forced_paths=ForcedPaths(access=frozenset({("s", "c2")})))
    result = assign_access(("c1", "c2"), _dual_inputs((0.0, 0.0)), plan)
    assert result is not None and {path.target for path in result if path.source == "s"} == {
        "c1", "c2",
    }


def test_build_synthesis_returns_none_without_homing() -> None:
    inputs = _dual_inputs()
    plan = search_plan([], access_homing_degree=2)
    assert build_synthesis_for_backbone(("c1",), inputs, plan) is None


def test_build_synthesis_returns_none_when_nodes_are_not_meshed() -> None:
    fiber = physical(
        {
            ("c1", "g1"): 1.0, ("c2", "g1"): 1.0, ("c1", "g2"): 1.0, ("c2", "g2"): 1.0,
            ("c3", "z"): 1.0, ("s", "c1"): 1.0, ("s", "c2"): 1.0,
        }
    )
    inputs = synthesis_inputs_from_fiber(
        ["c1", "c2", "c3", "g1", "g2", "z"], fiber, {"c1", "c2", "c3"}, [access("s")]
    )
    assert build_synthesis_for_backbone(("c1", "c2", "c3"), inputs, search_plan([])) is None


def test_build_synthesis_builds_a_full_synthesis() -> None:
    synthesis = build_synthesis_for_backbone(("c1", "c2"), _dual_inputs(), search_plan([]))
    assert synthesis is not None and set(synthesis.backbone_ids) == {"c1", "c2"}


def _two_pocket_inputs() -> SynthesisInputs:
    return synthesis_inputs_from_fiber(TWO_POCKET_IDS, TWO_POCKET_FIBER, set(TWO_POCKET_IDS))


def _bowtie_inputs() -> SynthesisInputs:
    return synthesis_inputs_from_fiber(_BOWTIE_IDS, _BOWTIE_FIBER, set(_BOWTIE_IDS))


def test_physically_biconnectable_within_one_block() -> None:
    assert backbone_physically_biconnectable(("a", "b"), _two_pocket_inputs()) is True


def test_not_physically_biconnectable_across_a_bridge() -> None:
    assert backbone_physically_biconnectable(("a", "d"), _two_pocket_inputs()) is False


def test_not_physically_biconnectable_across_a_cut_city() -> None:
    assert backbone_physically_biconnectable(("a", "d"), _bowtie_inputs()) is False


def test_physically_biconnectable_within_one_bowtie_lobe() -> None:
    assert backbone_physically_biconnectable(("a", "b"), _bowtie_inputs()) is True


def test_not_biconnectable_with_no_backbone_nodes() -> None:
    assert backbone_physically_biconnectable((), _bowtie_inputs()) is False


def test_forced_resilience_error_for_forced_nodes_split_across_pockets() -> None:
    assert forced_backbone_resilience_error(
        frozenset({"a", "d"}), _two_pocket_inputs(), 2
    ) is not None


def _triangle_inputs() -> SynthesisInputs:
    return synthesis_inputs_from_fiber(["a", "b", "c"], TRIANGLE, {"a", "b", "c"})


def test_forced_resilience_error_for_a_pocket_too_small_for_the_floor() -> None:
    assert forced_backbone_resilience_error(frozenset({"a"}), _two_pocket_inputs(), 5) is not None


def test_forced_resilience_error_none_for_a_healthy_forced_node() -> None:
    assert forced_backbone_resilience_error(frozenset({"a"}), _triangle_inputs(), 2) is None


def test_forced_resilience_error_none_without_forced_nodes() -> None:
    assert forced_backbone_resilience_error(frozenset(), _triangle_inputs(), 2) is None


DUAL_FIBER = physical(
    {("c1", "c2"): 1.0, ("s", "c1"): 1.0, ("s", "c2"): 1.0}
)


_BOWTIE_FIBER = physical(
    {
        ("a", "b"): 1.0, ("b", "x"): 1.0, ("a", "x"): 1.0,
        ("x", "d"): 1.0, ("d", "e"): 1.0, ("x", "e"): 1.0,
    }
)
_BOWTIE_IDS = ["a", "b", "x", "d", "e"]
