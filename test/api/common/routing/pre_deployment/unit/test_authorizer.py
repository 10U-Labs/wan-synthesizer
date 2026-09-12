from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from email.message import Message
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from test_http_doubles import UrlopenRecorder

_API_KEY = "the-seed-key"
_API = "arn:aws:execute-api:us-east-2:781581267945:abc123"
_EMAIL = "someone@10ulabs.com"


def _claims(**overrides: Any) -> dict[str, Any]:
    return {
        "iss": "https://accounts.google.com",
        "aud": os.environ["GOOGLE_CLIENT_ID"],
        "hd": os.environ["HOSTED_DOMAIN"],
        "email": _EMAIL,
        "email_verified": "true",
        **overrides,
    }


def _fake_ssm(names: list[str]) -> Any:
    def get_parameter(**kwargs: Any) -> dict[str, Any]:
        names.append(kwargs["Name"])
        return {"Parameter": {"Value": _API_KEY}}

    return SimpleNamespace(get_parameter=get_parameter)


def _event(token: str) -> dict[str, Any]:
    return {
        "type": "TOKEN",
        "authorizationToken": token,
        "methodArn": f"{_API}/prod/GET/wan-synthesizer/tenants",
    }


def _refusal() -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://oauth2.googleapis.com/tokeninfo", 400,
                                  "Bad Request", Message(), None)


def _google_says(monkeypatch: pytest.MonkeyPatch, **claims: Any) -> UrlopenRecorder:
    recorder = UrlopenRecorder(body=json.dumps(_claims(**claims)).encode())
    monkeypatch.setattr(urllib.request, "urlopen", recorder)
    return recorder


def _decide(authorizer: Any, token: str, names: list[str] | None = None) -> dict[str, Any]:
    with patch("boto3.client", return_value=_fake_ssm([] if names is None else names)):
        decision: dict[str, Any] = authorizer.lambda_handler(_event(token), None)
    return decision


def _effect(authorizer: Any, token: str) -> str:
    return str(_decide(authorizer, token)["policyDocument"]["Statement"][0]["Effect"])


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
    assert recorder.requests == []


def test_a_verdict_covers_every_method_and_route_of_the_stage(authorizer: Any) -> None:
    statement = _decide(authorizer, f"Bearer {_API_KEY}")["policyDocument"]["Statement"][0]
    assert statement["Resource"] == f"{_API}/prod/*"


def test_a_verdict_is_about_invoking_the_api(authorizer: Any) -> None:
    statement = _decide(authorizer, f"Bearer {_API_KEY}")["policyDocument"]["Statement"][0]
    assert statement["Action"] == "execute-api:Invoke"


def test_a_hosted_domain_account_is_allowed(
        authorizer: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _google_says(monkeypatch)
    assert _effect(authorizer, "Bearer id-token") == "Allow"


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
