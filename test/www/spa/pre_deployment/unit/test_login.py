from __future__ import annotations

import json
import re
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


def _app_js() -> str:
    return (SPA / "app.js").read_text(encoding="utf-8")


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
    index = (SPA / "index.html").read_text(encoding="utf-8")
    assert f'<script src="{GOOGLE_SIGN_IN_CLIENT}"></script>' in index


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
