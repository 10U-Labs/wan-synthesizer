from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from email.message import Message
from io import BytesIO
from typing import Any
from urllib.error import HTTPError

import pytest

from seed import DEFAULT_API
from test_http_doubles import FakeResponse
from test_published_syntheses import published_synthesis

_CONFIG: dict[str, Any] = {
    "backbone": {
        "coverage_target_miles": 200,
        "wan_pop_count": {"max": 6},
        "number_of_diverse_circuits": 2,
        "forced": {
            "circuits": [{"source": "Ashburn, VA", "target": "New York, NY"}],
            "wan_pops": ["Ashburn, VA"],
        },
    },
    "homing": {"degree": 2},
}
_WAN_POP = {"id": "ash", "name": "Ashburn, VA", "kind": "PoP", "coords": [39.0, -77.5]}
_SUCCEEDED = {
    "status": "success",
    "coverage": {"target_miles": 200, "met": True},
    "backbone_lower_bound_miles": 1250.0,
}


def _answering(bodies: dict[str, Any], code: int = 200) -> Callable[..., FakeResponse]:
    def urlopen(request: urllib.request.Request, timeout: float = 0.0) -> FakeResponse:
        del timeout
        path = request.full_url.removeprefix(f"{DEFAULT_API}/")
        body = json.dumps(bodies[path]).encode()
        if code >= 400:
            raise HTTPError(request.full_url, code, "", Message(), BytesIO(body))
        return FakeResponse(code, body)
    return urlopen


def test_a_published_network_is_read_beside_the_demands_its_config_makes(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _answering({
        "tenants/daf/wan": _SUCCEEDED,
        "tenants/daf/wan-pops": [_WAN_POP],
    }))
    assert published_synthesis(DEFAULT_API, "daf", _CONFIG) == {
        "tenant": "daf",
        "target_miles": 200,
        "number_of_diverse_circuits": 2,
        "homing_degree": 2,
        "max_wan_pop_count": 6,
        "forced": ["Ashburn, VA"],
        "forced_circuits": [{"source": "Ashburn, VA", "target": "New York, NY"}],
        "status": _SUCCEEDED,
        "lower_bound_miles": 1250.0,
        "wan_pops": [_WAN_POP],
    }


def test_a_tenant_whose_build_has_not_published_is_read_with_no_network(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _answering({
        "tenants/daf/wan": {"status": "synthesizing", "tenant": "daf"},
    }))
    synthesis = published_synthesis(DEFAULT_API, "daf", _CONFIG)
    assert synthesis["wan_pops"] == []


def test_a_build_the_service_refuses_to_serve_is_read_as_what_it_says_went_wrong(
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", _answering({
        "tenants/daf/wan": {"status": "fail", "reason": "no valid WAN is possible"},
    }, code=422))
    assert published_synthesis(DEFAULT_API, "daf", _CONFIG)["status"] == {
        "status": "fail", "reason": "no valid WAN is possible",
    }
