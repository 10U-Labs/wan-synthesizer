from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

import pytest

from stub_api import Answer, FakeApi, Listing, StubApi

ROUTE = "/hyperscale-cloud-service-provider-regions"
MEMBER = re.compile(rf"^{ROUTE}/(\d+)$")
OLD_REGION = {"name": "Provider Z", "municipality": "Nowhere", "state": "XX",
              "country": "United States", "latitude": 0.0, "longitude": 0.0}


class FakeRegions(FakeApi):
    def __init__(self, seeded: dict[int, dict[str, Any]]) -> None:
        self.regions: dict[int, dict[str, Any]] = dict(seeded)
        self._next = max([*seeded, 0]) + 1
        super().__init__(self._held, self._routed)

    def _held(self) -> Listing:
        return [{"id": key, **body} for key, body in sorted(self.regions.items())]

    def _create(self, body: dict[str, Any]) -> dict[str, Any]:
        created = self._next
        self._next += 1
        self.regions[created] = body
        return {"id": created, **body}

    def _routed(self, method: str, path: str, body: Any) -> Answer:
        if (method, path) == ("GET", ROUTE):
            return 200, self.listing()
        if (method, path) == ("POST", ROUTE):
            return 201, self._create(body)
        member = MEMBER.match(path)
        if method == "DELETE" and member and self.regions.pop(int(member.group(1)), None):
            return 204, None
        return 404, {"message": "No such hyperscale cloud service provider region"}


@pytest.fixture
def stub_api() -> Iterator[StubApi]:
    with StubApi(FakeRegions({4: OLD_REGION, 9: OLD_REGION})) as api:
        yield api
