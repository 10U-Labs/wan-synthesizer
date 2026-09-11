from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

from synthesizer.collections import site_role
from synthesizer.input_graph import segment_key
from synthesizer.model import (
    HomingCircuit,
    PROVIDER_HOMING,
    TENANT_HOMING,
    Synthesis,
    SynthesisArtifacts,
)
from synthesizer.validation import included_site_ids


def sorted_fiber_segments(synthesis: Synthesis) -> list[tuple[str, str]]:
    return sorted(synthesis.fiber_segment_keys)


def homed_site_count(homing_circuits: Iterable[HomingCircuit]) -> int:
    return len({homing_circuit.source for homing_circuit in homing_circuits})


def _kinded(synthesis: Synthesis) -> list[tuple[HomingCircuit, str]]:
    return sorted(
        [(homing_circuit, TENANT_HOMING) for homing_circuit in synthesis.homings.tenant]
        + [
            (homing_circuit, PROVIDER_HOMING)
            for homing_circuit in synthesis.homings.provider
        ],
        key=lambda pair: (pair[0].source, pair[0].target),
    )


def synthesis_payload(artifacts: SynthesisArtifacts) -> dict[str, Any]:
    sites = artifacts.sites
    fiber_segments = artifacts.fiber_segments
    synthesis = artifacts.synthesis
    validation = artifacts.validation
    sites_by_id = {site.id: site for site in sites}
    return {
        "objective": (
            "Two-tier WAN synthesis: demand sites (tenant sites and provider regions) home "
            "to a meshed backbone of selected Carrier PoPs over the physical Carrier "
            "graph, with at least three strong WAN PoPs and extra ones added "
            "where they bring demand closer."
        ),
        "summary": {
            "wan_pop_count": len(synthesis.wan_pop_ids),
            "transit_count": len(synthesis.transit_ids),
            "tenant_site_count": homed_site_count(synthesis.homings.tenant),
            "provider_region_count": homed_site_count(synthesis.homings.provider),
            "tenant_homing_circuit_count": len(synthesis.homings.tenant),
            "provider_homing_circuit_count": len(synthesis.homings.provider),
            "fiber_segment_count": len(synthesis.fiber_segment_keys),
            "tenant_homing_miles": round(synthesis.metrics.tenant_homing_miles, 3),
            "provider_homing_miles": round(synthesis.metrics.provider_homing_miles, 3),
            "physical_carrier_miles": round(synthesis.metrics.physical_miles, 3),
            "backbone_lower_bound_miles": round(
                synthesis.metrics.backbone_lower_bound_miles, 3
            ),
            "total_synthesis_miles": round(
                synthesis.metrics.tenant_homing_miles
                + synthesis.metrics.provider_homing_miles
                + synthesis.metrics.physical_miles,
                3,
            ),
            "score": round(synthesis.metrics.score, 3),
            "wan_pops": [
                sites_by_id[site_id].name for site_id in synthesis.wan_pop_ids
            ],
        },
        "validation": validation,
        "sites": [
            {
                **asdict(site),
                "tier_role": site_role(site, synthesis),
                "included": site.id in included_site_ids(synthesis),
            }
            for site in sites
        ],
        "homing_circuits": [
            {
                "source_id": homing_circuit.source,
                "source_name": sites_by_id[homing_circuit.source].name,
                "target_id": homing_circuit.target,
                "target_name": sites_by_id[homing_circuit.target].name,
                "homing_kind": homing_kind,
                "distance_miles": round(homing_circuit.distance_miles, 3),
            }
            for homing_circuit, homing_kind in _kinded(synthesis)
        ],
        "fiber_segments": [
            {
                "source_id": left,
                "source_name": sites_by_id[left].name,
                "target_id": right,
                "target_name": sites_by_id[right].name,
                "distance_miles": round(fiber_segments[segment_key(left, right)].distance_miles, 3),
                "source_page": fiber_segments[segment_key(left, right)].source_page,
                "note": fiber_segments[segment_key(left, right)].note,
                "submarine": fiber_segments[segment_key(left, right)].submarine,
            }
            for left, right in sorted_fiber_segments(synthesis)
        ],
        "drawn_circuits": [
            {
                "purpose": drawn_circuit.purpose,
                "source_id": drawn_circuit.source,
                "source_name": sites_by_id[drawn_circuit.source].name,
                "target_id": drawn_circuit.target,
                "target_name": sites_by_id[drawn_circuit.target].name,
                "distance_miles": round(drawn_circuit.distance_miles, 3),
                "carrier": drawn_circuit.carrier,
                "route": [sites_by_id[site_id].name for site_id in drawn_circuit.pop_ids],
                "reason": drawn_circuit.reason,
                "requested_by": [
                    sites_by_id[site_id].name for site_id in drawn_circuit.requested_by
                ],
            }
            for drawn_circuit in synthesis.drawn_circuits
        ],
    }
