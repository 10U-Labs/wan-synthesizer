from __future__ import annotations

from typing import Any

import pytest
import yaml

from repo_utils import REPO_ROOT
from seed import (
    DATA,
    ETC,
    _carrier_names,
    _degree_doc,
    _fiber_segment_rows,
    _mapping_rows,
    _off_net_rows,
    _rows,
)
from synthesizer.codec import load_merged_carriers, load_off_net, load_regions, load_sites
from synthesizer.config import app_config_from_parts
from synthesizer.input_graph import FiberSegment, Site
from synthesizer.model import Synthesis
from synthesizer.overrides import apply_role_overrides
from synthesizer.stages import dual_home, finalize
from synthesizer.synthesize import synthesize_two_tier

_SLACK = 1e-6


def _stamped(carrier: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pops = [{"carrier": carrier, **row} for row in _rows(DATA / "pops" / f"{carrier}.csv")]
    segments = [{"carrier": carrier, **row} for row in _fiber_segment_rows(carrier)]
    return pops, segments


def _parts(config: dict[str, Any]) -> dict[str, Any]:
    backbone = config["backbone"]
    homing = config["homing"]
    forced = backbone.get("forced", {})
    prohibited = backbone.get("prohibited", {})
    return {
        "forced-wan-pops": forced.get("wan_pops", []),
        "forced-circuits": forced.get("circuits", []),
        "forced-homes": homing.get("forced", []),
        "prohibited-wan-pops": prohibited.get("wan_pops", []),
        "prohibited-circuits": prohibited.get("circuits", []),
        "degree-exempt-wan-pops": backbone.get("degree_exempt", []),
        "wan-pop-count": backbone.get("wan_pop_count", {}),
        "backbone-number-of-diverse-circuits": _degree_doc(
            backbone["number_of_diverse_circuits"]
        ),
        "homing-degree": _degree_doc(homing["degree"]),
        "convergence-promotion": {"promote": backbone["promote_high_degree_convergences"]},
        "knobs": {"backbone_coverage_target_miles": backbone["coverage_target_miles"]},
        "settings": config.get("settings", {}),
    }


def _merged() -> tuple[list[Site], dict[tuple[str, str], FiberSegment]]:
    pops: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    for carrier in _carrier_names():
        stamped_pops, stamped_segments = _stamped(carrier)
        pops += stamped_pops
        segments += stamped_segments
    return load_merged_carriers(pops, segments)


def _tenant_sites(inputs: dict[str, Any]) -> list[Site]:
    return load_sites(_mapping_rows(inputs.get("locations", {}))) + load_regions(
        _rows(REPO_ROOT / inputs["providers"]) if inputs.get("providers") else []
    )


def _synthesized(stem: str) -> Synthesis:
    config: dict[str, Any] = yaml.safe_load((ETC / f"{stem}.yml").read_text(encoding="utf-8"))
    inputs = config.get("inputs", {})
    carrier_pops, fiber_segments = _merged()
    off_net_file = inputs.get("forced")
    off_net = load_off_net(_off_net_rows(off_net_file) if off_net_file else [])
    app = app_config_from_parts(_parts(config))
    homed = dual_home(
        carrier_pops + _tenant_sites(inputs), fiber_segments, app.params, off_net
    )
    graph, fiber_segments, overrides = apply_role_overrides(
        homed.sites, homed.fiber_segments, app.params, app.operator_circuits
    )
    synthesis = synthesize_two_tier(graph, fiber_segments, app.params, overrides)
    return finalize(
        graph, fiber_segments, synthesis, app.params, overrides.degree_exempt_wan_pop_ids
    )[2]


@pytest.fixture(name="daf", scope="module")
def _daf() -> Synthesis:
    return _synthesized("daf")


def test_dafs_wan_runs_no_fewer_miles_than_the_floor_published_beside_it(
        daf: Synthesis) -> None:
    assert daf.metrics.physical_miles >= daf.metrics.backbone_lower_bound_miles - _SLACK
