from __future__ import annotations

import subprocess
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from loader import ATTEMPTS, SETTLE_PAUSE_SECONDS
from repo_utils import REPO_ROOT
from etl.regions.load_regions import PROVIDERS, main, regions_of

AT_ONCE = ["--settle-seconds", "0"]
ROUTE = "/hyperscale-cloud-service-provider-regions"


def _run(api: Any, sleep: Any, *arguments: str) -> int:
    return main(["--api", api.url, *arguments], sleep=sleep)


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=repository, capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def _commit(repository: Path, message: str) -> str:
    _git(repository, "add", "--all")
    _git(repository, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message)
    return _git(repository, "rev-parse", "HEAD")


@pytest.fixture(name="repository")
def repository_fixture(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    providers = tmp_path / PROVIDERS
    providers.parent.mkdir(parents=True)
    providers.write_text(
        "Name,Municipality,State,Country,Latitude,Longitude\n"
        "Provider A,Columbus,OH,United States,39.9612,-82.9988\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("first\n", encoding="utf-8")
    _commit(tmp_path, "first")
    (tmp_path / "README.md").write_text("second\n", encoding="utf-8")
    (tmp_path / "unrelated").write_text(_commit(tmp_path, "second"), encoding="utf-8")
    providers.write_text(
        "Name,Municipality,State,Country,Latitude,Longitude\n"
        "Provider A,Columbus,OH,United States,39.9612,-82.9988\n"
        "Provider B,Boardman,OR,United States,45.8396,-119.7006\n", encoding="utf-8")
    _commit(tmp_path, "third")
    return tmp_path


@pytest.mark.usefixtures("the_key")
def test_the_regions_are_loaded(stub_api: Any, sleep: Any) -> None:
    assert _run(stub_api, sleep, *AT_ONCE) == 0


@pytest.mark.usefixtures("the_key")
def test_the_regions_loaded_are_the_csv(stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *AT_ONCE)
    assert list(stub_api.fake.regions.values()) == regions_of(REPO_ROOT)


@pytest.mark.usefixtures("the_key")
def test_the_old_regions_are_gone(stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *AT_ONCE)
    assert sorted(stub_api.fake.regions) == list(range(10, 20))


@pytest.mark.usefixtures("the_key")
def test_the_new_regions_are_built_before_the_old_ones_are_deleted(
        stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *AT_ONCE)
    requests = stub_api.requests
    assert requests.index(("POST", ROUTE)) < requests.index(("DELETE", f"{ROUTE}/4"))


@pytest.mark.usefixtures("the_key")
def test_a_file_changed_since_the_commit_is_loaded(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    since = (repository / "unrelated").read_text(encoding="utf-8")
    _run(stub_api, sleep, "--repository", str(repository), "--since", since, *AT_ONCE)
    assert [body["name"] for body in stub_api.fake.regions.values()] == [
        "Provider A", "Provider B"]


@pytest.mark.usefixtures("the_key")
def test_a_file_unchanged_since_the_commit_touches_nothing(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    _run(stub_api, sleep, "--repository", str(repository), "--since", "HEAD", *AT_ONCE)
    assert stub_api.requests == []


@pytest.mark.usefixtures("the_key")
def test_the_null_commit_means_the_file_is_loaded(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    _run(stub_api, sleep, "--repository", str(repository), "--since", "0" * 40, *AT_ONCE)
    assert len(stub_api.fake.regions) == 2


@pytest.mark.usefixtures("the_key")
def test_a_throttled_call_is_tried_again_after_a_growing_pause(
        stub_api: Any, sleep: Any, pauses: list[float]) -> None:
    stub_api.fake.faults["refusals"] = 2
    _run(stub_api, sleep, *AT_ONCE)
    assert pauses == [1.0, 2.0]


@pytest.mark.usefixtures("the_key")
def test_a_call_throttled_every_time_is_given_up(stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["refusals"] = ATTEMPTS
    with pytest.raises(urllib.error.HTTPError):
        _run(stub_api, sleep, *AT_ONCE)


@pytest.mark.usefixtures("the_key")
def test_a_delete_the_api_fails_stops_the_load(stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["failing_deletes"] = 1
    with pytest.raises(urllib.error.HTTPError):
        _run(stub_api, sleep, *AT_ONCE)


@pytest.mark.usefixtures("the_key")
def test_a_region_already_gone_is_no_failure(stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["stale_reads"] = 1
    del stub_api.fake.regions[9]
    assert _run(stub_api, sleep, *AT_ONCE) == 0


def test_a_refused_key_stops_the_load(
        stub_api: Any, sleep: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "not-the-key")
    with pytest.raises(urllib.error.HTTPError):
        _run(stub_api, sleep, *AT_ONCE)


def test_a_missing_key_is_exit_two(
        stub_api: Any, sleep: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    assert _run(stub_api, sleep, *AT_ONCE) == 2


@pytest.mark.usefixtures("the_key")
def test_a_listing_still_catching_up_is_read_again_after_a_pause(
        stub_api: Any, sleep: Any, pauses: list[float]) -> None:
    stub_api.fake.faults["stale_reads"] = 2
    _run(stub_api, sleep, "--settle-seconds", "10")
    assert pauses == [SETTLE_PAUSE_SECONDS]


@pytest.mark.usefixtures("the_key")
def test_a_listing_that_never_catches_up_is_exit_one(stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["stale_reads"] = 99
    assert _run(stub_api, sleep, *AT_ONCE) == 1
