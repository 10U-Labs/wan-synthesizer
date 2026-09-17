from __future__ import annotations

import io
import json
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable
from email.message import Message
from pathlib import Path
from typing import Any

import pytest

from loader import (
    API_KEY_VARIABLE, ATTEMPTS, NO_COMMIT, RETRIED, RETRY_PAUSE_SECONDS, SETTLE_PAUSE_SECONDS, Api,
    changed_paths, key, rows, settled,
)

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


@pytest.fixture(name="pauses")
def pauses_fixture() -> list[float]:
    return []


@pytest.fixture(name="api")
def api_fixture(pauses: list[float]) -> Api:
    return Api(f"{BASE}/", "the-key", pauses.append)


def _refusal(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(BASE, code, "refused", Message(), None)


@pytest.mark.usefixtures("sent")
def test_a_get_answers_the_json_the_api_sends(api: Api, answers: list[Any]) -> None:
    answers.append(b'[{"id": 1}]')
    assert api.get("carriers") == [{"id": 1}]


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


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=repository, capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def _commit(repository: Path, message: str) -> str:
    _git(repository, "add", "--all")
    _git(repository, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message)
    return _git(repository, "rev-parse", "HEAD")


@pytest.fixture(name="history")
def history_fixture(tmp_path: Path) -> tuple[Path, str]:
    _git(tmp_path, "init", "-q")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "a.csv").write_text("A\n1\n", encoding="utf-8")
    (tmp_path / "data" / "b.csv").write_text("B\n1\n", encoding="utf-8")
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc" / "c.yml").write_text("c: 1\n", encoding="utf-8")
    first = _commit(tmp_path, "first")
    (tmp_path / "data" / "a.csv").unlink()
    (tmp_path / "data" / "b.csv").write_text("B\n2\n", encoding="utf-8")
    (tmp_path / "etc" / "c.yml").write_text("c: 2\n", encoding="utf-8")
    _commit(tmp_path, "second")
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
