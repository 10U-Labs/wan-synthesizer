from __future__ import annotations

from typing import Any

import yaml

from repo_utils import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "www_spa.yml"
E2E = "post-deployment-e2e-tests"


def _job(name: str) -> dict[str, Any]:
    loaded: dict[Any, Any] = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    job: dict[str, Any] = loaded["jobs"][name]
    return job


def test_the_headers_are_read_off_the_site_only_after_the_deploy() -> None:
    assert _job(E2E)["needs"] == ["deploy"]


def test_the_e2e_job_runs_the_spas_post_deployment_e2e_tier() -> None:
    assert [
        step for step in _job(E2E)["steps"]
        if "test/www/spa/post_deployment/e2e/" in str(step.get("run", ""))
    ] != []
