from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, cast

KEY = "the-key"
REFUSALS = "refusals"
STALE_READS = "stale_reads"
FAILING_DELETES = "failing_deletes"

Answer = tuple[int, Any]
Listing = list[dict[str, Any]]


class FakeApi:
    def __init__(
            self, current: Callable[[], Listing],
            route: Callable[[str, str, Any], Answer]) -> None:
        self.requests: list[tuple[str, str]] = []
        self.faults = {REFUSALS: 0, STALE_READS: 0, FAILING_DELETES: 0}
        self._current = current
        self._route = route
        self._stale = current()

    def _faulted(self, fault: str) -> bool:
        if not self.faults[fault]:
            return False
        self.faults[fault] -= 1
        return True

    def listing(self) -> Listing:
        if self._faulted(STALE_READS):
            return list(self._stale)
        return self._current()

    def answer(self, method: str, path: str, bearer: str | None, body: Any) -> Answer:
        self.requests.append((method, path))
        if self._faulted(REFUSALS):
            return 429, {"message": "Too Many Requests"}
        if bearer != f"Bearer {KEY}":
            return 401, {"message": "Unauthorized"}
        if method == "DELETE" and self._faulted(FAILING_DELETES):
            return 500, {"message": "Failed to delete"}
        return self._route(method, path, body)


class _Handler(BaseHTTPRequestHandler):
    def _serve(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length)) if length else None
        fake = cast("_Server", self.server).fake
        status, answer = fake.answer(
            self.command, self.path, self.headers.get("Authorization"), body)
        encoded = b"" if answer is None else json.dumps(answer).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    do_GET = _serve
    do_POST = _serve
    do_PUT = _serve
    do_DELETE = _serve


class _Server(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, fake: FakeApi) -> None:
        self.fake = fake
        super().__init__(("127.0.0.1", 0), _Handler)


class StubApi:
    def __init__(self, fake: FakeApi) -> None:
        self.fake = fake
        self._server = _Server(fake)
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
