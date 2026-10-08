from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loader import NO_COMMIT
from repo_utils import REPO_ROOT
from stub_api import STALE_READS, run_against
from throwaway_repository import commit, git, write
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


@pytest.fixture(name="repository")
def repository_fixture(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    write(tmp_path, "etc/x.yml", CONFIGURATION)
    write(tmp_path, "data/tenants/x.csv", SITES + "A,Akron,OH,United States,41.08,-81.52,No\n")
    write(tmp_path, "README.md", "first\n")
    commit(tmp_path, "first")
    write(tmp_path, "README.md", "second\n")
    write(tmp_path, "unrelated", commit(tmp_path, "second"))
    write(tmp_path, "data/tenants/x.csv", SITES + "A,Akron,OH,United States,41.08,-81.52,Yes\n")
    commit(tmp_path, "third")
    return tmp_path


def _posted(stub_api: Any) -> dict[str, Any]:
    bodies: dict[int, dict[str, Any]] = stub_api.fake.bodies
    return bodies[max(bodies)]


@pytest.mark.usefixtures("the_key")
def test_the_named_configuration_is_created(stub_api: Any, sleep: Any) -> None:
    assert run_against(main, stub_api, sleep, *DAF, *AT_ONCE) == 0


@pytest.mark.usefixtures("the_key")
def test_the_synthesis_created_carries_the_label(stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *DAF, *AT_ONCE)
    assert _posted(stub_api)["label"] == "DAF"


@pytest.mark.usefixtures("the_key")
def test_the_synthesis_created_carries_the_sites_of_the_csv(stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *DAF, *AT_ONCE)
    configuration = read_configuration(configuration_named(REPO_ROOT, "daf"))
    assert _posted(stub_api)["sites"] == sites_of(REPO_ROOT, configuration)


@pytest.mark.usefixtures("the_key")
def test_the_synthesis_created_carries_the_regions_the_api_serves(
        stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *DAF, *AT_ONCE)
    assert _posted(stub_api)["hyperscale_cloud_service_provider_regions"] == [{
        "name": "Provider A", "municipality": "Columbus", "state": "OH",
        "country": "United States", "latitude": 39.9612, "longitude": -82.9988}]


@pytest.mark.usefixtures("the_key")
def test_the_synthesis_created_carries_the_forced_wan_pops(stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *DAF, *AT_ONCE)
    configuration = read_configuration(configuration_named(REPO_ROOT, "daf"))
    assert _posted(stub_api)["forced_wan_pops"] == configuration["backbone"]["forced"]["wan_pops"]


@pytest.mark.usefixtures("the_key")
def test_the_earlier_finished_synthesis_of_the_label_is_deleted(
        stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *DAF, *AT_ONCE)
    assert stub_api.fake.syntheses == {2: "DAF", 3: "Two-PoP", 4: "DAF"}


@pytest.mark.usefixtures("the_key")
def test_the_new_synthesis_is_created_before_the_earlier_one_is_deleted(
        stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *DAF, *AT_ONCE)
    requests = stub_api.requests
    assert requests.index(("POST", SYNTHESES)) < requests.index(("DELETE", f"{SYNTHESES}/1"))


@pytest.mark.usefixtures("the_key")
def test_an_earlier_synthesis_still_running_stays_and_is_no_failure(
        stub_api: Any, sleep: Any) -> None:
    ran = run_against(main, stub_api, sleep, *DAF, *AT_ONCE)
    assert (ran, 2 in stub_api.fake.syntheses) == (0, True)


@pytest.mark.usefixtures("the_key")
def test_an_earlier_synthesis_already_gone_is_no_failure(stub_api: Any, sleep: Any) -> None:
    stub_api.fake.faults[STALE_READS] = 1
    del stub_api.fake.syntheses[1]
    assert run_against(main, stub_api, sleep, *DAF, *AT_ONCE) == 0


@pytest.mark.usefixtures("the_key")
def test_every_named_configuration_is_created(stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *DAF, "--configuration", "two_pop", *AT_ONCE)
    assert sorted(stub_api.fake.syntheses.values()) == ["DAF", "DAF", "Two-PoP"]


@pytest.mark.usefixtures("the_key")
def test_a_configuration_whose_sites_changed_since_the_commit_is_created(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    since = (repository / "unrelated").read_text(encoding="utf-8")
    run_against(main, stub_api, sleep, "--repository", str(repository), "--since", since, *AT_ONCE)
    assert _posted(stub_api)["sites"][0]["exempt_from_distance_constraint"] is True


@pytest.mark.usefixtures("the_key")
def test_the_null_commit_means_every_configuration(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    run_against(
        main, stub_api, sleep, "--repository", str(repository), "--since", NO_COMMIT, *AT_ONCE)
    assert "X" in stub_api.fake.syntheses.values()


@pytest.mark.usefixtures("the_key")
def test_a_run_since_head_touches_nothing(stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, "--since", "HEAD", *AT_ONCE)
    assert stub_api.requests == []
