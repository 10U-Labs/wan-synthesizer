from __future__ import annotations

import subprocess
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from repo_utils import REPO_ROOT
from etl.carriers.load_carriers import (
    ATTEMPTS, SETTLE_PAUSE_SECONDS, changed_carriers, fiber_segments_of, main, pops_of,
)

VISION_NET = ["--carrier", "vision_net"]
AT_ONCE = ["--settle-seconds", "0"]


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


def _write(repository: Path, relative: str, text: str) -> None:
    path = repository / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture(name="repository")
def repository_fixture(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _write(tmp_path, "data/pops/alpha.csv", "Municipality,State,Country,Latitude,Longitude\n"
           "Akron,OH,United States,41.0814,-81.5190\n")
    _write(tmp_path, "data/fiber_segments/terrestrial/beta.csv",
           "A_Municipality,A_State,Z_Municipality,Z_State\nLeeds,AL,Memphis,TN\n")
    _write(tmp_path, "data/providers/providers.csv", "Name\n")
    first = _commit(tmp_path, "first")
    _write(tmp_path, "data/fiber_segments/submarine/beta.csv",
           "A_Municipality,A_State,Z_Municipality,Z_State\nLondon,,Paris,\n")
    (tmp_path / "data" / "pops" / "alpha.csv").unlink()
    _write(tmp_path, "data/providers/providers.csv", "Name\nchanged\n")
    _commit(tmp_path, "second")
    (tmp_path / "since").write_text(first, encoding="utf-8")
    return tmp_path


@pytest.mark.usefixtures("the_key")
def test_the_named_carrier_is_loaded(stub_api: Any, sleep: Any) -> None:
    assert _run(stub_api, sleep, *VISION_NET, *AT_ONCE) == 0


@pytest.mark.usefixtures("the_key")
def test_the_stale_copies_are_gone_and_the_new_one_is_listed(
        stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *VISION_NET, *AT_ONCE)
    assert stub_api.fake.carriers == {6: "dcn", 7: "vision_net"}


@pytest.mark.usefixtures("the_key")
def test_the_pops_loaded_are_the_csv(stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *VISION_NET, *AT_ONCE)
    assert stub_api.fake.members["pops"][7] == pops_of(REPO_ROOT, "vision_net")


@pytest.mark.usefixtures("the_key")
def test_the_fiber_segments_loaded_are_the_csv(stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *VISION_NET, *AT_ONCE)
    assert stub_api.fake.members["fiber-segments"][7] == fiber_segments_of(REPO_ROOT, "vision_net")


@pytest.mark.usefixtures("the_key")
def test_the_new_carrier_is_built_before_the_old_ones_are_deleted(
        stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *VISION_NET, *AT_ONCE)
    requests = stub_api.requests
    assert requests.index(("POST", "/carriers")) < requests.index(("DELETE", "/carriers/3"))


@pytest.mark.usefixtures("the_key")
def test_a_carrier_whose_data_is_gone_is_deleted_and_not_built(
        stub_api: Any, sleep: Any, tmp_path: Path) -> None:
    _run(stub_api, sleep, "--carrier", "dcn", "--repository", str(tmp_path), *AT_ONCE)
    assert stub_api.fake.carriers == {3: "vision_net", 5: "vision_net"}


@pytest.mark.usefixtures("the_key")
def test_every_carrier_is_loaded_when_none_is_named(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    _run(stub_api, sleep, "--repository", str(repository), *AT_ONCE)
    assert sorted(stub_api.fake.carriers.values()) == ["beta", "dcn", "vision_net", "vision_net"]


@pytest.mark.usefixtures("the_key")
def test_only_the_carriers_changed_since_the_commit_are_loaded(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    since = (repository / "since").read_text(encoding="utf-8")
    _run(stub_api, sleep, "--repository", str(repository), "--since", since, *AT_ONCE)
    assert [request for request in stub_api.requests if request[0] == "POST"] == [
        ("POST", "/carriers"), ("POST", "/carriers/7/fiber-segments"),
        ("POST", "/carriers/7/fiber-segments")]


@pytest.mark.usefixtures("the_key")
def test_the_null_commit_means_every_carrier(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    _run(stub_api, sleep, "--repository", str(repository), "--since", "0" * 40, *AT_ONCE)
    assert "beta" in stub_api.fake.carriers.values()


def test_the_carriers_changed_are_read_off_the_diff_deletions_included(repository: Path) -> None:
    since = (repository / "since").read_text(encoding="utf-8")
    assert changed_carriers(repository, since) == {"alpha", "beta"}


@pytest.mark.usefixtures("the_key")
def test_a_throttled_call_is_tried_again_after_a_growing_pause(
        stub_api: Any, sleep: Any, pauses: list[float]) -> None:
    stub_api.fake.faults["refusals"] = 2
    _run(stub_api, sleep, *VISION_NET, *AT_ONCE)
    assert pauses == [1.0, 2.0]


@pytest.mark.usefixtures("the_key")
def test_a_call_throttled_every_time_is_given_up(
        stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["refusals"] = ATTEMPTS
    with pytest.raises(urllib.error.HTTPError):
        _run(stub_api, sleep, *VISION_NET, *AT_ONCE)


@pytest.mark.usefixtures("the_key")
def test_a_delete_the_api_fails_stops_the_load(
        stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["failing_deletes"] = 1
    with pytest.raises(urllib.error.HTTPError):
        _run(stub_api, sleep, *VISION_NET, *AT_ONCE)


def test_a_refused_key_stops_the_load(
        stub_api: Any, sleep: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "not-the-key")
    with pytest.raises(urllib.error.HTTPError):
        _run(stub_api, sleep, *VISION_NET, *AT_ONCE)


def test_a_missing_key_is_exit_two(
        stub_api: Any, sleep: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    assert _run(stub_api, sleep, *VISION_NET, *AT_ONCE) == 2


@pytest.mark.usefixtures("the_key")
def test_a_listing_still_catching_up_is_read_again_after_a_pause(
        stub_api: Any, sleep: Any, pauses: list[float]) -> None:
    stub_api.fake.faults["stale_reads"] = 2
    _run(stub_api, sleep, *VISION_NET, "--settle-seconds", "10")
    assert pauses == [SETTLE_PAUSE_SECONDS]


@pytest.mark.usefixtures("the_key")
def test_a_listing_that_never_catches_up_is_exit_one(
        stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["stale_reads"] = 99
    assert _run(stub_api, sleep, *VISION_NET, *AT_ONCE) == 1
