from __future__ import annotations

from typing import Any

import pytest

from stub_api import FAILING_DELETES, KEY, REFUSALS, STALE_READS, Answer, FakeApi, Listing

BEARER = f"Bearer {KEY}"
THINGS = "/things"


@pytest.fixture(name="held")
def held_fixture() -> Listing:
    return [{"id": 1}]


@pytest.fixture(name="routed")
def routed_fixture() -> list[tuple[str, str, Any]]:
    return []


@pytest.fixture(name="fake")
def fake_fixture(held: Listing, routed: list[tuple[str, str, Any]]) -> FakeApi:
    def route(method: str, path: str, body: Any) -> Answer:
        routed.append((method, path, body))
        return 200, {"routed": path}
    return FakeApi(lambda: list(held), route)


def test_every_request_is_logged_by_its_method_and_path(fake: FakeApi) -> None:
    fake.answer("DELETE", f"{THINGS}/3", None, None)
    assert fake.requests == [("DELETE", f"{THINGS}/3")]


def test_a_request_bearing_the_key_is_answered_by_the_route(fake: FakeApi) -> None:
    assert fake.answer("GET", THINGS, BEARER, None) == (200, {"routed": THINGS})


def test_the_route_is_given_the_method_the_path_and_the_body(
        fake: FakeApi, routed: list[tuple[str, str, Any]]) -> None:
    fake.answer("POST", THINGS, BEARER, {"name": "a"})
    assert routed == [("POST", THINGS, {"name": "a"})]


def test_a_request_bearing_another_key_is_unauthorized(fake: FakeApi) -> None:
    assert fake.answer("GET", THINGS, "Bearer another-key", None)[0] == 401


def test_a_refusal_owed_is_answered_too_many_requests(fake: FakeApi) -> None:
    fake.faults[REFUSALS] = 1
    assert fake.answer("GET", THINGS, BEARER, None)[0] == 429


def test_a_refusal_owed_comes_before_the_key_is_checked(fake: FakeApi) -> None:
    fake.faults[REFUSALS] = 1
    assert fake.answer("GET", THINGS, None, None)[0] == 429


def test_a_refusal_owed_is_spent_by_one_request(fake: FakeApi) -> None:
    fake.faults[REFUSALS] = 1
    fake.answer("GET", THINGS, BEARER, None)
    assert fake.answer("GET", THINGS, BEARER, None)[0] == 200


def test_a_failing_delete_owed_is_answered_with_a_server_error(fake: FakeApi) -> None:
    fake.faults[FAILING_DELETES] = 1
    assert fake.answer("DELETE", f"{THINGS}/3", BEARER, None)[0] == 500


def test_a_failing_delete_owed_is_kept_through_a_request_that_deletes_nothing(
        fake: FakeApi) -> None:
    fake.faults[FAILING_DELETES] = 1
    fake.answer("GET", THINGS, BEARER, None)
    assert fake.faults[FAILING_DELETES] == 1


def test_a_failing_delete_owed_is_spent_by_one_delete(fake: FakeApi) -> None:
    fake.faults[FAILING_DELETES] = 1
    fake.answer("DELETE", f"{THINGS}/3", BEARER, None)
    assert fake.answer("DELETE", f"{THINGS}/3", BEARER, None)[0] == 200


def test_the_listing_is_what_the_fake_holds_now(fake: FakeApi, held: Listing) -> None:
    held.append({"id": 2})
    assert fake.listing() == [{"id": 1}, {"id": 2}]


def test_a_stale_read_owed_serves_the_listing_as_the_fake_first_held_it(
        fake: FakeApi, held: Listing) -> None:
    held.append({"id": 2})
    fake.faults[STALE_READS] = 1
    assert fake.listing() == [{"id": 1}]


def test_a_stale_read_owed_is_spent_by_one_listing(fake: FakeApi, held: Listing) -> None:
    held.append({"id": 2})
    fake.faults[STALE_READS] = 1
    fake.listing()
    assert fake.listing() == [{"id": 1}, {"id": 2}]
