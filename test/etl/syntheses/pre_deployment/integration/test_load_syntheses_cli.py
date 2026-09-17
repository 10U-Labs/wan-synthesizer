from __future__ import annotations

import subprocess
import urllib.error
from pathlib import Path
from typing import Any

import pytest

from loader import ATTEMPTS, SETTLE_PAUSE_SECONDS
from repo_utils import REPO_ROOT
from etl.syntheses.load_syntheses import configuration_named, main, read_configuration, sites_of

DAF = ["--configuration", "daf"]
AT_ONCE = ["--settle-seconds", "0"]
SYNTHESES = "/wan-syntheses"
SITES = "Name,Municipality,State,Country,Latitude,Longitude,ExemptFromDistanceConstraint\n"
CONFIGURATION = """---
backbone:
  coverage_target_miles: 100
  forced:
    circuits: []
    wan_pops: []
  number_of_diverse_circuits: 2
  prohibited:
    circuits: []
    wan_pops: []
  promote_high_degree_convergences: false
  wan_pop_count:
    max: 2
    min: 2
homing:
  degree: 2
  forced: []
inputs:
  sites:
    X: data/tenants/x.csv
label: X
settings: {}
"""


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
    _write(tmp_path, "etc/x.yml", CONFIGURATION)
    _write(tmp_path, "data/tenants/x.csv", SITES + "A,Akron,OH,United States,41.08,-81.52,No\n")
    _write(tmp_path, "README.md", "first\n")
    _commit(tmp_path, "first")
    _write(tmp_path, "README.md", "second\n")
    _write(tmp_path, "unrelated", _commit(tmp_path, "second"))
    _write(tmp_path, "data/tenants/x.csv", SITES + "A,Akron,OH,United States,41.08,-81.52,Yes\n")
    _commit(tmp_path, "third")
    return tmp_path


def _posted(stub_api: Any) -> dict[str, Any]:
    bodies: dict[int, dict[str, Any]] = stub_api.fake.bodies
    return bodies[max(bodies)]


@pytest.mark.usefixtures("the_key")
def test_the_named_configuration_is_created(stub_api: Any, sleep: Any) -> None:
    assert _run(stub_api, sleep, *DAF, *AT_ONCE) == 0


@pytest.mark.usefixtures("the_key")
def test_the_synthesis_created_carries_the_label(stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *DAF, *AT_ONCE)
    assert _posted(stub_api)["label"] == "DAF"


@pytest.mark.usefixtures("the_key")
def test_the_synthesis_created_carries_the_sites_of_the_csv(stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *DAF, *AT_ONCE)
    configuration = read_configuration(configuration_named(REPO_ROOT, "daf"))
    assert _posted(stub_api)["sites"] == sites_of(REPO_ROOT, configuration)


@pytest.mark.usefixtures("the_key")
def test_the_synthesis_created_carries_the_regions_the_api_serves(
        stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *DAF, *AT_ONCE)
    assert _posted(stub_api)["hyperscale_cloud_service_provider_regions"] == [{
        "name": "Provider A", "municipality": "Columbus", "state": "OH",
        "country": "United States", "latitude": 39.9612, "longitude": -82.9988}]


@pytest.mark.usefixtures("the_key")
def test_the_synthesis_created_carries_the_forced_wan_pops(stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *DAF, *AT_ONCE)
    configuration = read_configuration(configuration_named(REPO_ROOT, "daf"))
    assert _posted(stub_api)["forced_wan_pops"] == configuration["backbone"]["forced"]["wan_pops"]


@pytest.mark.usefixtures("the_key")
def test_the_earlier_finished_synthesis_of_the_label_is_deleted(
        stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *DAF, *AT_ONCE)
    assert stub_api.fake.syntheses == {2: "DAF", 3: "Two-PoP", 4: "DAF"}


@pytest.mark.usefixtures("the_key")
def test_the_new_synthesis_is_created_before_the_earlier_one_is_deleted(
        stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *DAF, *AT_ONCE)
    requests = stub_api.requests
    assert requests.index(("POST", SYNTHESES)) < requests.index(("DELETE", f"{SYNTHESES}/1"))


@pytest.mark.usefixtures("the_key")
def test_an_earlier_synthesis_still_running_stays_and_is_no_failure(
        stub_api: Any, sleep: Any) -> None:
    assert (_run(stub_api, sleep, *DAF, *AT_ONCE), 2 in stub_api.fake.syntheses) == (0, True)


@pytest.mark.usefixtures("the_key")
def test_an_earlier_synthesis_already_gone_is_no_failure(stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["stale_reads"] = 1
    del stub_api.fake.syntheses[1]
    assert _run(stub_api, sleep, *DAF, *AT_ONCE) == 0


@pytest.mark.usefixtures("the_key")
def test_every_named_configuration_is_created(stub_api: Any, sleep: Any) -> None:
    _run(stub_api, sleep, *DAF, "--configuration", "two_pop", *AT_ONCE)
    assert sorted(stub_api.fake.syntheses.values()) == ["DAF", "DAF", "Two-PoP"]


@pytest.mark.usefixtures("the_key")
def test_a_configuration_whose_sites_changed_since_the_commit_is_created(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    since = (repository / "unrelated").read_text(encoding="utf-8")
    _run(stub_api, sleep, "--repository", str(repository), "--since", since, *AT_ONCE)
    assert _posted(stub_api)["sites"][0]["exempt_from_distance_constraint"] is True


@pytest.mark.usefixtures("the_key")
def test_nothing_changed_since_the_commit_touches_nothing(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    _run(stub_api, sleep, "--repository", str(repository), "--since", "HEAD", *AT_ONCE)
    assert stub_api.requests == []


@pytest.mark.usefixtures("the_key")
def test_the_null_commit_means_every_configuration(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    _run(stub_api, sleep, "--repository", str(repository), "--since", "0" * 40, *AT_ONCE)
    assert "X" in stub_api.fake.syntheses.values()


@pytest.mark.usefixtures("the_key")
def test_a_throttled_call_is_tried_again_after_a_growing_pause(
        stub_api: Any, sleep: Any, pauses: list[float]) -> None:
    stub_api.fake.faults["refusals"] = 2
    _run(stub_api, sleep, *DAF, *AT_ONCE)
    assert pauses == [1.0, 2.0]


@pytest.mark.usefixtures("the_key")
def test_a_call_throttled_every_time_is_given_up(stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["refusals"] = ATTEMPTS
    with pytest.raises(urllib.error.HTTPError):
        _run(stub_api, sleep, *DAF, *AT_ONCE)


@pytest.mark.usefixtures("the_key")
def test_a_delete_the_api_fails_stops_the_load(stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["failing_deletes"] = 1
    with pytest.raises(urllib.error.HTTPError):
        _run(stub_api, sleep, *DAF, *AT_ONCE)


def test_a_refused_key_stops_the_load(
        stub_api: Any, sleep: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "not-the-key")
    with pytest.raises(urllib.error.HTTPError):
        _run(stub_api, sleep, *DAF, *AT_ONCE)


def test_a_missing_key_is_exit_two(
        stub_api: Any, sleep: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    assert _run(stub_api, sleep, *DAF, *AT_ONCE) == 2


@pytest.mark.usefixtures("the_key")
def test_a_listing_still_catching_up_is_read_again_after_a_pause(
        stub_api: Any, sleep: Any, pauses: list[float]) -> None:
    stub_api.fake.faults["stale_reads"] = 2
    _run(stub_api, sleep, *DAF, "--settle-seconds", "10")
    assert pauses == [SETTLE_PAUSE_SECONDS]


@pytest.mark.usefixtures("the_key")
def test_a_listing_that_never_catches_up_is_exit_one(stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults["stale_reads"] = 99
    assert _run(stub_api, sleep, *DAF, *AT_ONCE) == 1
