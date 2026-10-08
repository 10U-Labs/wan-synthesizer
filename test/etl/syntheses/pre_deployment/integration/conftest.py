from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

import pytest

from stub_api import Answer, FakeApi, Listing, StubApi

SYNTHESES = "/wan-syntheses"
REGIONS = "/hyperscale-cloud-service-provider-regions"
MEMBER = re.compile(rf"^{SYNTHESES}/(\d+)$")
REGION = {"id": 1, "name": "Provider A", "municipality": "Columbus", "state": "OH",
          "country": "United States", "latitude": 39.9612, "longitude": -82.9988}


class FakeSyntheses(FakeApi):
    def __init__(self, seeded: dict[int, str], running: set[int]) -> None:
        self._next = max([*seeded, 0]) + 1
        self.syntheses: dict[int, str] = dict(seeded)
        self.bodies: dict[int, dict[str, Any]] = {}
        self.running = set(running)
        super().__init__(self._held, self._routed)

    def _held(self) -> Listing:
        return [{"id": key, "label": label} for key, label in sorted(self.syntheses.items())]

    def _create(self, given: dict[str, Any]) -> dict[str, Any]:
        created = self._next
        self._next += 1
        self.syntheses[created] = str(given["label"])
        self.bodies[created] = given
        return {"id": created, "label": given["label"], "status": "creating"}

    def _delete(self, synthesis_id: int) -> int:
        if synthesis_id in self.running:
            return 409
        return 204 if self.syntheses.pop(synthesis_id, None) is not None else 404

    def _routed(self, method: str, path: str, body: Any) -> Answer:
        if (method, path) == ("GET", SYNTHESES):
            return 200, self.listing()
        if (method, path) == ("GET", REGIONS):
            return 200, [REGION]
        if (method, path) == ("POST", SYNTHESES):
            return 201, self._create(body)
        member = MEMBER.match(path)
        if method == "DELETE" and member:
            status = self._delete(int(member.group(1)))
            return status, None if status == 204 else {"message": "refused"}
        return 404, {"message": "No such wan synthesis"}


@pytest.fixture
def stub_api() -> Iterator[StubApi]:
    with StubApi(FakeSyntheses({1: "DAF", 2: "DAF", 3: "Two-PoP"}, {2})) as api:
        yield api
