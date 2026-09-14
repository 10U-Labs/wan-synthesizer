from __future__ import annotations

import sys
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path
from typing import Any

import pytest

import seed
from test_http_doubles import CallRecorder, UrlopenRecorder
from seed import (
    _carrier_names,
    _post,
    _post_json,
    _put,
    _rows,
    _send,
    _slug,
    build_merged_carriers,
    main,
    prune_store,
    push_carriers,
    push_providers,
)

def _write_csv(path: Path, header: str, *rows: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join((header, *rows)) + "\n", encoding="utf-8")


def _one_carrier(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed, "DATA", tmp_path)
    _write_csv(
        tmp_path / "fiber_segments" / "terrestrial" / "lumen.csv",
        "a_city,z_city", "Reston,Denver")
    _write_csv(
        tmp_path / "pops" / "lumen.csv",
        "Municipality,State", "Reston,VA", "Denver,CO")


def _one_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed, "DATA", tmp_path)
    _write_csv(
        tmp_path / "providers" / "providers.csv", "city,state", "Reston,VA")


def test_slug_replaces_underscores_with_hyphens() -> None:
    assert _slug("f_35") == "f-35"


def test_slug_leaves_a_plain_stem_unchanged() -> None:
    assert _slug("lumen") == "lumen"


def test_rows_lowercases_the_header_keys(tmp_path: Path) -> None:
    path = tmp_path / "v.csv"
    _write_csv(path, "City,State", "Reston,VA")
    assert set(_rows(path)[0]) == {"city", "state"}


def test_rows_parses_latitude_as_float(tmp_path: Path) -> None:
    path = tmp_path / "v.csv"
    _write_csv(path, "city,latitude,longitude", "Reston,38.95,-77.34")
    assert _rows(path)[0]["latitude"] == 38.95


def test_rows_parses_longitude_as_float(tmp_path: Path) -> None:
    path = tmp_path / "v.csv"
    _write_csv(path, "city,latitude,longitude", "Reston,38.95,-77.34")
    assert _rows(path)[0]["longitude"] == -77.34


def test_rows_strips_surrounding_whitespace(tmp_path: Path) -> None:
    path = tmp_path / "v.csv"
    _write_csv(path, "city,state", " Reston , VA ")
    assert _rows(path)[0]["city"] == "Reston"


def test_rows_keeps_string_values_without_coordinates(tmp_path: Path) -> None:
    path = tmp_path / "e.csv"
    _write_csv(path, "a_city,z_city", "Reston,Denver")
    assert _rows(path)[0] == {"a_city": "Reston", "z_city": "Denver"}


def test_rows_raises_for_a_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="does not exist"):
        _rows(tmp_path / "missing.csv")


def test_carrier_names_returns_sorted_stems(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed, "DATA", tmp_path)
    _write_csv(
        tmp_path / "fiber_segments" / "terrestrial" / "lumen.csv", "a_city,z_city", "X,Y")
    _write_csv(
        tmp_path / "fiber_segments" / "submarine" / "lumen.csv", "a_city,z_city", "X,Y")
    _write_csv(
        tmp_path / "fiber_segments" / "terrestrial" / "cogent.csv", "a_city,z_city", "X,Y")
    assert _carrier_names() == ["cogent", "lumen"]


def test_carrier_names_ignores_non_csv_files(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed, "DATA", tmp_path)
    _write_csv(
        tmp_path / "fiber_segments" / "terrestrial" / "lumen.csv", "a_city,z_city", "X,Y")
    (tmp_path / "fiber_segments" / "terrestrial" / "notes.txt").write_text(
        "x", encoding="utf-8")
    assert _carrier_names() == ["lumen"]


def _reset() -> ConnectionResetError:
    return ConnectionResetError(104, "Connection reset by peer")


def _not_found() -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://api/carriers", 404, "Not Found", Message(), None)


def _failing_urlopen(
        monkeypatch: pytest.MonkeyPatch, *failures: BaseException) -> UrlopenRecorder:
    recorder = UrlopenRecorder(body=b'[{"id": "f-35"}]', failures=failures)
    monkeypatch.setattr(urllib.request, "urlopen", recorder)
    return recorder


def _attempts_made(monkeypatch: pytest.MonkeyPatch, failure: BaseException) -> int:
    recorder = _failing_urlopen(monkeypatch, failure)
    try:
        _send("http://api", "carriers", "GET", None)
    except OSError:
        pass
    return len(recorder.requests)


@pytest.mark.usefixtures("instant_retry")
def test_send_returns_the_body_when_a_reset_connection_is_tried_again(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _failing_urlopen(monkeypatch, _reset())
    assert _send("http://api", "carriers", "GET", None) == b'[{"id": "f-35"}]'


@pytest.mark.usefixtures("instant_retry")
def test_send_tries_a_reset_connection_again_wherever_the_reset_was_raised(
        monkeypatch: pytest.MonkeyPatch) -> None:
    _failing_urlopen(monkeypatch, urllib.error.URLError(_reset()))
    assert _send("http://api", "carriers", "GET", None) == b'[{"id": "f-35"}]'


@pytest.mark.usefixtures("instant_retry")
def test_send_raises_when_every_attempt_is_reset(monkeypatch: pytest.MonkeyPatch) -> None:
    _failing_urlopen(monkeypatch, _reset(), _reset())
    with pytest.raises(ConnectionResetError):
        _send("http://api", "carriers", "GET", None)


@pytest.mark.usefixtures("instant_retry")
def test_send_says_it_is_trying_a_reset_connection_again(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    _failing_urlopen(monkeypatch, _reset())
    _send("http://api", "carriers", "GET", None)
    assert "connection reset" in capsys.readouterr().out


def test_send_makes_one_request_when_the_api_answers_first_time(
        urlopen_recorder: UrlopenRecorder) -> None:
    _send("http://api", "carriers", "GET", None)
    assert len(urlopen_recorder.requests) == 1


def test_send_does_not_try_an_http_error_again(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _attempts_made(monkeypatch, _not_found()) == 1


def test_send_does_not_try_a_url_error_that_is_not_a_reset_again(
        monkeypatch: pytest.MonkeyPatch) -> None:
    assert _attempts_made(monkeypatch, urllib.error.URLError("Name or service not known")) == 1


def test_send_carries_the_api_key_the_environment_holds(
        urlopen_recorder: UrlopenRecorder, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(seed.API_KEY_VARIABLE, "the-seed-key")
    _send("http://api", "carriers", "GET", None)
    assert urlopen_recorder.requests[0].get_header("Authorization") == "Bearer the-seed-key"


def test_send_carries_no_token_when_the_environment_holds_no_key(
        urlopen_recorder: UrlopenRecorder, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(seed.API_KEY_VARIABLE, raising=False)
    _send("http://api", "carriers", "GET", None)
    assert urlopen_recorder.requests[0].has_header("Authorization") is False


def test_send_keeps_the_content_type_beside_the_key(
        urlopen_recorder: UrlopenRecorder, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(seed.API_KEY_VARIABLE, "the-seed-key")
    _send("http://api", "carriers", "PUT", b"[]")
    assert urlopen_recorder.requests[0].get_header("Content-type") == "application/json"


def test_put_uses_the_put_method(urlopen_recorder: UrlopenRecorder) -> None:
    _put("http://api", "carriers/lumen/pops", [{"city": "Reston"}])
    assert urlopen_recorder.requests[0].method == "PUT"


def test_put_targets_the_api_path(urlopen_recorder: UrlopenRecorder) -> None:
    _put("http://api", "carriers/lumen/pops", [])
    assert urlopen_recorder.requests[0].full_url == "http://api/carriers/lumen/pops"


def test_put_encodes_the_json_body(urlopen_recorder: UrlopenRecorder) -> None:
    _put("http://api", "carriers/lumen/pops", [{"city": "Reston"}])
    assert urlopen_recorder.requests[0].data == b'[{"city": "Reston"}]'


def test_put_sets_the_json_content_type(urlopen_recorder: UrlopenRecorder) -> None:
    _put("http://api", "carriers/lumen/pops", [])
    assert urlopen_recorder.requests[0].get_header("Content-type") == "application/json"


@pytest.mark.usefixtures("urlopen_recorder")
def test_put_prints_the_response_status(capsys: pytest.CaptureFixture[str]) -> None:
    _put("http://api", "carriers/lumen/pops", [])
    assert "-> 200" in capsys.readouterr().out


def test_post_uses_the_post_method(urlopen_recorder: UrlopenRecorder) -> None:
    _post("http://api", "carriers/merge")
    assert urlopen_recorder.requests[0].method == "POST"


def test_post_targets_the_api_path(urlopen_recorder: UrlopenRecorder) -> None:
    _post("http://api", "carriers/merge")
    assert urlopen_recorder.requests[0].full_url == "http://api/carriers/merge"


def test_post_sends_no_body(urlopen_recorder: UrlopenRecorder) -> None:
    _post("http://api", "carriers/merge")
    assert urlopen_recorder.requests[0].data == b""


@pytest.mark.usefixtures("urlopen_recorder")
def test_post_prints_the_response_status(capsys: pytest.CaptureFixture[str]) -> None:
    _post("http://api", "carriers/merge")
    assert "-> 200" in capsys.readouterr().out


def test_post_json_decodes_the_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        urllib.request, "urlopen", UrlopenRecorder(body=b'{"deleted": ["csps/a.json"]}'))
    assert _post_json("http://api", "store/prune", {}) == {"deleted": ["csps/a.json"]}


def test_post_json_encodes_the_json_body(urlopen_recorder: UrlopenRecorder) -> None:
    _post_json("http://api", "store/prune", {"written": ["a.json"]})
    assert urlopen_recorder.requests[0].data == b'{"written": ["a.json"]}'


@pytest.mark.usefixtures("urlopen_recorder")
def test_put_records_the_key_it_wrote(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(seed, "WRITTEN", set())
    _put("http://api", "carriers/lumen/pops", {})
    assert seed.WRITTEN == {"carriers/lumen/pops.json"}


def test_push_carriers_puts_the_pops_path(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        put_recorder: CallRecorder) -> None:
    _one_carrier(tmp_path, monkeypatch)
    push_carriers("http://api")
    assert "carriers/lumen/pops" in put_recorder.nth(1)


def test_push_carriers_puts_the_fiber_segments_path(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        put_recorder: CallRecorder) -> None:
    _one_carrier(tmp_path, monkeypatch)
    push_carriers("http://api")
    assert "carriers/lumen/fiber-segments" in put_recorder.nth(1)


def test_push_providers_pushes_regions(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        put_recorder: CallRecorder) -> None:
    _one_provider(tmp_path, monkeypatch)
    push_providers("http://api")
    assert "providers/regions" in put_recorder.nth(1)


@pytest.mark.usefixtures("put_recorder")
@pytest.mark.usefixtures("put_recorder")
def test_build_merged_carriers_posts_the_merge(post_recorder: CallRecorder) -> None:
    build_merged_carriers("http://api")
    assert post_recorder.calls == [("http://api", "carriers/merge")]


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


def test_prune_store_sends_the_keys_this_run_wrote(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = _prune_answering(monkeypatch, [])
    monkeypatch.setattr(
        seed, "WRITTEN", {"carriers/lumen/pops.json", "providers/regions.json"})
    prune_store("http://api")
    assert sent[0][2] == {
        "written": ["providers/regions.json", "carriers/lumen/pops.json"]}


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
    monkeypatch.setattr(seed, "push_carriers", lambda api: calls.append(("carriers", api)))
    monkeypatch.setattr(seed, "build_merged_carriers", lambda api: calls.append(("merge", api)))
    monkeypatch.setattr(seed, "push_providers", lambda api: calls.append(("providers", api)))
    monkeypatch.setattr(
        seed, "prune_store", lambda api: calls.append(("prune-store", api)))
    main()
    return calls


def test_main_defaults_to_the_public_api(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _run_main(monkeypatch, ["seed"])[0] == ("carriers", seed.DEFAULT_API)


def test_main_uses_the_cli_argument_when_given(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _run_main(monkeypatch, ["seed", "http://custom"])[0][1] == "http://custom"


def test_main_seeds_inputs_then_triggers_builds_in_order(
        monkeypatch: pytest.MonkeyPatch) -> None:
    assert [name for name, _ in _run_main(monkeypatch, ["seed"])] == [
        "carriers", "merge", "providers", "prune-store"]
