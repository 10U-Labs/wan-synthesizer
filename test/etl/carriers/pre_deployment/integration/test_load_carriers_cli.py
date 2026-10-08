from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from loader import NO_COMMIT
from repo_utils import REPO_ROOT
from stub_api import run_against
from throwaway_repository import commit, git, write
from etl.carriers.load_carriers import changed_carriers, fiber_segments_of, main, pops_of

VISION_NET = ["--carrier", "vision_net"]
AT_ONCE = ["--settle-seconds", "0"]
AKRON_POP = ("Municipality,State,Country,Latitude,Longitude\n"
             "Akron,OH,United States,41.0814,-81.5190\n")


@pytest.fixture(name="repository")
def repository_fixture(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    write(tmp_path, "data/pops/alpha.csv", AKRON_POP)
    write(tmp_path, "data/fiber_segments/terrestrial/beta.csv",
          "A_Municipality,A_State,Z_Municipality,Z_State\nLeeds,AL,Memphis,TN\n")
    write(tmp_path, "data/providers/providers.csv", "Name\n")
    first = commit(tmp_path, "first")
    write(tmp_path, "data/fiber_segments/submarine/beta.csv",
          "A_Municipality,A_State,Z_Municipality,Z_State\nLondon,,Paris,\n")
    (tmp_path / "data" / "pops" / "alpha.csv").unlink()
    write(tmp_path, "data/providers/providers.csv", "Name\nchanged\n")
    commit(tmp_path, "second")
    (tmp_path / "since").write_text(first, encoding="utf-8")
    return tmp_path


@pytest.mark.usefixtures("the_key")
def test_the_named_carrier_is_loaded(stub_api: Any, sleep: Any) -> None:
    assert run_against(main, stub_api, sleep, *VISION_NET, *AT_ONCE) == 0


@pytest.mark.usefixtures("the_key")
def test_the_stale_copies_are_gone_and_the_new_one_is_listed(
        stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *VISION_NET, *AT_ONCE)
    assert stub_api.fake.carriers == {6: "dcn", 7: "vision_net"}


@pytest.mark.usefixtures("the_key")
def test_the_pops_loaded_are_the_csv(stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *VISION_NET, *AT_ONCE)
    assert stub_api.fake.members["pops"][7] == pops_of(REPO_ROOT, "vision_net")


@pytest.mark.usefixtures("the_key")
def test_the_fiber_segments_loaded_are_the_csv(stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *VISION_NET, *AT_ONCE)
    assert stub_api.fake.members["fiber-segments"][7] == fiber_segments_of(REPO_ROOT, "vision_net")


@pytest.mark.usefixtures("the_key")
@pytest.mark.parametrize("route", ["/carriers/7/pops", "/carriers/7/fiber-segments"])
def test_a_carriers_list_is_sent_in_one_put(stub_api: Any, sleep: Any, route: str) -> None:
    run_against(main, stub_api, sleep, *VISION_NET, *AT_ONCE)
    assert [request for request in stub_api.requests if request[1] == route] == [("PUT", route)]


@pytest.mark.usefixtures("the_key")
def test_a_carrier_without_fiber_segments_sends_none(
        stub_api: Any, sleep: Any, tmp_path: Path) -> None:
    write(tmp_path, "data/pops/gamma.csv", AKRON_POP)
    run_against(
        main, stub_api, sleep, "--carrier", "gamma", "--repository", str(tmp_path), *AT_ONCE)
    assert [request for request in stub_api.requests if request[0] == "PUT"] == [
        ("PUT", "/carriers/7/pops")]


@pytest.mark.usefixtures("the_key")
def test_the_new_carrier_is_built_before_the_old_ones_are_deleted(
        stub_api: Any, sleep: Any) -> None:
    run_against(main, stub_api, sleep, *VISION_NET, *AT_ONCE)
    requests = stub_api.requests
    assert requests.index(("POST", "/carriers")) < requests.index(("DELETE", "/carriers/3"))


@pytest.mark.usefixtures("the_key")
def test_a_carrier_whose_data_is_gone_is_deleted_and_not_built(
        stub_api: Any, sleep: Any, tmp_path: Path) -> None:
    run_against(main, stub_api, sleep, "--carrier", "dcn", "--repository", str(tmp_path), *AT_ONCE)
    assert stub_api.fake.carriers == {3: "vision_net", 5: "vision_net"}


@pytest.mark.usefixtures("the_key")
def test_every_carrier_is_loaded_when_none_is_named(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    run_against(main, stub_api, sleep, "--repository", str(repository), *AT_ONCE)
    assert sorted(stub_api.fake.carriers.values()) == ["beta", "dcn", "vision_net", "vision_net"]


@pytest.mark.usefixtures("the_key")
def test_only_the_carriers_changed_since_the_commit_are_loaded(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    since = (repository / "since").read_text(encoding="utf-8")
    run_against(main, stub_api, sleep, "--repository", str(repository), "--since", since, *AT_ONCE)
    assert [request for request in stub_api.requests if request[0] in ("POST", "PUT")] == [
        ("POST", "/carriers"), ("PUT", "/carriers/7/fiber-segments")]


@pytest.mark.usefixtures("the_key")
def test_the_null_commit_means_every_carrier(
        stub_api: Any, sleep: Any, repository: Path) -> None:
    run_against(
        main, stub_api, sleep, "--repository", str(repository), "--since", NO_COMMIT, *AT_ONCE)
    assert "beta" in stub_api.fake.carriers.values()


def test_the_carriers_changed_are_read_off_the_diff_deletions_included(repository: Path) -> None:
    since = (repository / "since").read_text(encoding="utf-8")
    assert changed_carriers(repository, since) == {"alpha", "beta"}
