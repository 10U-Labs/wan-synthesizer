from __future__ import annotations

import json
import re
import threading
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, cast

import pytest

SYNTHESES = "/wan-syntheses"
REGIONS = "/hyperscale-cloud-service-provider-regions"
MEMBER = re.compile(rf"^{SYNTHESES}/(\d+)$")
REFUSALS = "refusals"
STALE_READS = "stale_reads"
FAILING_DELETES = "failing_deletes"
REGION = {"id": 1, "name": "Provider A", "municipality": "Columbus", "state": "OH",
          "country": "United States", "latitude": 39.9612, "longitude": -82.9988}


class FakeSyntheses:
    def __init__(self, seeded: dict[int, str], running: set[int]) -> None:
        self.syntheses: dict[int, str] = dict(seeded)
        self.bodies: dict[int, dict[str, Any]] = {}
        self.requests: list[tuple[str, str]] = []
        self.faults = {REFUSALS: 0, STALE_READS: 0, FAILING_DELETES: 0}
        self.running = set(running)
        self._stale = self.listing()
        self._next = max([*seeded, 0]) + 1

    def faulted(self, fault: str) -> bool:
        if not self.faults[fault]:
            return False
        self.faults[fault] -= 1
        return True

    def listing(self) -> list[dict[str, Any]]:
        if self.faulted(STALE_READS):
            return list(self._stale)
        return [{"id": key, "label": label} for key, label in sorted(self.syntheses.items())]

    def create(self, given: dict[str, Any]) -> dict[str, Any]:
        created = self._next
        self._next += 1
        self.syntheses[created] = str(given["label"])
        self.bodies[created] = given
        return {"id": created, "label": given["label"], "status": "creating"}

    def delete(self, synthesis_id: int) -> int:
        if synthesis_id in self.running:
            return 409
        return 204 if self.syntheses.pop(synthesis_id, None) is not None else 404


class _Handler(BaseHTTPRequestHandler):
    def _fake(self) -> FakeSyntheses:
        return cast("_Server", self.server).fake

    def _answer(self, status: int, body: Any = None) -> None:
        encoded = b"" if body is None else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _refused(self) -> bool:
        fake = self._fake()
        fake.requests.append((self.command, self.path))
        if fake.faulted(REFUSALS):
            self._answer(429, {"message": "Too Many Requests"})
            return True
        if self.headers.get("Authorization") != "Bearer the-key":
            self._answer(401, {"message": "Unauthorized"})
            return True
        return False

    def _get(self) -> None:
        if self._refused():
            return
        if self.path == SYNTHESES:
            self._answer(200, self._fake().listing())
        elif self.path == REGIONS:
            self._answer(200, [REGION])
        else:
            self._answer(404, {"message": "No such route"})

    def _post(self) -> None:
        if self._refused():
            return
        if self.path == SYNTHESES:
            length = int(self.headers.get("Content-Length", "0"))
            self._answer(201, self._fake().create(json.loads(self.rfile.read(length))))
        else:
            self._answer(404, {"message": "No such route"})

    def _delete(self) -> None:
        if self._refused():
            return
        matched = MEMBER.match(self.path)
        if self._fake().faulted(FAILING_DELETES):
            self._answer(500, {"message": "Failed to delete the wan synthesis"})
        elif matched:
            status = self._fake().delete(int(matched.group(1)))
            self._answer(status, None if status == 204 else {"message": "refused"})
        else:
            self._answer(404, {"message": "No such wan synthesis"})

    do_GET = _get
    do_POST = _post
    do_DELETE = _delete


class _Server(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, fake: FakeSyntheses) -> None:
        self.fake = fake
        super().__init__(("127.0.0.1", 0), _Handler)


class StubApi:
    def __init__(self, seeded: dict[int, str], running: set[int]) -> None:
        self.fake = FakeSyntheses(seeded, running)
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
    with StubApi({1: "DAF", 2: "DAF", 3: "Two-PoP"}, {2}) as api:
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
