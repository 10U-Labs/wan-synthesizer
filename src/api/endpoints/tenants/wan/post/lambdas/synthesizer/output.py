from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from typing import Any

from synthesizer.codec import PROVIDER_KIND
from synthesizer.collections import site_role
from synthesizer.input_graph import Site, segment_key
from synthesizer.model import Synthesis, SynthesisArtifacts, SourceFiles, is_carrier_pop
from synthesizer.validation import included_site_ids


def sorted_fiber_segments(synthesis: Synthesis) -> list[tuple[str, str]]:
    return sorted(synthesis.fiber_segment_keys)


def included_demand_count(sites: Iterable[Site], synthesis: Synthesis) -> int:
    included = included_site_ids(synthesis)
    return sum(
        1 for site in sites if not is_carrier_pop(site) and site.id in included
    )


def _demand_path_kind(source_site: Site) -> str:
    return "provider_to_backbone" if source_site.kind == PROVIDER_KIND else "tenant_to_backbone"


def synthesis_payload(sources: SourceFiles, artifacts: SynthesisArtifacts) -> dict[str, Any]:
    sites = artifacts.sites
    fiber_segments = artifacts.fiber_segments
    synthesis = artifacts.synthesis
    validation = artifacts.validation
    sites_by_id = {site.id: site for site in sites}
    return {
        "sites_files": [str(path) for path in sources.site_files],
        "fiber_segment_file": str(sources.fiber_segment_path),
        "objective": (
            "Two-tier WAN synthesis: demand sites (tenant sites and provider regions) home "
            "to a meshed backbone of selected Carrier PoPs over the physical Carrier "
            "graph, with at least three strong backbone nodes and extra ones added "
            "where they bring demand closer."
        ),
        "summary": {
            "backbone_count": len(synthesis.backbone_ids),
            "transit_count": len(synthesis.transit_ids),
            "demand_site_count": included_demand_count(sites, synthesis),
            "access_path_count": len(synthesis.access_paths),
            "fiber_segment_count": len(synthesis.fiber_segment_keys),
            "access_miles": round(synthesis.metrics.access_miles, 3),
            "physical_carrier_miles": round(synthesis.metrics.physical_miles, 3),
            "backbone_lower_bound_miles": round(
                synthesis.metrics.backbone_lower_bound_miles, 3
            ),
            "total_synthesis_miles": round(
                synthesis.metrics.access_miles + synthesis.metrics.physical_miles, 3
            ),
            "score": round(synthesis.metrics.score, 3),
            "backbone_nodes": [
                sites_by_id[site_id].name for site_id in synthesis.backbone_ids
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
        "access_paths": [
            {
                "source_id": access_path.source,
                "source_name": sites_by_id[access_path.source].name,
                "target_id": access_path.target,
                "target_name": sites_by_id[access_path.target].name,
                "link_kind": _demand_path_kind(sites_by_id[access_path.source]),
                "distance_miles": round(access_path.distance_miles, 3),
            }
            for access_path in sorted(
                synthesis.access_paths, key=lambda item: (item.source, item.target)
            )
        ],
        "fiber_segments": [
            {
                "source_id": left,
                "source_name": sites_by_id[left].name,
                "target_id": right,
                "target_name": sites_by_id[right].name,
                "link_kind": "carrier_physical",
                "distance_miles": round(fiber_segments[segment_key(left, right)].distance_miles, 3),
                "source_page": fiber_segments[segment_key(left, right)].source_page,
                "note": fiber_segments[segment_key(left, right)].note,
                "submarine": fiber_segments[segment_key(left, right)].submarine,
            }
            for left, right in sorted_fiber_segments(synthesis)
        ],
        "drawn_paths": [
            {
                "purpose": drawn_path.purpose,
                "source_id": drawn_path.source,
                "source_name": sites_by_id[drawn_path.source].name,
                "target_id": drawn_path.target,
                "target_name": sites_by_id[drawn_path.target].name,
                "distance_miles": round(drawn_path.distance_miles, 3),
                "carrier": drawn_path.carrier,
                "path": [sites_by_id[site_id].name for site_id in drawn_path.path],
                "reason": drawn_path.reason,
                "requested_by": [
                    sites_by_id[site_id].name for site_id in drawn_path.requested_by
                ],
            }
            for drawn_path in synthesis.drawn_paths
        ],
    }
