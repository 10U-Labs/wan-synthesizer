from __future__ import annotations

import json
import re
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

import pytest

from repo_utils import REPO_ROOT

SPA = REPO_ROOT / "src" / "www" / "spa"
COUNTRIES = SPA / "vendor" / "ne_110m_admin_0_countries.js"
COUNTRIES_CONSTANT = "NE_110M_ADMIN_0_COUNTRIES"
STATES = SPA / "vendor" / "ne_50m_admin_1_us_states.js"
STATES_CONSTANT = "NE_50M_ADMIN_1_US_STATES"
LAYERS = [(COUNTRIES, COUNTRIES_CONSTANT), (STATES, STATES_CONSTANT)]
PAGE_FILES = ("index.html", "app.js", "style.css")
ORIGINS_THE_PAGE_MAY_REACH = frozenset({
    "10ulabs.com",
    "accounts.google.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
})

_URL = re.compile(r"https?://[^\s\"'`)<>;]+")


def _page(name: str) -> str:
    return (SPA / name).read_text(encoding="utf-8")


def _hosts_named_by_the_page() -> set[str]:
    return {
        urlsplit(url).hostname or ""
        for name in PAGE_FILES
        for url in _URL.findall(_page(name))
    }


def _is_allowed(host: str) -> bool:
    return any(
        host == origin or host.endswith(f".{origin}")
        for origin in ORIGINS_THE_PAGE_MAY_REACH
    )


def _shipped(path: Path, constant: str) -> dict[str, object]:
    source = path.read_text(encoding="utf-8")
    prefix = f"const {constant} = "
    if not source.startswith(prefix):
        raise AssertionError(f"{path.name} does not declare {constant}")
    loaded: dict[str, object] = json.loads(source[len(prefix):].rstrip().removesuffix(";"))
    return loaded


def _features(path: Path, constant: str) -> list[dict[str, dict[str, str]]]:
    return cast("list[dict[str, dict[str, str]]]", _shipped(path, constant)["features"])


def _script_at(page: str, name: str) -> int:
    return page.find(f'<script src="{name}"></script>')


def test_no_url_on_the_page_leaves_the_origins_it_may_reach() -> None:
    assert [host for host in sorted(_hosts_named_by_the_page()) if not _is_allowed(host)] == []


def test_the_map_draws_no_tile_layer() -> None:
    assert "L.tileLayer(" not in _page("app.js")


def test_the_page_ships_the_countries_before_the_map_draws_them() -> None:
    page = _page("index.html")
    assert 0 < _script_at(page, f"vendor/{COUNTRIES.name}") < _script_at(page, "app.js")


def test_the_page_ships_the_states_after_the_countries_and_before_the_map_draws_them() -> None:
    page = _page("index.html")
    shipped = [_script_at(page, name) for name in (
        f"vendor/{COUNTRIES.name}", f"vendor/{STATES.name}", "app.js")]
    assert 0 < shipped[0] < shipped[1] < shipped[2]


@pytest.mark.parametrize("path, constant", LAYERS)
def test_the_map_draws_each_shipped_layer(path: Path, constant: str) -> None:
    assert re.search(rf"L\.geoJSON\(\s*{constant}\b", _page("app.js")), path.name


@pytest.mark.parametrize("path, constant", LAYERS)
def test_each_shipped_layer_is_a_feature_collection(path: Path, constant: str) -> None:
    assert _shipped(path, constant)["type"] == "FeatureCollection"


def test_the_shipped_countries_cover_the_world() -> None:
    assert len(_features(COUNTRIES, COUNTRIES_CONSTANT)) == 177


def test_the_shipped_states_are_the_fifty_states_and_the_district() -> None:
    names = {feature["properties"]["name"] for feature in _features(STATES, STATES_CONSTANT)}
    assert (len(names), {"Alaska", "Hawaii", "District of Columbia"} <= names) == (51, True)


def test_every_shipped_state_carries_its_name_alone() -> None:
    kept = {tuple(feature["properties"]) for feature in _features(STATES, STATES_CONSTANT)}
    assert kept == {("name",)}


def test_the_states_are_drawn_over_the_countries_without_hiding_them() -> None:
    assert re.search(r"^const STATE_STYLE = \{[^}]*\bfill: false\b", _page("app.js"), re.M)


def test_the_states_are_drawn_in_their_own_style() -> None:
    drawn = rf"L\.geoJSON\(\s*{STATES_CONSTANT}, \{{\s*style: STATE_STYLE,"
    assert re.search(drawn, _page("app.js"))
