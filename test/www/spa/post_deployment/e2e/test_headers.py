from __future__ import annotations

from http.client import HTTPConnection
from urllib.request import urlopen

import pytest

from repo_utils import REPO_ROOT

SITE = "10ulabs.com"
INDEX = REPO_ROOT / "src" / "www" / "spa" / "index.html"
SPA_PATH = "/wan-synthesizer/"
ONE_YEAR_SECONDS = 31536000


@pytest.fixture(name="served", scope="module")
def served_fixture() -> dict[str, str]:
    with urlopen(f"https://{SITE}{SPA_PATH}", timeout=30) as response:
        return {key.lower(): value for key, value in response.getheaders()}


@pytest.fixture(name="page", scope="module")
def page_fixture() -> str:
    with urlopen(f"https://{SITE}{SPA_PATH}", timeout=30) as response:
        return str(response.read().decode("utf-8"))


@pytest.fixture(name="over_http", scope="module")
def over_http_fixture() -> tuple[int, str]:
    connection = HTTPConnection(SITE, timeout=30)
    try:
        connection.request("GET", SPA_PATH)
        response = connection.getresponse()
        return response.status, response.getheader("Location", "")
    finally:
        connection.close()


def test_the_spa_is_sent_over_https_alone(over_http: tuple[int, str]) -> None:
    assert (over_http[0], over_http[1].startswith("https://")) == (301, True)


def test_the_spa_tells_the_browser_to_stay_on_https_for_a_year(served: dict[str, str]) -> None:
    assert f"max-age={ONE_YEAR_SECONDS}" in served["strict-transport-security"]


def test_the_spa_holds_every_subdomain_to_https(served: dict[str, str]) -> None:
    assert "includeSubDomains" in served["strict-transport-security"]


def test_the_spa_forbids_sniffing_its_content_type(served: dict[str, str]) -> None:
    assert served["x-content-type-options"] == "nosniff"


def test_the_spa_sends_its_referrer_to_the_origin_alone_across_sites(
        served: dict[str, str]) -> None:
    assert served["referrer-policy"] == "strict-origin-when-cross-origin"


def test_the_spa_denies_framing(served: dict[str, str]) -> None:
    assert served["x-frame-options"] == "DENY"


def test_the_page_served_is_the_page_in_the_tree_with_its_content_security_policy(
        page: str) -> None:
    assert page == INDEX.read_text(encoding="utf-8")
