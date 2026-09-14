from __future__ import annotations

from test_published_syntheses import state_path


def test_the_build_state_is_read_from_the_tenants_wan() -> None:
    assert state_path("daf") == "tenants/daf/wan"
