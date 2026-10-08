from __future__ import annotations

import argparse
import io
import json
import urllib.error
import urllib.request
from collections.abc import Callable
from email.message import Message
from pathlib import Path
from typing import Any

import pytest

from loader import (
    API_KEY_VARIABLE, ATTEMPTS, DEFAULT_API, DEFAULT_SETTLE_SECONDS, DELETED, GONE, NO_COMMIT,
    NO_KEY, RETRIED, RETRY_PAUSE_SECONDS, SETTLE_PAUSE_SECONDS, UNSETTLED, Api, Loaded, Program,
    changed_paths, key, keyed_api, location_body, place_body, removed, rows, run, settled,
    sorted_without_ids, started,
)
from repo_utils import REPO_ROOT
from throwaway_repository import commit, git

BASE = "https://api.example.test"


@pytest.fixture(name="answers")
def answers_fixture() -> list[Any]:
    return []


@pytest.fixture(name="sent")
def sent_fixture(monkeypatch: pytest.MonkeyPatch, answers: list[Any]) -> list[Any]:
    sent: list[Any] = []

    def urlopen(request: urllib.request.Request, timeout: float) -> io.BytesIO:
        sent.append((request, timeout))
        answer = answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return io.BytesIO(answer)
    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    return sent


@pytest.fixture(name="api")
def api_fixture(pauses: list[float]) -> Api:
    return Api(f"{BASE}/", "the-key", pauses.append)


def _refusal(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(BASE, code, "refused", Message(), None)


@pytest.mark.usefixtures("sent")
def test_a_get_answers_the_json_the_api_sends(api: Api, answers: list[Any]) -> None:
    answers.append(b'[{"id": 1}]')
    assert api.get("carriers") == [{"id": 1}]


@pytest.mark.usefixtures("sent")
def test_a_listing_answers_the_rows_the_api_sends(api: Api, answers: list[Any]) -> None:
    answers.append(b'[{"id": 1, "name": "zayo"}]')
    assert api.listing("carriers") == [{"id": 1, "name": "zayo"}]


def test_a_get_is_sent_to_the_base_less_its_trailing_slash(
        api: Api, answers: list[Any], sent: list[Any]) -> None:
    answers.append(b"[]")
    api.get("carriers")
    assert sent[0][0].full_url == f"{BASE}/carriers"


def test_every_call_bears_the_key(api: Api, answers: list[Any], sent: list[Any]) -> None:
    answers.append(b"[]")
    api.get("carriers")
    assert sent[0][0].get_header("Authorization") == "Bearer the-key"


def test_a_post_sends_its_body_as_json(api: Api, answers: list[Any], sent: list[Any]) -> None:
    answers.append(b'{"id": 2}')
    api.post("carriers", {"name": "zayo"})
    assert json.loads(sent[0][0].data) == {"name": "zayo"}


def test_a_post_says_its_body_is_json(api: Api, answers: list[Any], sent: list[Any]) -> None:
    answers.append(b"{}")
    api.post("carriers", {"name": "zayo"})
    assert sent[0][0].get_header("Content-type") == "application/json"


@pytest.mark.usefixtures("sent")
def test_a_post_answers_what_the_api_sends(api: Api, answers: list[Any]) -> None:
    answers.append(b'{"id": 2}')
    assert api.post("carriers", {"name": "zayo"}) == {"id": 2}


def test_a_put_is_sent_as_a_put(api: Api, answers: list[Any], sent: list[Any]) -> None:
    answers.append(b"[]")
    api.put("carriers/2/pops", [])
    assert sent[0][0].get_method() == "PUT"


def test_a_delete_is_sent_as_a_delete(api: Api, answers: list[Any], sent: list[Any]) -> None:
    answers.append(b"")
    api.delete("carriers/2")
    assert sent[0][0].get_method() == "DELETE"


@pytest.mark.usefixtures("sent")
def test_an_empty_answer_is_none(api: Api, answers: list[Any]) -> None:
    answers.append(b"")
    assert api.delete("carriers/2") is None


@pytest.mark.parametrize("code", sorted(RETRIED))
@pytest.mark.usefixtures("sent")
def test_a_throttled_call_is_tried_again(api: Api, answers: list[Any], code: int) -> None:
    answers.extend([_refusal(code), b"[]"])
    assert api.get("carriers") == []


@pytest.mark.usefixtures("sent")
def test_the_pauses_between_tries_grow(api: Api, answers: list[Any], pauses: list[float]) -> None:
    answers.extend([_refusal(429), _refusal(429), _refusal(429), b"[]"])
    api.get("carriers")
    assert pauses == [RETRY_PAUSE_SECONDS * 2 ** n for n in range(3)]


@pytest.mark.usefixtures("sent")
def test_a_call_refused_every_time_is_raised(api: Api, answers: list[Any]) -> None:
    answers.extend([_refusal(503)] * ATTEMPTS)
    with pytest.raises(urllib.error.HTTPError):
        api.get("carriers")


@pytest.fixture(name="exhausted")
def exhausted_fixture(api: Api, answers: list[Any], sent: list[Any]) -> list[Any]:
    answers.extend([_refusal(503)] * ATTEMPTS)
    with pytest.raises(urllib.error.HTTPError):
        api.get("carriers")
    return sent


def test_a_call_is_given_up_after_the_last_try(exhausted: list[Any]) -> None:
    assert len(exhausted) == ATTEMPTS


@pytest.mark.parametrize("code", [400, 401, 403, 404, 500])
@pytest.mark.usefixtures("sent")
def test_a_refusal_that_is_not_throttling_is_raised_at_once(
        api: Api, answers: list[Any], code: int) -> None:
    answers.append(_refusal(code))
    with pytest.raises(urllib.error.HTTPError):
        api.get("carriers")


def test_rows_are_read_by_their_header(tmp_path: Path) -> None:
    path = tmp_path / "rows.csv"
    path.write_text("A,B\n1,2\n3,4\n", encoding="utf-8")
    assert rows(path) == [{"A": "1", "B": "2"}, {"A": "3", "B": "4"}]


def test_the_key_is_read_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(API_KEY_VARIABLE, "the-key")
    assert key() == "the-key"


def test_a_missing_key_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(API_KEY_VARIABLE, raising=False)
    assert key() == ""


def test_the_options_default_to_the_live_api_over_the_whole_repository(
        pauses: list[float]) -> None:
    parsed, _ = started([], pauses.append, "load-test", "Test the shared options.")
    assert (parsed.api, parsed.repository, parsed.since, parsed.settle_seconds) == (
        DEFAULT_API, REPO_ROOT, "", DEFAULT_SETTLE_SECONDS)


def test_the_settle_seconds_are_read_as_a_number(pauses: list[float]) -> None:
    parsed, _ = started(["--settle-seconds", "7"], pauses.append, "load-test", "Test the options.")
    assert parsed.settle_seconds == 7.0


def test_an_appended_option_collects_every_value_given(pauses: list[float]) -> None:
    parsed, _ = started(
        ["--carrier", "zayo", "--carrier", "lumen"], pauses.append, "load-test",
        "Test the options.", ["--carrier"])
    assert parsed.carrier == ["zayo", "lumen"]


def test_the_start_is_keyed_from_the_environment(
        monkeypatch: pytest.MonkeyPatch, pauses: list[float]) -> None:
    monkeypatch.setenv(API_KEY_VARIABLE, "the-key")
    assert isinstance(started([], pauses.append, "load-test", "Test the options.")[1], Api)


def test_a_missing_key_gives_no_api(
        monkeypatch: pytest.MonkeyPatch, pauses: list[float]) -> None:
    monkeypatch.delenv(API_KEY_VARIABLE, raising=False)
    assert keyed_api(BASE, pauses.append) is None


def test_a_missing_key_is_said_on_stderr(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
        pauses: list[float]) -> None:
    monkeypatch.delenv(API_KEY_VARIABLE, raising=False)
    keyed_api(BASE, pauses.append)
    assert capsys.readouterr().err == "the environment carries no key for the API\n"


def test_a_key_gives_an_api(monkeypatch: pytest.MonkeyPatch, pauses: list[float]) -> None:
    monkeypatch.setenv(API_KEY_VARIABLE, "the-key")
    assert isinstance(keyed_api(BASE, pauses.append), Api)


def test_a_place_row_becomes_its_six_location_fields() -> None:
    row = {"Name": "Provider A", "Municipality": "Columbus", "State": "OH",
           "Country": "United States", "Latitude": "39.9612", "Longitude": "-82.9988",
           "ExemptFromDistanceConstraint": "yes"}
    assert place_body(row) == {
        "name": "Provider A", "municipality": "Columbus", "state": "OH",
        "country": "United States", "latitude": 39.9612, "longitude": -82.9988}


def test_a_pop_row_becomes_its_five_location_fields() -> None:
    row = {"Municipality": "Akron", "State": "OH", "Country": "United States",
           "Latitude": "41.0814", "Longitude": "-81.5190"}
    assert location_body(row) == {
        "municipality": "Akron", "state": "OH", "country": "United States",
        "latitude": 41.0814, "longitude": -81.519}


def test_rows_compare_without_their_ids_in_a_fixed_order() -> None:
    served = [{"id": 9, "name": "b", "state": ""}, {"id": 3, "state": "OH", "name": "a"}]
    assert sorted_without_ids(served) == [
        '{"name": "a", "state": "OH"}', '{"name": "b", "state": ""}']


@pytest.fixture(name="history")
def history_fixture(tmp_path: Path) -> tuple[Path, str]:
    git(tmp_path, "init", "-q")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "a.csv").write_text("A\n1\n", encoding="utf-8")
    (tmp_path / "data" / "b.csv").write_text("B\n1\n", encoding="utf-8")
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc" / "c.yml").write_text("c: 1\n", encoding="utf-8")
    first = commit(tmp_path, "first")
    (tmp_path / "data" / "a.csv").unlink()
    (tmp_path / "data" / "b.csv").write_text("B\n2\n", encoding="utf-8")
    (tmp_path / "etc" / "c.yml").write_text("c: 2\n", encoding="utf-8")
    commit(tmp_path, "second")
    return tmp_path, first


def test_the_paths_changed_since_a_commit_are_read_off_the_diff_under_the_paths_named(
        history: tuple[Path, str]) -> None:
    repository, first = history
    assert changed_paths(repository, first, ["data"]) == ["data/a.csv", "data/b.csv"]


def test_a_path_outside_those_named_is_not_a_change(history: tuple[Path, str]) -> None:
    repository, first = history
    assert changed_paths(repository, first, ["etc"]) == ["etc/c.yml"]


def test_no_commit_means_nothing_to_diff_against(history: tuple[Path, str]) -> None:
    repository, _ = history
    assert changed_paths(repository, "", ["data"]) is None


def test_the_null_commit_means_nothing_to_diff_against(history: tuple[Path, str]) -> None:
    repository, _ = history
    assert changed_paths(repository, NO_COMMIT, ["data"]) is None


def _reads(listings: list[list[int]]) -> Callable[[], list[int]]:
    return lambda: listings.pop(0)


def test_a_listing_that_agrees_at_once_is_settled(pauses: list[float]) -> None:
    assert settled(_reads([[1]]), lambda listing: listing == [1], 0, pauses.append) is True


def test_a_listing_that_catches_up_is_read_again_after_a_pause(pauses: list[float]) -> None:
    settled(_reads([[0], [1]]), lambda listing: listing == [1], 10, pauses.append)
    assert pauses == [SETTLE_PAUSE_SECONDS]


def test_a_listing_that_never_catches_up_is_not_settled(pauses: list[float]) -> None:
    listings = [[0]] * 3
    assert settled(_reads(listings), lambda listing: listing == [1], 5, pauses.append) is False


def test_the_polls_are_the_settle_seconds_over_the_pause_plus_one(pauses: list[float]) -> None:
    settled(_reads([[0]] * 4), lambda listing: listing == [1], 10, pauses.append)
    assert len(pauses) == 3


@pytest.mark.usefixtures("sent")
def test_a_delete_answered_is_deleted(api: Api, answers: list[Any]) -> None:
    answers.append(b"")
    assert removed(api, "carriers/3") == DELETED


@pytest.mark.usefixtures("sent")
def test_a_path_already_gone_is_gone(api: Api, answers: list[Any]) -> None:
    answers.append(_refusal(GONE))
    assert removed(api, "carriers/3") == GONE


@pytest.mark.usefixtures("sent")
def test_a_refusal_tolerated_is_answered_by_its_code(api: Api, answers: list[Any]) -> None:
    answers.append(_refusal(409))
    assert removed(api, "wan-syntheses/3", (GONE, 409)) == 409


@pytest.mark.usefixtures("sent")
def test_a_refusal_not_tolerated_stops_the_delete(api: Api, answers: list[Any]) -> None:
    answers.append(_refusal(500))
    with pytest.raises(urllib.error.HTTPError):
        removed(api, "carriers/3")


def _agrees(listing: Any) -> bool:
    return bool(listing == [1])


@pytest.fixture(name="loads")
def loads_fixture() -> list[argparse.Namespace]:
    return []


@pytest.fixture(name="program")
def program_fixture(loads: list[argparse.Namespace]) -> Program:
    def load(args: argparse.Namespace, _api: Api) -> Loaded:
        loads.append(args)
        return Loaded("things", _agrees, "loaded 1 thing")
    return Program("load-test", "Test the run.", load, ["--thing"])


@pytest.fixture(name="idle")
def idle_fixture() -> Program:
    return Program("load-test", "Test the run.", lambda _args, _api: None)


def test_a_run_without_a_key_is_exit_two(
        program: Program, pauses: list[float], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(API_KEY_VARIABLE, raising=False)
    assert run(program, [], pauses.append) == NO_KEY


def test_a_run_without_a_key_loads_nothing(
        program: Program, loads: list[argparse.Namespace], pauses: list[float],
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(API_KEY_VARIABLE, raising=False)
    run(program, [], pauses.append)
    assert loads == []


@pytest.mark.usefixtures("the_key", "sent")
def test_the_load_is_given_the_options_parsed(
        program: Program, loads: list[argparse.Namespace], answers: list[Any],
        pauses: list[float]) -> None:
    answers.append(b"[1]")
    run(program, ["--thing", "zayo", "--settle-seconds", "0"], pauses.append)
    assert loads[0].thing == ["zayo"]


@pytest.mark.usefixtures("the_key", "sent")
def test_a_run_whose_listing_agrees_is_exit_zero(
        program: Program, answers: list[Any], pauses: list[float]) -> None:
    answers.append(b"[1]")
    assert run(program, ["--settle-seconds", "0"], pauses.append) == 0


@pytest.mark.usefixtures("the_key")
def test_the_listing_read_is_the_route_the_load_names(
        program: Program, answers: list[Any], sent: list[Any], pauses: list[float]) -> None:
    answers.append(b"[1]")
    run(program, ["--settle-seconds", "0"], pauses.append)
    assert sent[0][0].full_url == f"{DEFAULT_API}/things"


@pytest.mark.usefixtures("the_key", "sent")
def test_a_run_whose_listing_agrees_says_what_it_loaded(
        program: Program, answers: list[Any], pauses: list[float],
        capsys: pytest.CaptureFixture[str]) -> None:
    answers.append(b"[1]")
    run(program, ["--settle-seconds", "0"], pauses.append)
    assert capsys.readouterr().out == "loaded 1 thing\n"


@pytest.mark.usefixtures("the_key", "sent")
def test_a_run_whose_listing_never_agrees_is_exit_one(
        program: Program, answers: list[Any], pauses: list[float]) -> None:
    answers.append(b"[0]")
    assert run(program, ["--settle-seconds", "0"], pauses.append) == UNSETTLED


@pytest.mark.usefixtures("the_key", "sent")
def test_a_run_whose_listing_never_agrees_says_so_on_stderr(
        program: Program, answers: list[Any], pauses: list[float],
        capsys: pytest.CaptureFixture[str]) -> None:
    answers.append(b"[0]")
    run(program, ["--settle-seconds", "0"], pauses.append)
    assert capsys.readouterr().err == "the listing has not caught up\n"


@pytest.mark.usefixtures("the_key", "sent")
def test_a_run_whose_load_found_nothing_changed_is_exit_zero(
        idle: Program, pauses: list[float]) -> None:
    assert run(idle, [], pauses.append) == 0


@pytest.mark.usefixtures("the_key")
def test_a_run_whose_load_found_nothing_changed_reads_no_listing(
        idle: Program, sent: list[Any], pauses: list[float]) -> None:
    run(idle, [], pauses.append)
    assert sent == []
