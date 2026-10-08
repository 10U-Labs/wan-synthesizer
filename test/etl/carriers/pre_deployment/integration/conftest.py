from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

import pytest

from stub_api import Answer, FakeApi, Listing, StubApi

CARRIERS = "/carriers"
CARRIER = re.compile(r"^/carriers/(\d+)$")
UNDER = re.compile(r"^/carriers/(\d+)/(pops|fiber-segments)$")
POPS = "pops"
FIBER_SEGMENTS = "fiber-segments"


class FakeCarriers(FakeApi):
    def __init__(self, seeded: dict[int, str], phantoms: dict[int, str]) -> None:
        self.carriers: dict[int, str] = dict(seeded)
        self.members: dict[str, dict[int, list[dict[str, Any]]]] = {POPS: {}, FIBER_SEGMENTS: {}}
        self._phantoms = dict(phantoms)
        self._next = max([*seeded, *phantoms, 0]) + 1
        super().__init__(self._held, self._routed)

    def _held(self) -> Listing:
        listed = {**self.carriers, **self._phantoms}
        return [{"id": key, "name": name} for key, name in sorted(listed.items())]

    def _create(self, name: str) -> dict[str, Any]:
        created = self._next
        self._next += 1
        self.carriers[created] = name
        return {"id": created, "name": name}

    def _delete(self, carrier_id: int) -> bool:
        if self._phantoms.pop(carrier_id, None) is not None:
            return False
        return self.carriers.pop(carrier_id, None) is not None

    def _replace(self, carrier_id: int, kind: str, bodies: list[dict[str, Any]]) -> bool:
        if carrier_id not in self.carriers:
            return False
        self.members[kind][carrier_id] = list(bodies)
        return True

    def _routed(self, method: str, path: str, body: Any) -> Answer:
        if (method, path) == ("GET", CARRIERS):
            return 200, self.listing()
        if (method, path) == ("POST", CARRIERS):
            return 201, self._create(body["name"])
        under = UNDER.match(path)
        if method == "PUT" and under and self._replace(int(under.group(1)), under.group(2), body):
            return 200, [{"id": at, **one} for at, one in enumerate(body, start=1)]
        carrier = CARRIER.match(path)
        if method == "DELETE" and carrier and self._delete(int(carrier.group(1))):
            return 204, None
        return 404, {"message": "No such carrier"}


@pytest.fixture
def stub_api() -> Iterator[StubApi]:
    fake = FakeCarriers({3: "vision_net", 5: "vision_net", 6: "dcn"}, {4: "vision_net"})
    with StubApi(fake) as api:
        yield api
