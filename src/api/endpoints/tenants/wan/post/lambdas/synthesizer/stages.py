from __future__ import annotations

from synthesizer.ceiling import CircuitProofInputs, diverse_circuit_ceilings
from synthesizer.graphs import adjacency_by_carrier, build_adjacency
from synthesizer.input_graph import FiberSegment, Site
from synthesizer.model import Synthesis, SynthesisParams, MeshRequirements, ValidationReport
from synthesizer.on_net_fabrication import fabricate_missing_on_net_pops
from synthesizer.offnet import realize_off_net_sites
from synthesizer.validation import (
    wan_pop_names_by_group,
    wan_pop_mesh_target,
    validate_synthesis,
)


def dual_home(
    sites: list[Site],
    fiber_segments: dict[tuple[str, str], FiberSegment],
    params: SynthesisParams,
    off_net_sites: list[Site],
) -> tuple[list[Site], dict[tuple[str, str], FiberSegment]]:
    forced_wan_pops = frozenset(params.forced_wan_pop_names)
    fabricated = fabricate_missing_on_net_pops(
        sites, fiber_segments, forced_wan_pops
    )
    sites, fiber_segments = fabricated.sites, fabricated.fiber_segments
    off_net = realize_off_net_sites(
        sites,
        fiber_segments,
        off_net_sites,
        forced_wan_pops,
    )
    return off_net.sites, off_net.fiber_segments


def finalize(
    sites: list[Site],
    fiber_segments: dict[tuple[str, str], FiberSegment],
    synthesis: Synthesis,
    params: SynthesisParams,
    degree_exempt: frozenset[str] = frozenset(),
) -> tuple[
    list[Site], dict[tuple[str, str], FiberSegment], Synthesis, ValidationReport
]:
    adjacency = build_adjacency(fiber_segments)
    terrestrial = build_adjacency({
        key: segment for key, segment in fiber_segments.items() if not segment.submarine
    })
    targets = MeshRequirements(
        number_of_diverse_circuits=params.tuning.backbone_number_of_diverse_circuits,
        degree_exempt=degree_exempt,
        ceilings=diverse_circuit_ceilings(CircuitProofInputs(
            synthesis.wan_pop_ids,
            adjacency,
            params.tuning.backbone_number_of_diverse_circuits,
            params.max_wan_pop_count,
            adjacency_by_carrier(fiber_segments),
            terrestrial,
        )),
    )
    validation = validate_synthesis(
        sites, synthesis, params.tuning.homing_degree, targets
    )
    if not validation["connected"]:
        groups = "; ".join(
            ", ".join(names) for names in wan_pop_names_by_group(sites, synthesis)
        )
        raise ValueError(
            f"Synthesis falls into {validation['component_count']} groups "
            f"no fiber joins: {groups}"
        )
    cut_pops = validation["backbone_mesh_cut_pops"]
    if cut_pops:
        splits = ", ".join(str(entry["name"]) for entry in cut_pops)
        raise ValueError(f"Loss of one PoP splits the WAN at: {splits}")
    deficient = validation["backbone_mesh_independence_deficient"]
    if deficient:
        shortfalls = ", ".join(
            f"{entry['name']} ({entry['independent_degree']} of "
            f"{wan_pop_mesh_target(str(entry['id']), targets)})"
            for entry in deficient
        )
        raise ValueError(
            f"Too few independently failing backbone mesh paths at: {shortfalls}"
        )
    return sites, fiber_segments, synthesis, validation
