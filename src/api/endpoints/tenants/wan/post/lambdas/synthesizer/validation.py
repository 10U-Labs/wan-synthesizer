from __future__ import annotations

from collections.abc import Callable, Mapping
from itertools import combinations

from synthesizer.input_graph import Site, segment_key
from synthesizer.model import (
    PATH_FOR_TARGET,
    Synthesis,
    SynthesisPath,
    MeshRequirements,
    ValidationReport,
)
from synthesizer.graphs import (
    articulation_points,
    connected_components,
    survives_any_one_segment_loss,
    survives_any_one_site_loss,
    path_segment_keys,
)


def node_mesh_target(site: str, targets: MeshRequirements) -> int:
    ceilings = targets.ceilings
    if ceilings is None or site not in ceilings:
        return targets.number_of_diverse_paths
    return min(targets.number_of_diverse_paths, ceilings[site])


def backbone_mesh_deficient(
    backbone_ids: tuple[str, ...],
    backbone_degrees: dict[str, int],
    sites_by_id: dict[str, Site],
    targets: MeshRequirements,
) -> list[dict[str, object]]:
    if len(backbone_ids) <= targets.number_of_diverse_paths:
        return []
    return [
        {"id": backbone_id, "name": sites_by_id[backbone_id].name, "degree": degree}
        for backbone_id, degree in sorted(backbone_degrees.items())
        if degree < node_mesh_target(backbone_id, targets)
        and backbone_id not in targets.degree_exempt
    ]


def synthesis_site_pairs(synthesis: Synthesis) -> set[tuple[str, str]]:
    pairs = set(synthesis.fiber_segment_keys)
    pairs.update(
        segment_key(access_path.source, access_path.target)
        for access_path in synthesis.access_paths
    )
    return pairs

def included_site_ids(synthesis: Synthesis) -> set[str]:
    ids = set(synthesis.backbone_ids) | set(synthesis.transit_ids)
    ids.update(site_id for key in synthesis.fiber_segment_keys for site_id in key)
    ids.update(access_path.source for access_path in synthesis.access_paths)
    ids.update(access_path.target for access_path in synthesis.access_paths)
    return ids

def demand_backbone_homes(synthesis: Synthesis) -> dict[str, set[str]]:
    homes: dict[str, set[str]] = {}
    for access_path in synthesis.access_paths:
        homes.setdefault(access_path.source, set()).add(access_path.target)
    return homes

def demand_without_backbone_redundancy(synthesis: Synthesis, homes: int) -> list[str]:
    return [
        demand_id
        for demand_id, targets in sorted(demand_backbone_homes(synthesis).items())
        if len(targets) != homes
    ]

def backbone_mesh_pairs(synthesis: Synthesis) -> set[tuple[str, str]]:
    return {
        segment_key(drawn_path.source, drawn_path.target)
        for drawn_path in synthesis.drawn_paths
        if drawn_path.purpose == "backbone_mesh"
    }

def backbone_mesh_fiber_segments(synthesis: Synthesis) -> set[tuple[str, str]]:
    segments: set[tuple[str, str]] = set()
    for drawn_path in synthesis.drawn_paths:
        if drawn_path.purpose == "backbone_mesh":
            segments |= path_segment_keys(drawn_path.path)
    return segments

def _backbone_mesh_survives(
    synthesis: Synthesis, is_resilient: Callable[[set[str], set[tuple[str, str]]], bool]
) -> bool:
    ids = set(synthesis.backbone_ids)
    if len(ids) < 2:
        return True
    segments = backbone_mesh_fiber_segments(synthesis)
    sites = ids | {site for segment in segments for site in segment}
    return is_resilient(sites, segments)

def backbone_mesh_survives_any_one_link_loss(synthesis: Synthesis) -> bool:
    return _backbone_mesh_survives(synthesis, survives_any_one_segment_loss)

def backbone_mesh_survives_any_one_site_loss(synthesis: Synthesis) -> bool:
    return _backbone_mesh_survives(synthesis, survives_any_one_site_loss)

def paths_out_of(
    drawn_paths: list[SynthesisPath], site: str
) -> list[tuple[str, frozenset[str]]]:
    return [
        (
            drawn_path.target if drawn_path.source == site else drawn_path.source,
            frozenset(drawn_path.path) - {site},
        )
        for drawn_path in drawn_paths
        if drawn_path.purpose == "backbone_mesh" and site in (drawn_path.source, drawn_path.target)
    ]


def _all_disjoint(paths: tuple[tuple[str, frozenset[str]], ...]) -> bool:
    for (near_peer, near), (far_peer, far) in combinations(paths, 2):
        shared = near & far
        if near_peer == far_peer:
            shared -= {near_peer}
        if shared:
            return False
    return True


def diverse_path_count(drawn_paths: list[SynthesisPath], site: str) -> int:
    paths = paths_out_of(drawn_paths, site)
    for size in range(len(paths), 0, -1):
        if any(_all_disjoint(combo) for combo in combinations(paths, size)):
            return size
    return 0


def backbone_mesh_independence_deficient(
    synthesis: Synthesis,
    sites_by_id: dict[str, Site],
    targets: MeshRequirements,
) -> list[dict[str, object]]:
    return [
        {
            "id": backbone_id,
            "name": sites_by_id[backbone_id].name,
            "independent_degree": degree,
        }
        for backbone_id, degree in sorted(
            (site, diverse_path_count(synthesis.drawn_paths, site))
            for site in synthesis.backbone_ids
        )
        if degree < node_mesh_target(backbone_id, targets)
        and backbone_id not in targets.degree_exempt
    ]


def _ceilings_where(
    backbone_ids: tuple[str, ...],
    ceilings: Mapping[str, int] | None,
    keep: Callable[[int], bool],
) -> list[tuple[str, int]]:
    if ceilings is None:
        return []
    return [
        (site, ceilings[site])
        for site in sorted(backbone_ids)
        if site in ceilings and keep(ceilings[site])
    ]


def _ceiling_rows(
    backbone_ids: tuple[str, ...],
    sites_by_id: dict[str, Site],
    ceilings: Mapping[str, int] | None,
    keep: Callable[[int], bool],
) -> list[dict[str, object]]:
    return [
        {"id": site, "name": sites_by_id[site].name, "ceiling": ceiling}
        for site, ceiling in _ceilings_where(backbone_ids, ceilings, keep)
    ]


def diverse_path_ceilings_reported(
    backbone_ids: tuple[str, ...],
    sites_by_id: dict[str, Site],
    targets: MeshRequirements,
) -> list[dict[str, object]]:
    return [
        dict(row, target=node_mesh_target(str(row["id"]), targets))
        for row in _ceiling_rows(
            backbone_ids, sites_by_id, targets.ceilings, lambda _ceiling: True
        )
    ]


def ceiling_limited_nodes(
    backbone_ids: tuple[str, ...],
    sites_by_id: dict[str, Site],
    targets: MeshRequirements,
) -> list[dict[str, object]]:
    return _ceiling_rows(
        backbone_ids, sites_by_id, targets.ceilings,
        lambda value: value < targets.number_of_diverse_paths,
    )


def mesh_paths_out_of(synthesis: Synthesis, site: str) -> list[SynthesisPath]:
    return [
        drawn_path
        for drawn_path in synthesis.drawn_paths
        if drawn_path.purpose == "backbone_mesh" and site in (drawn_path.source, drawn_path.target)
    ]


def unrequested_mesh_paths(synthesis: Synthesis, site: str) -> list[dict[str, object]]:
    unrequested: list[dict[str, object]] = [
        {
            "peer": drawn_path.target if drawn_path.source == site else drawn_path.source,
            "reason": "peer_target" if drawn_path.reason == PATH_FOR_TARGET else drawn_path.reason,
        }
        for drawn_path in mesh_paths_out_of(synthesis, site)
        if not (drawn_path.reason == PATH_FOR_TARGET and site in drawn_path.requested_by)
    ]
    return sorted(unrequested, key=lambda item: (str(item["peer"]), str(item["reason"])))


def above_target_nodes(
    synthesis: Synthesis,
    sites_by_id: dict[str, Site],
    targets: MeshRequirements,
) -> list[dict[str, object]]:
    asked_for = targets.number_of_diverse_paths
    rows: list[dict[str, object]] = []
    for site in sorted(synthesis.backbone_ids):
        paths = mesh_paths_out_of(synthesis, site)
        if len(paths) <= asked_for:
            continue
        rows.append({
            "id": site,
            "name": sites_by_id[site].name,
            "target": asked_for,
            "link_count": len(paths),
            "diverse_path_count": diverse_path_count(synthesis.drawn_paths, site),
            "unrequested_links": unrequested_mesh_paths(synthesis, site),
        })
    return rows


def neighbor_degrees(
    ids: set[str], site_pairs: set[tuple[str, str]]
) -> dict[str, int]:
    neighbors: dict[str, set[str]] = {site_id: set() for site_id in ids}
    for left, right in site_pairs:
        if left in ids and right in ids:
            neighbors[left].add(right)
            neighbors[right].add(left)
    return {site_id: len(value) for site_id, value in neighbors.items()}

def backbone_names_by_group(sites: list[Site], synthesis: Synthesis) -> list[list[str]]:
    names = {site.id: site.name for site in sites}
    seated = set(synthesis.backbone_ids)
    return [
        [names[site_id] for site_id in group if site_id in seated]
        for group in connected_components(
            included_site_ids(synthesis), synthesis_site_pairs(synthesis)
        )
    ]

def validate_synthesis(
    sites: list[Site],
    synthesis: Synthesis,
    access_homing_degree: int = 2,
    targets: MeshRequirements = MeshRequirements(),
) -> ValidationReport:
    sites_by_id = {site.id: site for site in sites}
    ids = included_site_ids(synthesis)
    pairs = synthesis_site_pairs(synthesis)
    components = connected_components(ids, pairs)
    degrees = neighbor_degrees(ids, pairs)
    articulations = articulation_points(ids, pairs) if len(components) == 1 else set()
    missing_redundancy = demand_without_backbone_redundancy(synthesis, access_homing_degree)
    backbone_degrees = neighbor_degrees(set(synthesis.backbone_ids), backbone_mesh_pairs(synthesis))
    mesh_deficient = backbone_mesh_deficient(
        synthesis.backbone_ids, backbone_degrees, sites_by_id, targets
    )
    independence_deficient = backbone_mesh_independence_deficient(
        synthesis, sites_by_id, targets
    )

    return {
        "connected": len(components) == 1,
        "component_count": len(components),
        "min_distinct_neighbor_degree": min(degrees.values()) if degrees else 0,
        "degree_deficient_sites": [
            {"id": site_id, "name": sites_by_id[site_id].name, "degree": degree}
            for site_id, degree in sorted(degrees.items())
            if degree < 2
        ],
        "biconnected_no_articulation_points": len(components) == 1 and not articulations,
        "articulation_points": [
            {"id": site_id, "name": sites_by_id[site_id].name}
            for site_id in sorted(articulations)
        ],
        "access_sites_with_required_backbone_links": not missing_redundancy,
        "demand_missing_backbone_redundancy": [
            {"id": site_id, "name": sites_by_id[site_id].name}
            for site_id in missing_redundancy
        ],
        "backbone_meets_mesh_link_target": not mesh_deficient,
        "backbone_diverse_paths_deficient": mesh_deficient,
        "backbone_meets_independent_mesh_link_target": not independence_deficient,
        "backbone_mesh_independence_deficient": independence_deficient,
        "backbone_degree_exempt": [
            {"id": backbone_id, "name": sites_by_id[backbone_id].name}
            for backbone_id in sorted(set(synthesis.backbone_ids) & targets.degree_exempt)
        ],
        "backbone_diverse_paths_ceilings": diverse_path_ceilings_reported(
            synthesis.backbone_ids, sites_by_id, targets
        ),
        "backbone_diverse_paths_ceiling_limited": ceiling_limited_nodes(
            synthesis.backbone_ids, sites_by_id, targets
        ),
        "backbone_diverse_paths_above_target": above_target_nodes(
            synthesis, sites_by_id, targets
        ),
        "backbone_mesh_survives_any_one_link_loss":
            backbone_mesh_survives_any_one_link_loss(synthesis),
        "backbone_mesh_survives_any_one_site_loss":
            backbone_mesh_survives_any_one_site_loss(synthesis),
    }
