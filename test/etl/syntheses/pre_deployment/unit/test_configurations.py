from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from repo_utils import REPO_ROOT

ETC = REPO_ROOT / "etc"
TENANTS = Path("data") / "tenants"
CONFIGURATIONS = sorted(ETC.glob("*.yml"))
SITES_HEADER = "Name,Municipality,State,Country,Latitude,Longitude,ExemptFromDistanceConstraint"


def _sites_named(configuration: Path) -> list[Path]:
    loaded: dict[str, Any] = yaml.safe_load(configuration.read_text(encoding="utf-8"))
    return [Path(path) for path in loaded["inputs"]["sites"].values()]


def test_there_are_configurations_to_hold() -> None:
    assert [configuration.stem for configuration in CONFIGURATIONS] == [
        "daf", "dow", "f_35", "minuteman", "two_pop"]


@pytest.mark.parametrize("configuration", CONFIGURATIONS, ids=lambda path: str(path.stem))
def test_every_sites_file_a_configuration_names_is_in_the_tree(configuration: Path) -> None:
    assert [path for path in _sites_named(configuration) if not (REPO_ROOT / path).is_file()] == []


@pytest.mark.parametrize("configuration", CONFIGURATIONS, ids=lambda path: str(path.stem))
def test_every_sites_file_a_configuration_names_is_under_data_tenants(
        configuration: Path) -> None:
    assert [path for path in _sites_named(configuration) if path.parent != TENANTS] == []


@pytest.mark.parametrize("configuration", CONFIGURATIONS, ids=lambda path: str(path.stem))
def test_every_sites_file_a_configuration_names_carries_the_sites_header(
        configuration: Path) -> None:
    assert [
        path for path in _sites_named(configuration)
        if (REPO_ROOT / path).read_text(encoding="utf-8").splitlines()[0] != SITES_HEADER
    ] == []


def test_every_tenants_file_is_named_by_a_configuration() -> None:
    named = {path for configuration in CONFIGURATIONS for path in _sites_named(configuration)}
    assert sorted(path.relative_to(REPO_ROOT) for path in (REPO_ROOT / TENANTS).glob("*.csv")) == (
        sorted(named))


@pytest.mark.parametrize("configuration", CONFIGURATIONS, ids=lambda path: str(path.stem))
def test_a_configuration_takes_sites_and_no_other_input(configuration: Path) -> None:
    loaded: dict[str, Any] = yaml.safe_load(configuration.read_text(encoding="utf-8"))
    assert list(loaded["inputs"]) == ["sites"]
