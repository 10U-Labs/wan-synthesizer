from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any, cast
from urllib.parse import urlsplit

from repo_utils import REPO_ROOT
from seed import DEFAULT_API
from test_terraform_config import find_resource, load_tf

SPA = REPO_ROOT / "src" / "www" / "spa"
OPENAPI_SPEC = REPO_ROOT / "src" / "www" / "api" / "openapi.json"
AUTHORIZER_TF = REPO_ROOT / "src" / "api" / "common" / "routing" / "authorizer.tf"
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


def _authorizer_variables() -> dict[str, Any]:
    function = find_resource(load_tf(AUTHORIZER_TF), "aws_lambda_function", "authorizer")
    if function is None:
        raise AssertionError("aws_lambda_function.authorizer is not declared in authorizer.tf")
    variables = cast("dict[str, Any]", function)["environment"][0]["variables"]
    return dict(variables)


def _fetched_routes() -> list[str]:
    prefix = urlsplit(DEFAULT_API).path
    return [
        f"{prefix}/{path.replace('${tenantId}', '{tenant}')}"
        for path in _FETCHED.findall(_app_js())
    ]


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


def test_the_page_asks_google_for_the_client_the_authorizer_expects() -> None:
    assert _constant("GOOGLE_CLIENT_ID") == _authorizer_variables()["GOOGLE_CLIENT_ID"]


def test_the_page_offers_the_accounts_the_authorizer_admits() -> None:
    assert _constant("HOSTED_DOMAIN") == _authorizer_variables()["HOSTED_DOMAIN"]


def test_the_map_fetches_something() -> None:
    assert _fetched_routes() != []


def test_every_route_the_map_fetches_answers_the_browsers_preflight() -> None:
    spec = json.loads(OPENAPI_SPEC.read_text(encoding="utf-8"))
    unanswered = [
        route for route in _fetched_routes()
        if "options" not in spec["paths"].get(route, {})
    ]
    assert unanswered == []


def _sign_in_note(status: str) -> str:
    match = re.search(rf"^  {status}: `([^`]+)`,$", _app_js(), re.M)
    if match is None:
        raise AssertionError(f"app.js carries no sign-in note for {status}")
    return match.group(1)


def test_a_turned_away_account_is_told_it_is_not_authorized() -> None:
    assert "not authorized" in _sign_in_note("403")


def test_a_turned_away_account_is_not_told_the_domain_alone_would_admit_it() -> None:
    assert "${HOSTED_DOMAIN}" not in _sign_in_note("403")
