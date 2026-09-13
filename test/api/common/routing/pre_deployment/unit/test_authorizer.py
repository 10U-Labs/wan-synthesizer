from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from email.message import Message
from fnmatch import fnmatchcase
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from repo_utils import REPO_ROOT
from seed import ETC, _carrier_names, _slug, main
from test_http_doubles import UrlopenRecorder

_API_KEY = "the-seed-key"
_API = "arn:aws:execute-api:us-east-2:781581267945:abc123"
_STAGE = f"{_API}/prod"
_STALE_TENANT = "stale"
_EMAIL = "someone@10ulabs.com"
_ANOTHER = "another@10ulabs.com"
_AUTHORIZED = f"{_EMAIL}, {_ANOTHER}"


def _claims(**overrides: Any) -> dict[str, Any]:
    return {
        "iss": "https://accounts.google.com",
        "aud": os.environ["GOOGLE_CLIENT_ID"],
        "hd": os.environ["HOSTED_DOMAIN"],
        "email": _EMAIL,
        "email_verified": "true",
        **overrides,
    }


def _fake_ssm(names: list[str], authorized: str = _AUTHORIZED) -> Any:
    values = {
        os.environ["API_KEY_PARAMETER"]: _API_KEY,
        os.environ["AUTHORIZED_ACCOUNTS_PARAMETER"]: authorized,
    }

    def get_parameter(**kwargs: Any) -> dict[str, Any]:
        names.append(kwargs["Name"])
        return {"Parameter": {"Value": values[kwargs["Name"]]}}

    return SimpleNamespace(get_parameter=get_parameter)


def _event(token: str) -> dict[str, Any]:
    return {
        "type": "TOKEN",
        "authorizationToken": token,
        "methodArn": f"{_STAGE}/GET/wan-synthesizer/tenants",
    }


def _refusal() -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://oauth2.googleapis.com/tokeninfo", 400,
                                  "Bad Request", Message(), None)


def _google_says(monkeypatch: pytest.MonkeyPatch, **claims: Any) -> UrlopenRecorder:
    recorder = UrlopenRecorder(body=json.dumps(_claims(**claims)).encode())
    monkeypatch.setattr(urllib.request, "urlopen", recorder)
    return recorder


def _decide(authorizer: Any, token: str, names: list[str] | None = None,
            authorized: str = _AUTHORIZED) -> dict[str, Any]:
    ssm = _fake_ssm([] if names is None else names, authorized)
    with patch("boto3.client", return_value=ssm):
        decision: dict[str, Any] = authorizer.lambda_handler(_event(token), None)
    return decision


def _effect(authorizer: Any, token: str, authorized: str = _AUTHORIZED) -> str:
    decision = _decide(authorizer, token, authorized=authorized)
    return str(decision["policyDocument"]["Statement"][0]["Effect"])


def test_the_api_key_is_allowed(authorizer: Any) -> None:
    assert _effect(authorizer, f"Bearer {_API_KEY}") == "Allow"


def test_the_api_key_is_named_as_the_principal(authorizer: Any) -> None:
    assert _decide(authorizer, f"Bearer {_API_KEY}")["principalId"] == "api-key"


def test_the_api_key_is_read_from_the_parameter_the_environment_names(
        authorizer: Any) -> None:
    names: list[str] = []
    _decide(authorizer, f"Bearer {_API_KEY}", names)
    assert names == [os.environ["API_KEY_PARAMETER"]]


def test_the_api_key_is_settled_without_asking_google(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = _google_says(monkeypatch)
    _decide(authorizer, f"Bearer {_API_KEY}")
    assert not recorder.requests


def _resources(authorizer: Any, token: str) -> list[str]:
    statement = _decide(authorizer, token)["policyDocument"]["Statement"][0]
    resource = statement["Resource"]
    return [str(entry) for entry in ([resource] if isinstance(resource, str) else resource)]


def _granted(resources: list[str], method: str, path: str) -> bool:
    return any(fnmatchcase(f"{_STAGE}/{method}/{path}", resource) for resource in resources)


def _operations_served() -> set[tuple[str, str]]:
    spec = json.loads((REPO_ROOT / "src" / "www" / "api" / "openapi.json").read_text())
    return {
        (method.upper(), path.lstrip("/"))
        for path, operations in spec["paths"].items()
        for method in operations
        if method != "options"
    }


def _ids_the_seed_names() -> frozenset[str]:
    carriers = {_slug(name) for name in _carrier_names()}
    tenants = {_slug(path.stem) for path in ETC.glob("*.yml")}
    return frozenset(carriers | tenants | {_STALE_TENANT})


def _generalized(path: str, ids: frozenset[str]) -> str:
    return "/".join("*" if segment in ids else segment for segment in path.split("/"))


def _writes_the_seed_makes(monkeypatch: pytest.MonkeyPatch) -> set[tuple[str, str]]:
    api = "http://api"
    recorder = UrlopenRecorder(body=json.dumps([{"id": _STALE_TENANT}]).encode())
    monkeypatch.setattr(urllib.request, "urlopen", recorder)
    monkeypatch.setattr(sys, "argv", ["seed", api])
    main()
    ids = _ids_the_seed_names()
    return {
        (request.get_method(), _generalized(path, ids))
        for request, path in zip(recorder.requests, recorder.paths(api))
        if request.get_method() != "GET"
    }


def _writes_the_key_is_granted(authorizer: Any) -> set[tuple[str, str]]:
    prefix = f"{_STAGE}/"
    granted: set[tuple[str, str]] = set()
    for resource in _resources(authorizer, f"Bearer {_API_KEY}"):
        method, _, path = resource[len(prefix):].partition("/")
        if method != "GET":
            granted.add((method, path[len(f"{authorizer.BASE_PATH}/"):]))
    return granted


def test_a_google_verdict_covers_every_method_and_route_of_the_stage(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch)
    assert _resources(authorizer, "Bearer id-token") == [f"{_STAGE}/*"]


def test_a_google_verdict_covers_every_operation_the_api_serves(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch)
    resources = _resources(authorizer, "Bearer id-token")
    assert all(_granted(resources, method, path) for method, path in _operations_served())


def test_the_api_key_verdict_reads_every_route(authorizer: Any) -> None:
    resources = _resources(authorizer, f"Bearer {_API_KEY}")
    reads = {(method, path) for method, path in _operations_served() if method == "GET"}
    assert all(_granted(resources, method, path) for method, path in reads)


def test_the_api_key_verdict_writes_exactly_what_the_seed_writes(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    assert _writes_the_key_is_granted(authorizer) == _writes_the_seed_makes(monkeypatch)


def test_every_grant_to_the_api_key_sits_under_the_base_path(authorizer: Any) -> None:
    resources = _resources(authorizer, f"Bearer {_API_KEY}")
    assert all(f"{_STAGE}/" in resource and f"/{authorizer.BASE_PATH}/" in resource
               for resource in resources)


def test_the_api_key_cannot_delete_a_carrier(authorizer: Any) -> None:
    resources = _resources(authorizer, f"Bearer {_API_KEY}")
    assert not _granted(resources, "DELETE", f"{authorizer.BASE_PATH}/carriers/level3")


def test_the_api_key_cannot_delete_the_provider_regions(authorizer: Any) -> None:
    resources = _resources(authorizer, f"Bearer {_API_KEY}")
    assert not _granted(resources, "DELETE", f"{authorizer.BASE_PATH}/providers/regions")


def test_the_api_key_can_delete_a_tenant(authorizer: Any) -> None:
    resources = _resources(authorizer, f"Bearer {_API_KEY}")
    assert _granted(resources, "DELETE", f"{authorizer.BASE_PATH}/tenants/f-35")


def test_every_route_the_api_serves_sits_under_the_base_path(authorizer: Any) -> None:
    assert all(path.startswith(f"{authorizer.BASE_PATH}/") for _, path in _operations_served())


def test_a_verdict_is_about_invoking_the_api(authorizer: Any) -> None:
    statement = _decide(authorizer, f"Bearer {_API_KEY}")["policyDocument"]["Statement"][0]
    assert statement["Action"] == "execute-api:Invoke"


def test_a_hosted_domain_account_on_the_list_is_allowed(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch)
    assert _effect(authorizer, "Bearer id-token") == "Allow"


def test_a_hosted_domain_account_off_the_list_is_denied(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch, email="stranger@10ulabs.com")
    assert _effect(authorizer, "Bearer id-token") == "Deny"


def test_an_empty_list_admits_nobody(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch)
    assert _effect(authorizer, "Bearer id-token", authorized="") == "Deny"


def test_a_listed_account_is_matched_whole_and_not_as_a_suffix(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch, email="one@10ulabs.com")
    assert _effect(authorizer, "Bearer id-token") == "Deny"


def test_a_listed_account_is_matched_regardless_of_case(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch, email="Someone@10ulabs.com")
    assert _effect(authorizer, "Bearer id-token") == "Allow"


def test_every_entry_of_the_list_is_read_past_its_spacing(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch, email=_ANOTHER)
    assert _effect(authorizer, "Bearer id-token") == "Allow"


def test_a_listed_account_off_the_hosted_domain_is_still_denied(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch, hd="example.com")
    assert _effect(authorizer, "Bearer id-token") == "Deny"


def test_the_list_is_read_from_the_parameter_the_environment_names(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch)
    names: list[str] = []
    _decide(authorizer, "Bearer id-token", names)
    assert names == [os.environ["API_KEY_PARAMETER"], os.environ["AUTHORIZED_ACCOUNTS_PARAMETER"]]


def test_the_api_key_is_settled_without_reading_the_list(authorizer: Any) -> None:
    names: list[str] = []
    _decide(authorizer, f"Bearer {_API_KEY}", names)
    assert os.environ["AUTHORIZED_ACCOUNTS_PARAMETER"] not in names


def test_the_account_is_named_as_the_principal(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch)
    assert _decide(authorizer, "Bearer id-token")["principalId"] == _EMAIL


def test_google_is_asked_about_the_token_that_was_presented(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = _google_says(monkeypatch)
    _decide(authorizer, "Bearer id-token")
    assert recorder.requests[0].full_url == (
        "https://oauth2.googleapis.com/tokeninfo?id_token=id-token")


def test_an_account_outside_the_hosted_domain_is_denied(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch, hd="example.com")
    assert _effect(authorizer, "Bearer id-token") == "Deny"


def test_an_account_with_no_hosted_domain_is_denied(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    claims = {key: value for key, value in _claims().items() if key != "hd"}
    monkeypatch.setattr(urllib.request, "urlopen",
                        UrlopenRecorder(body=json.dumps(claims).encode()))
    assert _effect(authorizer, "Bearer id-token") == "Deny"


def test_an_unverified_address_is_denied(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch, email_verified="false")
    assert _effect(authorizer, "Bearer id-token") == "Deny"


def test_a_token_minted_for_another_client_is_unauthorized(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch, aud="other.apps.googleusercontent.com")
    with pytest.raises(Exception, match="^Unauthorized$"):
        _decide(authorizer, "Bearer id-token")


def test_a_token_from_another_issuer_is_unauthorized(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch, iss="https://example.com")
    with pytest.raises(Exception, match="^Unauthorized$"):
        _decide(authorizer, "Bearer id-token")


def test_a_token_google_refuses_is_unauthorized(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", UrlopenRecorder(failures=[_refusal()]))
    with pytest.raises(Exception, match="^Unauthorized$"):
        _decide(authorizer, "Bearer expired")


@pytest.mark.parametrize("header", ["", "Bearer", "Bearer ", "Basic abc", _API_KEY])
def test_anything_but_a_bearer_token_is_unauthorized(authorizer: Any, header: str) -> None:
    with pytest.raises(Exception, match="^Unauthorized$"):
        _decide(authorizer, header)
