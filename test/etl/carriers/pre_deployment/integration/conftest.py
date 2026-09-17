from __future__ import annotations

import json
import re
import threading
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, cast

import pytest

CARRIER = re.compile(r"^/carriers/(\d+)$")
UNDER = re.compile(r"^/carriers/(\d+)/(pops|fiber-segments)$")


class FakeCarriers:
    def __init__(self, seeded: dict[int, str], phantoms: dict[int, str]) -> None:
        self.carriers: dict[int, str] = dict(seeded)
        self.pops: dict[int, list[dict[str, Any]]] = {}
        self.fiber_segments: dict[int, list[dict[str, Any]]] = {}
        self.requests: list[tuple[str, str]] = []
        self.refusals = 0
        self.stale_reads = 0
        self.failing_deletes = 0
        self._phantoms = dict(phantoms)
        self._stale = self.listing()
        self._next = max([*seeded, *phantoms, 0]) + 1

    def listing(self) -> list[dict[str, Any]]:
        if self.stale_reads:
            self.stale_reads -= 1
            return list(self._stale)
        listed = {**self.carriers, **self._phantoms}
        return [{"id": key, "name": name} for key, name in sorted(listed.items())]

    def create(self, name: str) -> dict[str, Any]:
        created = self._next
        self._next += 1
        self.carriers[created] = name
        self.pops[created] = []
        self.fiber_segments[created] = []
        return {"id": created, "name": name}

    def delete(self, carrier_id: int) -> bool:
        if self._phantoms.pop(carrier_id, None) is not None:
            return False
        return self.carriers.pop(carrier_id, None) is not None

    def add(self, carrier_id: int, kind: str, body: dict[str, Any]) -> bool:
        if carrier_id not in self.carriers:
            return False
        held = self.pops if kind == "pops" else self.fiber_segments
        held.setdefault(carrier_id, []).append(body)
        return True


class _Handler(BaseHTTPRequestHandler):
    def _fake(self) -> FakeCarriers:
        return cast("_Server", self.server).fake

    def _answer(self, status: int, body: Any = None) -> None:
        encoded = b"" if body is None else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        loaded: dict[str, Any] = json.loads(self.rfile.read(length))
        return loaded

    def _refused(self) -> bool:
        fake = self._fake()
        fake.requests.append((self.command, self.path))
        if fake.refusals:
            fake.refusals -= 1
            self._answer(429, {"message": "Too Many Requests"})
            return True
        if self.headers.get("Authorization") != "Bearer the-key":
            self._answer(401, {"message": "Unauthorized"})
            return True
        return False

    def _get(self) -> None:
        if self._refused():
            return
        if self.path == "/carriers":
            self._answer(200, self._fake().listing())
        else:
            self._answer(404, {"message": "No such route"})

    def _post(self) -> None:
        if self._refused():
            return
        under = UNDER.match(self.path)
        if self.path == "/carriers":
            self._answer(201, self._fake().create(self._body()["name"]))
        elif under and self._fake().add(int(under.group(1)), under.group(2), self._body()):
            self._answer(201, {})
        else:
            self._answer(404, {"message": "No such carrier"})

    def _delete(self) -> None:
        if self._refused():
            return
        matched = CARRIER.match(self.path)
        if self._fake().failing_deletes:
            self._fake().failing_deletes -= 1
            self._answer(500, {"message": "Failed to delete the carrier"})
        elif matched and self._fake().delete(int(matched.group(1))):
            self._answer(204)
        else:
            self._answer(404, {"message": "No such carrier"})

    do_GET = _get
    do_POST = _post
    do_DELETE = _delete


class _Server(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, fake: FakeCarriers) -> None:
        self.fake = fake
        super().__init__(("127.0.0.1", 0), _Handler)


class StubApi:
    def __init__(self, seeded: dict[int, str], phantoms: dict[int, str]) -> None:
        self.fake = FakeCarriers(seeded, phantoms)
        self._server = _Server(self.fake)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        address = cast("tuple[str, int]", self._server.server_address)
        return f"http://127.0.0.1:{address[1]}"

    @property
    def requests(self) -> list[tuple[str, str]]:
        return self.fake.requests

    def __enter__(self) -> StubApi:
        self._thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture
def stub_api() -> Iterator[StubApi]:
    with StubApi({3: "vision_net", 5: "vision_net", 6: "dcn"}, {4: "vision_net"}) as api:
        yield api


@pytest.fixture
def the_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "the-key")


@pytest.fixture(name="pauses")
def pauses_fixture() -> list[float]:
    return []


@pytest.fixture
def sleep(pauses: list[float]) -> Callable[[float], None]:
    return pauses.append
