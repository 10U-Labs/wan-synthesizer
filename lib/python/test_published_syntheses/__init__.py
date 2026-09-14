from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError

from seed import _get


UNFINISHED = frozenset({"creating", "synthesizing"})


def state_path(tenant: str) -> str:
    return f"tenants/{tenant}/wan"


def _build_state(api: str, path: str) -> dict[str, Any]:
    try:
        state: dict[str, Any] = _get(api, path)
    except HTTPError as refusal:
        state = json.loads(refusal.read())
    return state


def published_synthesis(api: str, tenant: str, config: dict[str, Any]) -> dict[str, Any]:
    state = _build_state(api, state_path(tenant))
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
    }
