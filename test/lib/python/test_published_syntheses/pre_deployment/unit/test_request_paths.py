from __future__ import annotations

from test_published_syntheses import request_paths


def test_the_build_state_is_asked_for_before_the_collections_it_gates() -> None:
    assert request_paths("daf") == [
        "tenants/daf/wan",
        "tenants/daf/wan-pops",
        "tenants/daf/backbone-circuits",
        "tenants/daf/tenant-sites",
        "tenants/daf/provider-sites",
        "tenants/daf/homing-circuits",
        "tenants/daf/fiber-segments",
    ]
