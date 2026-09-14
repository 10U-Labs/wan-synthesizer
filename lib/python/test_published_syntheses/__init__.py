from __future__ import annotations

import json
from collections import deque
from typing import Any
from urllib.error import HTTPError

from seed import _get
from synthesizer.input_graph import Site, haversine_miles


UNFINISHED = frozenset({"creating", "synthesizing"})

COLLECTIONS = (
    "wan-pops",
    "tenant-sites",
    "provider-sites",
)


def request_paths(tenant: str) -> list[str]:
    return [f"tenants/{tenant}/{name}" for name in ("wan", *COLLECTIONS)]


def _build_state(api: str, path: str) -> dict[str, Any]:
    try:
        state: dict[str, Any] = _get(api, path)
    except HTTPError as refusal:
        state = json.loads(refusal.read())
    return state


def published_synthesis(api: str, tenant: str, config: dict[str, Any]) -> dict[str, Any]:
    state_path, *collection_paths = request_paths(tenant)
    state = _build_state(api, state_path)
    published: dict[str, Any] = (
        {path.rsplit("/", 1)[-1]: _get(api, path) for path in collection_paths}
        if state.get("status") == "success" else {}
    )
    backbone = config["backbone"]
    return {
        "tenant": tenant,
        "target_miles": backbone["coverage_target_miles"],
        "number_of_diverse_circuits": backbone["number_of_diverse_circuits"],
        "homing_degree": config["homing"]["degree"],
        "max_wan_pop_count": backbone["wan_pop_count"]["max"],
        "forced": backbone.get("forced", {}).get("wan_pops", []),
        "forced_circuits": backbone.get("forced", {}).get("circuits", []),
        "status": state,
        "lower_bound_miles": state.get("backbone_lower_bound_miles"),
        "wan_pops": published.get("wan-pops", []),
        "tenant_sites": published.get("tenant-sites", []),
        "provider_regions": published.get("provider-sites", []),
    }


def site_from_row(row: dict[str, Any]) -> Site:
    latitude, longitude = row["coords"]
    return Site(row["id"], row["name"], row["kind"], (latitude, longitude))


def homed_sites(synthesis: dict[str, Any]) -> list[dict[str, Any]]:
    tenant_sites: list[dict[str, Any]] = synthesis["tenant_sites"]
    provider_regions: list[dict[str, Any]] = synthesis["provider_regions"]
    return tenant_sites + provider_regions


def worst_haul(synthesis: dict[str, Any]) -> float:
    wan_pop_sites = [site_from_row(row) for row in synthesis["wan_pops"]]
    hauls: list[float] = [
        min(haversine_miles(site_from_row(row), site) for site in wan_pop_sites)
        for row in homed_sites(synthesis)
        if not row["exempt_from_distance_constraint"]
    ]
    return round(max(hauls, default=0.0), 1)


def _joined_to(pairs: list[tuple[str, str]]) -> dict[str, set[str]]:
    joined: dict[str, set[str]] = {}
    for near, far in pairs:
        joined.setdefault(near, set()).add(far)
        joined.setdefault(far, set()).add(near)
    return joined


_ARRIVING = "into "
_LEAVING = "out of "
_SINK = "a peer"


def _joined_by(pairs: set[frozenset[str]]) -> dict[str, set[str]]:
    ends = [sorted(pair) for pair in pairs if len(pair) == 2]
    return _joined_to([(both[0], both[1]) for both in ends])


def _capacity(
    joined: dict[str, set[str]], city: str, peers: frozenset[str]
) -> dict[str, dict[str, int]]:
    left: dict[str, dict[str, int]] = {
        _ARRIVING + place: (
            {_SINK: len(joined[place])} if place in peers else {_LEAVING + place: 1}
        )
        for place in joined
        if place != city
    }
    for place, neighbours in joined.items():
        left[_LEAVING + place] = {_ARRIVING + neighbour: 1 for neighbour in neighbours}
    left[_SINK] = {}
    for tail, heads in list(left.items()):
        for head in heads:
            left.setdefault(head, {}).setdefault(tail, 0)
    return left


def _walk_to_a_peer(
    left: dict[str, dict[str, int]], source: str
) -> dict[str, str] | None:
    came: dict[str, str] = {source: source}
    queue: deque[str] = deque([source])
    while queue:
        tail = queue.popleft()
        for head, spare in left[tail].items():
            if spare > 0 and head not in came:
                came[head] = tail
                if head == _SINK:
                    return came
                queue.append(head)
    return None


def _offered_over(joined: dict[str, set[str]], city: str, peers: frozenset[str]) -> int:
    left = _capacity(joined, city, peers)
    source = _LEAVING + city
    if source not in left:
        return 0
    offered = 0
    came = _walk_to_a_peer(left, source)
    while came is not None:
        head = _SINK
        while head != source:
            tail = came[head]
            left[tail][head] -= 1
            left[head][tail] += 1
            head = tail
        offered += 1
        came = _walk_to_a_peer(left, source)
    return offered


def offered_diverse_circuits(
    fiber: set[frozenset[str]], city: str, peers: frozenset[str]
) -> int:
    return _offered_over(_joined_by(fiber), city, peers)
