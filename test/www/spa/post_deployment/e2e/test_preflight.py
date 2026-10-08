from __future__ import annotations

from http.client import HTTPSConnection

import pytest

API_HOST = "api.10ulabs.com"
MAP_ORIGIN = "https://www.10ulabs.com"
SYNTHESIS = "preflight"
TABLES = (
    "wan-pops",
    "sites",
    "hyperscale-cloud-service-provider-regions",
    "fiber-segments",
    "homing-circuits",
    "backbone-circuits",
)
ROUTES = ["/wan-syntheses", *(f"/wan-syntheses/{SYNTHESIS}/{table}" for table in TABLES)]
PREFLIGHT = {
    "Origin": MAP_ORIGIN,
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "authorization",
}


@pytest.fixture(name="answer", scope="module", params=ROUTES)
def answer_fixture(request: pytest.FixtureRequest) -> dict[str, str]:
    connection = HTTPSConnection(API_HOST, timeout=30)
    try:
        connection.request("OPTIONS", request.param, headers=PREFLIGHT)
        return {key.lower(): value for key, value in connection.getresponse().getheaders()}
    finally:
        connection.close()


def _listed(answer: dict[str, str], header: str) -> set[str]:
    return {item.strip().lower() for item in answer.get(header, "").split(",")}


def test_the_api_lets_the_maps_origin_read_each_route_it_draws_from(
        answer: dict[str, str]) -> None:
    assert answer.get("access-control-allow-origin") in (MAP_ORIGIN, "*")


def test_the_api_lets_the_map_get_each_route_it_draws_from(answer: dict[str, str]) -> None:
    assert bool(_listed(answer, "access-control-allow-methods") & {"get", "*"})


def test_the_api_lets_the_map_send_its_google_id_token_to_each_route(
        answer: dict[str, str]) -> None:
    assert "authorization" in _listed(answer, "access-control-allow-headers")
