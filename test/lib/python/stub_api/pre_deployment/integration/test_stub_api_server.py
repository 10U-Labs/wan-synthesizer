from __future__ import annotations

import json
import urllib.request
from collections.abc import Iterator
from typing import Any

import pytest

from stub_api import KEY, Answer, FakeApi, StubApi


def _route(method: str, path: str, body: Any) -> Answer:
    if method == "DELETE":
        return 204, None
    return 200, {"method": method, "path": path, "body": body}


@pytest.fixture(name="served")
def served_fixture() -> Iterator[StubApi]:
    with StubApi(FakeApi(lambda: [], _route)) as served:
        yield served


def _call(served: StubApi, method: str, body: Any = None) -> bytes:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        f"{served.url}/things", data=data, method=method,
        headers={"Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(request, timeout=10) as response:
        answer: bytes = response.read()
    return answer


def test_a_get_is_answered_with_the_json_the_route_gives(served: StubApi) -> None:
    assert json.loads(_call(served, "GET")) == {"method": "GET", "path": "/things", "body": None}


def test_a_post_hands_the_route_its_json_body(served: StubApi) -> None:
    assert json.loads(_call(served, "POST", {"name": "a"}))["body"] == {"name": "a"}


def test_a_put_is_routed_as_a_put(served: StubApi) -> None:
    assert json.loads(_call(served, "PUT", [{"name": "a"}]))["method"] == "PUT"


def test_an_answer_of_nothing_has_an_empty_body(served: StubApi) -> None:
    assert _call(served, "DELETE") == b""


def test_the_requests_served_are_the_fakes_log(served: StubApi) -> None:
    _call(served, "GET")
    assert served.requests == [("GET", "/things")]
