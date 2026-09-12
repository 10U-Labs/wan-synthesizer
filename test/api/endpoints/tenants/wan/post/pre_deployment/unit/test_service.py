from __future__ import annotations

import fixtures
from synthesizer.model import SynthesisParams
from fixtures import run_synthesis


def test_run_synthesis_is_connected() -> None:
    artifacts = run_synthesis(
        fixtures.ring_sites(), fixtures.ring_fiber_segments(), fixtures.ring_params()
    )
    assert artifacts.validation["connected"] is True


def test_run_synthesis_honors_a_forced_wan_pop() -> None:
    synthesis = run_synthesis(
        fixtures.ring_sites(),
        fixtures.ring_fiber_segments(),
        SynthesisParams(
            min_wan_pop_count=2,
            forced_wan_pop_names=("P3",),
        ),
    ).synthesis
    assert "P3" in synthesis.wan_pop_ids


def test_run_synthesis_selects_a_forced_off_net_site_as_a_wan_pop() -> None:
    site = fixtures.off_net_site("Dulles Hub", 40.5, -100.0)
    synthesis = run_synthesis(
        fixtures.ring_sites(),
        fixtures.ring_fiber_segments(),
        SynthesisParams(
            min_wan_pop_count=2,
            forced_wan_pop_names=("Dulles Hub",),
        ),
        off_net_sites=[site],
    ).synthesis
    assert any(site_id.startswith("offnet_") for site_id in synthesis.wan_pop_ids)
