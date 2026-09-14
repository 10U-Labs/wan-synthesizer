from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any, cast

import pytest
import yaml

import seed
from repo_utils import REPO_ROOT
from seed import _carrier_names, _rows
from test_http_doubles import UrlopenRecorder
from test_terraform_config import api_key_parameter_name

_API = "http://stub"


def _declared_templates() -> set[str]:
    spec = json.loads(
        (REPO_ROOT / "src/www/api/openapi.json").read_text(encoding="utf-8"))
    prefix = f"{urlsplit(seed.DEFAULT_API).path}/"
    return {path[len(prefix):] for path in spec["paths"] if path.startswith(prefix)}


def _downstream_of(jobs: dict[str, Any], root: str) -> set[str]:
    downstream = {root}
    while True:
        wider = downstream | {
            name for name, job in jobs.items()
            if downstream & set(_needed_by(job))
        }
        if wider == downstream:
            return downstream
        downstream = wider


def _gates_on_seeding() -> set[str]:
    jobs = _seed_workflow()["jobs"]
    return set(jobs) - _downstream_of(jobs, "seeding")


def _linted_configs() -> set[str]:
    workflow = (REPO_ROOT / ".github/workflows/seed.yml").read_text(encoding="utf-8")
    return set(re.findall(r"etc/(\w+\.yml)", workflow))


def _matches(path: str, template: str) -> bool:
    pattern = re.sub(r"\{[^}]+\}", "[^/]+", template)
    return re.fullmatch(pattern, path) is not None


def _seed(recorder: UrlopenRecorder, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    monkeypatch.setattr(sys, "argv", ["seed", _API])
    seed.main()
    return recorder.paths(_API)


def _needed_by(job: dict[str, Any]) -> list[str]:
    needed = job.get("needs", [])
    return [needed] if isinstance(needed, str) else needed


def _seed_workflow() -> dict[str, Any]:
    return cast("dict[str, Any]", yaml.safe_load(
        (REPO_ROOT / ".github/workflows/seed.yml").read_text(encoding="utf-8")))


def test_every_requested_path_is_declared_in_openapi(
        urlopen_recorder: UrlopenRecorder, monkeypatch: pytest.MonkeyPatch) -> None:
    templates = _declared_templates()
    undeclared = [
        path for path in _seed(urlopen_recorder, monkeypatch)
        if not any(_matches(path, template) for template in templates)
    ]
    assert undeclared == []


def test_pipeline_writes_at_least_one_carrier(
        urlopen_recorder: UrlopenRecorder, monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _seed(urlopen_recorder, monkeypatch)
    assert any(re.fullmatch(r"carriers/[^/]+/pops", path) for path in paths)


def _backbone_keys_seed_reads() -> set[str]:
    source = (REPO_ROOT / "scripts" / "seed.py").read_text(encoding="utf-8")
    return set(re.findall(r'backbone(?:\[|\.get\()"([^"]+)"', source))


def test_no_tenant_declares_a_backbone_key_the_seed_does_not_read() -> None:
    declared: set[str] = set()
    for config in sorted((REPO_ROOT / "etc").glob("*.yml")):
        declared |= set(yaml.safe_load(config.read_text(encoding="utf-8"))["backbone"])
    assert declared <= _backbone_keys_seed_reads()


def test_yamllint_names_every_tenant_config() -> None:
    declared = {path.name for path in seed.ETC.glob("*.yml")}
    assert _linted_configs() == declared


def test_seeding_waits_for_every_check_the_workflow_runs() -> None:
    assert set(_needed_by(_seed_workflow()["jobs"]["seeding"])) == _gates_on_seeding()


def test_seeding_demands_a_success_from_every_check_it_waits_for() -> None:
    condition = _seed_workflow()["jobs"]["seeding"]["if"]
    demanded = set(re.findall(r"needs\.([\w-]+)\.result == 'success'", condition))
    assert demanded == _gates_on_seeding()


_WAIT_JOB = "wait-for-every-deploy"


def _workflows_that_deploy() -> set[str]:
    return {
        path.name
        for path in (REPO_ROOT / ".github/workflows").glob("*.yml")
        if "reconciliation" in yaml.safe_load(path.read_text(encoding="utf-8"))["jobs"]
    }


def _workflows_seeding_waits_for() -> set[str]:
    steps = _seed_workflow()["jobs"][_WAIT_JOB]["steps"]
    waited = next(step["env"]["WORKFLOWS"] for step in steps if "env" in step)
    return set(str(waited).split())


def test_seeding_waits_for_every_workflow_that_deploys_on_the_same_commit() -> None:
    assert _workflows_seeding_waits_for() == _workflows_that_deploy()


_JOBS_REACHING_THE_API = ("seeding",)


def _runs(job: dict[str, Any]) -> str:
    return "\n".join(str(step.get("run", "")) for step in job["steps"])


def test_every_job_that_reaches_the_api_reads_the_key_the_authorizer_holds() -> None:
    jobs = _seed_workflow()["jobs"]
    parameter = api_key_parameter_name()
    unkeyed = [
        name for name in _JOBS_REACHING_THE_API
        if seed.API_KEY_VARIABLE not in _runs(jobs[name]) or parameter not in _runs(jobs[name])
    ]
    assert unkeyed == []


def test_every_job_that_reaches_the_api_may_read_the_key() -> None:
    jobs = _seed_workflow()["jobs"]
    assert [
        name for name in _JOBS_REACHING_THE_API
        if jobs[name].get("permissions", {}).get("id-token") != "write"
    ] == []


def test_seeding_seeds_only_on_the_conclusion_the_wait_job_reports() -> None:
    condition = _seed_workflow()["jobs"]["seeding"]["if"]
    assert f"needs.{_WAIT_JOB}.outputs.apply == 'true'" in condition


def test_every_carrier_has_both_a_points_file_and_a_fiber_file() -> None:
    points = sorted(p.stem for p in (seed.DATA / "pops").glob("*.csv"))
    assert points == _carrier_names()


def _fiber_file(directory: str) -> Path:
    return seed.DATA / seed.FIBER_SEGMENTS / directory / "zayo.csv"


def _carrier_fiber_written(
    recorder: UrlopenRecorder, carrier: str
) -> list[dict[str, Any]]:
    return next(
        cast("list[dict[str, Any]]", json.loads(cast("bytes", request.data)))
        for request in recorder.requests
        if request.full_url.endswith(f"/carriers/{carrier}/fiber-segments")
    )


def test_push_carriers_marks_each_fiber_row_by_the_directory_it_came_out_of(
        urlopen_recorder: UrlopenRecorder, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed(urlopen_recorder, monkeypatch)
    written = _carrier_fiber_written(urlopen_recorder, "zayo")
    assert {
        water: sum(1 for row in written if row["submarine"] is water)
        for water in (False, True)
    } == {
        False: len(_rows(_fiber_file(seed.TERRESTRIAL))),
        True: len(_rows(_fiber_file(seed.SUBMARINE))),
    }


def _tenants_written(paths: list[str], resource: str) -> int:
    return sum(1 for path in paths if re.fullmatch(rf"tenants/[^/]+/{resource}", path))


@pytest.mark.parametrize("resource", ["degree-exempt-wan-pops", "prohibited-circuits", "prohibited-wan-pops"])
def test_pipeline_writes_a_document_for_every_tenant(
        resource: str, urlopen_recorder: UrlopenRecorder,
        monkeypatch: pytest.MonkeyPatch) -> None:
    paths = _seed(urlopen_recorder, monkeypatch)
    assert _tenants_written(paths, resource) == len(list(seed.ETC.glob("*.yml")))
