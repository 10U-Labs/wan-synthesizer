from __future__ import annotations


import fixtures
from synthesizer import collections as gc
from synthesizer.model import Homings, Synthesis, SynthesisMetrics


def _synthesis(wan_pop_ids: tuple[str, ...], transit_ids: tuple[str, ...]) -> Synthesis:
    return Synthesis(
        wan_pop_ids, transit_ids, Homings([], []), set(), [],
        SynthesisMetrics(0.0, 0.0, 0.0),
    )


def test_site_role_wan_pop_for_selected_pop() -> None:
    assert gc.site_role(fixtures.carrier_pop("a"), _synthesis(("a",), ())) == "wan_pop"


def test_site_role_transit_for_routing_only_pop() -> None:
    assert gc.site_role(fixtures.carrier_pop("a"), _synthesis((), ("a",))) == "transit"


def test_site_role_unused_for_unselected_pop() -> None:
    assert gc.site_role(fixtures.carrier_pop("a"), _synthesis((), ())) == "unused"


def test_site_role_tenant_for_a_site() -> None:
    assert gc.site_role(fixtures.tenant_site("s"), _synthesis((), ())) == "tenant"


def test_site_role_provider_for_a_provider_region() -> None:
    assert gc.site_role(fixtures.provider_region("r"), _synthesis((), ())) == "provider"
