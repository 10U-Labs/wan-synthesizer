from __future__ import annotations


from synthesizer.codec import PROVIDER_KIND
from synthesizer.input_graph import Site
from synthesizer.model import Synthesis, is_carrier_pop


def site_role(site: Site, synthesis: Synthesis) -> str:
    if not is_carrier_pop(site):
        return "provider" if site.kind == PROVIDER_KIND else "tenant"
    if site.id in synthesis.wan_pop_ids:
        return "wan_pop"
    if site.id in synthesis.transit_ids:
        return "transit"
    return "unused"
