from __future__ import annotations

import re
from html.parser import HTMLParser

from repo_utils import REPO_ROOT

SPA = REPO_ROOT / "src" / "www" / "spa"
RETIRED_API = "wan-synthesizer"
GOOGLE_SIGN_IN_CLIENT = "https://accounts.google.com/gsi/client"

_FETCHED = re.compile(r"\$\{API_BASE\}/([^`]+)`")
_CONSTANT = r'^const {name} = "([^"]+)";$'
_HIDDEN = "hidden"
_VOID = frozenset({"meta", "link"})


class _Elements(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._open: list[tuple[str, bool]] = []
        self.hidden_by_itself: dict[str, bool] = {}
        self.hidden_by_an_ancestor: dict[str, bool] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id is not None:
            self.hidden_by_itself[element_id] = _HIDDEN in attributes
            self.hidden_by_an_ancestor[element_id] = any(hidden for _, hidden in self._open)
        if tag not in _VOID:
            self._open.append((tag, _HIDDEN in attributes))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if self._open and self._open[-1][0] == tag:
            self._open.pop()


def _app_js() -> str:
    return (SPA / "app.js").read_text(encoding="utf-8")


def _index_html() -> str:
    return (SPA / "index.html").read_text(encoding="utf-8")


def _elements() -> _Elements:
    elements = _Elements()
    elements.feed(_index_html())
    return elements


def _constant(name: str) -> str:
    match = re.search(_CONSTANT.format(name=name), _app_js(), re.M)
    if match is None:
        raise AssertionError(f"app.js declares no {name}")
    return match.group(1)


def _fetched() -> list[str]:
    return _FETCHED.findall(_app_js())


def _fetched_routes() -> list[str]:
    return [path for path in _fetched() if path.startswith(f"{RETIRED_API}/")]


def test_the_page_loads_googles_sign_in_client() -> None:
    assert f'<script src="{GOOGLE_SIGN_IN_CLIENT}"></script>' in _index_html()


def test_the_page_opens_on_the_sign_in_screen() -> None:
    assert _elements().hidden_by_itself["sign-in"] is False


def test_the_page_keeps_the_map_hidden_until_someone_signs_in() -> None:
    assert _elements().hidden_by_an_ancestor["map"] is True


def test_the_page_keeps_the_tenants_hidden_until_someone_signs_in() -> None:
    assert _elements().hidden_by_an_ancestor["tenants"] is True


def test_signing_in_reveals_the_page() -> None:
    assert 'document.getElementById("app").hidden = false;' in _app_js()


def test_the_revealed_map_learns_its_size() -> None:
    assert re.search(r'"app"\)\.hidden = false;\s*map\.invalidateSize\(\);', _app_js())


def test_being_turned_away_hides_the_page_again() -> None:
    assert 'document.getElementById("app").hidden = true;' in _app_js()


def test_the_page_asks_google_for_a_client() -> None:
    assert _constant("GOOGLE_CLIENT_ID").endswith(".apps.googleusercontent.com")


def test_the_page_offers_the_accounts_of_the_hosted_domain() -> None:
    assert _constant("HOSTED_DOMAIN") == "10ulabs.com"


def test_the_map_fetches_something() -> None:
    assert _fetched() != []


def test_the_map_lists_the_syntheses_the_api_serves() -> None:
    assert "wan-syntheses" in _fetched()


def test_the_map_reads_nothing_served_here_any_more() -> None:
    assert _fetched_routes() == []


def test_the_map_shows_each_synthesis_by_its_label() -> None:
    assert "    link.textContent = label;" in _app_js()


def _sign_in_note(status: str) -> str:
    match = re.search(rf"^  {status}: `([^`]+)`,$", _app_js(), re.M)
    if match is None:
        raise AssertionError(f"app.js carries no sign-in note for {status}")
    return match.group(1)


def test_a_turned_away_account_is_told_it_is_not_authorized() -> None:
    assert "not authorized" in _sign_in_note("403")


def test_a_turned_away_account_is_not_told_the_domain_alone_would_admit_it() -> None:
    assert "${HOSTED_DOMAIN}" not in _sign_in_note("403")
