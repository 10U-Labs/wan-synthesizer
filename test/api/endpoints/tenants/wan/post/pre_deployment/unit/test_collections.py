from __future__ import annotations

from typing import Any

import fixtures
from synthesizer import collections as gc
from synthesizer.model import Synthesis, SynthesisMetrics
from synthesizer.output import synthesis_payload


def _payload() -> dict[str, Any]:
    return synthesis_payload(fixtures.sample_sources(), fixtures.ring_artifacts())


def _synthesis(backbone_ids: tuple[str, ...], transit_ids: tuple[str, ...]) -> Synthesis:
    return Synthesis(backbone_ids, transit_ids, [], set(), [], SynthesisMetrics(0.0, 0.0, 0.0))


def test_site_role_backbone_for_selected_pop() -> None:
    assert gc.site_role(fixtures.carrier_pop("a"), _synthesis(("a",), ())) == "backbone"


def test_site_role_transit_for_routing_only_pop() -> None:
    assert gc.site_role(fixtures.carrier_pop("a"), _synthesis((), ("a",))) == "transit"


def test_site_role_unused_for_unselected_pop() -> None:
    assert gc.site_role(fixtures.carrier_pop("a"), _synthesis((), ())) == "unused"


def test_site_role_tenant_for_a_site() -> None:
    assert gc.site_role(fixtures.access_site("s"), _synthesis((), ())) == "tenant"


def test_site_role_provider_for_a_provider_region() -> None:
    assert gc.site_role(fixtures.provider_site("r"), _synthesis((), ())) == "provider"


def test_sites_returns_the_payload_sites() -> None:
    payload = _payload()
    assert gc.sites(payload) == payload["sites"]


def test_paths_combines_access_and_carrier_fiber() -> None:
    payload = _payload()
    assert gc.paths(payload) == payload["access_paths"] + payload["fiber_segments"]


def test_backbone_nodes_are_all_tier_backbone() -> None:
    assert all(site["tier_role"] == "backbone" for site in gc.backbone_nodes(_payload()))


def test_tenant_nodes_are_all_tier_tenant() -> None:
    assert all(site["tier_role"] == "tenant" for site in gc.tenant_nodes(_payload()))


def test_provider_nodes_are_all_tier_provider() -> None:
    assert all(site["tier_role"] == "provider" for site in gc.provider_nodes(_payload()))


def test_backbone_links_exist_for_a_meshed_synthesis() -> None:
    assert gc.backbone_links(_payload())


def test_backbone_links_are_all_backbone_mesh_paths() -> None:
    assert all(path["purpose"] == "backbone_mesh" for path in gc.backbone_links(_payload()))


def test_backbone_links_omit_other_drawn_paths() -> None:
    assert gc.backbone_links({"drawn_paths": [{"purpose": "access"}]}) == []


def test_backbone_links_name_both_endpoints() -> None:
    assert all(
        path["source_name"] and path["target_name"] for path in gc.backbone_links(_payload())
    )
