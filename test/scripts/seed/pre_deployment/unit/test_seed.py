from __future__ import annotations

import sys
import urllib.error
import urllib.request
from email.message import Message
from typing import Any

import pytest

import seed
from test_http_doubles import UrlopenRecorder
from seed import (
    _post_json,
    _send,
    main,
    prune_store,
)

def _reset() -> ConnectionResetError:
    return ConnectionResetError(104, "Connection reset by peer")


def _not_found() -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://api/providers/regions", 404, "Not Found", Message(), None)


def _failing_urlopen(
        monkeypatch: pytest.MonkeyPatch, *failures: BaseException) -> UrlopenRecorder:
    recorder = UrlopenRecorder(body=b'[{"id": "f-35"}]', failures=failures)
    monkeypatch.setattr(urllib.request, "urlopen", recorder)
    return recorder


def _attempts_made(monkeypatch: pytest.MonkeyPatch, failure: BaseException) -> int:
    recorder = _failing_urlopen(monkeypatch, failure)
    try:
        _send("http://api", "providers/regions", "GET", None)
    except OSError:
        pass
    return len(recorder.requests)


@pytest.mark.usefixtures("instant_retry")
def test_send_returns_the_body_when_a_reset_connection_is_tried_again(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _failing_urlopen(monkeypatch, _reset())
    assert _send("http://api", "providers/regions", "GET", None) == b'[{"id": "f-35"}]'


@pytest.mark.usefixtures("instant_retry")
def test_send_tries_a_reset_connection_again_wherever_the_reset_was_raised(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _failing_urlopen(monkeypatch, urllib.error.URLError(_reset()))
    assert _send("http://api", "providers/regions", "GET", None) == b'[{"id": "f-35"}]'


@pytest.mark.usefixtures("instant_retry")
def test_send_raises_when_every_attempt_is_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    _failing_urlopen(monkeypatch, _reset(), _reset())
    with pytest.raises(ConnectionResetError):
        _send("http://api", "providers/regions", "GET", None)


@pytest.mark.usefixtures("instant_retry")
def test_send_says_it_is_trying_a_reset_connection_again(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _failing_urlopen(monkeypatch, _reset())
    _send("http://api", "providers/regions", "GET", None)
    assert "connection reset" in capsys.readouterr().out


def test_send_makes_one_request_when_the_api_answers_first_time(
        urlopen_recorder: UrlopenRecorder) -> None:
    _send("http://api", "providers/regions", "GET", None)
    assert len(urlopen_recorder.requests) == 1


def test_send_does_not_try_an_http_error_again(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _attempts_made(monkeypatch, _not_found()) == 1


def test_send_does_not_try_a_url_error_that_is_not_a_reset_again(
        monkeypatch: pytest.MonkeyPatch) -> None:
    assert _attempts_made(monkeypatch, urllib.error.URLError("Name or service not known")) == 1


def test_send_carries_the_api_key_the_environment_holds(
        urlopen_recorder: UrlopenRecorder, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(seed.API_KEY_VARIABLE, "the-seed-key")
    _send("http://api", "providers/regions", "GET", None)
    assert urlopen_recorder.requests[0].get_header("Authorization") == "Bearer the-seed-key"


def test_send_carries_no_token_when_the_environment_holds_no_key(
        urlopen_recorder: UrlopenRecorder, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(seed.API_KEY_VARIABLE, raising=False)
    _send("http://api", "providers/regions", "GET", None)
    assert urlopen_recorder.requests[0].has_header("Authorization") is False


def test_send_keeps_the_content_type_beside_the_key(
        urlopen_recorder: UrlopenRecorder, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(seed.API_KEY_VARIABLE, "the-seed-key")
    _send("http://api", "providers/regions", "PUT", b"[]")
    assert urlopen_recorder.requests[0].get_header("Content-type") == "application/json"


@pytest.mark.usefixtures("urlopen_recorder")
@pytest.mark.usefixtures("urlopen_recorder")
def test_post_json_decodes_the_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        urllib.request, "urlopen", UrlopenRecorder(body=b'{"deleted": ["csps/a.json"]}'))
    assert _post_json("http://api", "store/prune", {}) == {"deleted": ["csps/a.json"]}


def test_post_json_encodes_the_json_body(urlopen_recorder: UrlopenRecorder) -> None:
    _post_json("http://api", "store/prune", {"written": ["a.json"]})
    assert urlopen_recorder.requests[0].data == b'{"written": ["a.json"]}'


@pytest.mark.usefixtures("urlopen_recorder")
def _prune_answering(
        monkeypatch: pytest.MonkeyPatch, deleted: list[str]) -> list[tuple[str, str, Any]]:
    sent: list[tuple[str, str, Any]] = []

    def _answer(api: str, path: str, body: Any) -> dict[str, list[str]]:
        sent.append((api, path, body))
        return {"deleted": deleted}

    monkeypatch.setattr(seed, "_post_json", _answer)
    return sent


def test_prune_store_posts_the_prune(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = _prune_answering(monkeypatch, [])
    prune_store("http://api")
    assert [(api, path) for api, path, _body in sent] == [("http://api", "store/prune")]


def test_prune_store_names_every_key_that_went(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _prune_answering(monkeypatch, ["csps/aws/vertices.json"])
    prune_store("http://api")
    assert "deleted csps/aws/vertices.json" in capsys.readouterr().out


def test_prune_store_names_nothing_when_the_store_is_already_clean(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _prune_answering(monkeypatch, [])
    prune_store("http://api")
    assert "deleted " not in capsys.readouterr().out


def test_prune_store_survives_an_answer_it_does_not_recognise(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(seed, "_post_json", lambda _api, _path, _body: [])
    prune_store("http://api")
    assert "deleted " not in capsys.readouterr().out


def _run_main(
        monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> list[tuple[str, str]]:
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setattr(
        seed, "prune_store", lambda api: calls.append(("prune-store", api)))
    main()
    return calls


def test_main_defaults_to_the_public_api(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _run_main(monkeypatch, ["seed"])[0] == ("prune-store", seed.DEFAULT_API)


def test_main_uses_the_cli_argument_when_given(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _run_main(monkeypatch, ["seed", "http://custom"])[0][1] == "http://custom"


def test_main_seeds_inputs_then_triggers_builds_in_order(
        monkeypatch: pytest.MonkeyPatch) -> None:
    assert [name for name, _ in _run_main(monkeypatch, ["seed"])] == ["prune-store"]
