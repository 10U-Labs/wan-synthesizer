from __future__ import annotations

import json
import re
from urllib.parse import urlsplit

from repo_utils import REPO_ROOT

SPA = REPO_ROOT / "src" / "www" / "spa"
COUNTRIES = SPA / "vendor" / "ne_110m_admin_0_countries.js"
COUNTRIES_CONSTANT = "NE_110M_ADMIN_0_COUNTRIES"
PAGE_FILES = ("index.html", "app.js", "style.css")
ORIGINS_THE_PAGE_MAY_REACH = frozenset({
    "10ulabs.com",
    "accounts.google.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
})

_URL = re.compile(r"https?://[^\s\"'`)<>]+")


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


def _shipped_countries() -> dict[str, object]:
    source = COUNTRIES.read_text(encoding="utf-8")
    prefix = f"const {COUNTRIES_CONSTANT} = "
    if not source.startswith(prefix):
        raise AssertionError(f"{COUNTRIES.name} does not declare {COUNTRIES_CONSTANT}")
    loaded: dict[str, object] = json.loads(source[len(prefix):].rstrip().removesuffix(";"))
    return loaded


def test_no_url_on_the_page_leaves_the_origins_it_may_reach() -> None:
    assert [host for host in sorted(_hosts_named_by_the_page()) if not _is_allowed(host)] == []


def test_the_map_draws_no_tile_layer() -> None:
    assert "L.tileLayer(" not in _page("app.js")


def test_the_page_ships_the_countries_before_the_map_draws_them() -> None:
    page = _page("index.html")
    assert 0 < page.find(f'<script src="vendor/{COUNTRIES.name}"></script>') < page.find('<script src="app.js">')


def test_the_map_draws_the_shipped_countries() -> None:
    assert re.search(rf"L\.geoJSON\(\s*{COUNTRIES_CONSTANT}\b", _page("app.js"))


def test_the_shipped_countries_are_a_feature_collection() -> None:
    assert _shipped_countries()["type"] == "FeatureCollection"


def test_the_shipped_countries_cover_the_world() -> None:
    features = _shipped_countries()["features"]
    assert isinstance(features, list) and len(features) == 177
