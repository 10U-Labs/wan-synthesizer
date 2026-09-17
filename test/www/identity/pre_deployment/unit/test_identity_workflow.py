from __future__ import annotations

from typing import Any

import yaml

from repo_utils import REPO_ROOT

IDENTITY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "www_identity.yml"
POST_DEPLOYMENT = "post-deployment-integration-tests"
RECONCILIATION = "reconciliation"
POST_DEPLOYMENT_TIER = "test/www/identity/post_deployment/integration/"
UNIT_TIER = "test/www/identity/pre_deployment/unit/"


def _workflow() -> dict[str, Any]:
    loaded: dict[Any, Any] = yaml.safe_load(IDENTITY_WORKFLOW.read_text(encoding="utf-8"))
    return loaded


def _runs(job: str) -> list[str]:
    return [str(step.get("run", "")) for step in _workflow()["jobs"][job]["steps"]]


def test_the_key_is_read_only_after_the_role_is_reconciled() -> None:
    assert _workflow()["jobs"][POST_DEPLOYMENT]["needs"] == [RECONCILIATION]


def test_the_post_deployment_job_runs_the_identity_post_deployment_integration_tier() -> None:
    assert [run for run in _runs(POST_DEPLOYMENT) if POST_DEPLOYMENT_TIER in run] != []


def test_the_post_deployment_job_assumes_the_role_every_workflow_assumes() -> None:
    assert [
        step for step in _workflow()["jobs"][POST_DEPLOYMENT]["steps"]
        if step.get("with", {}).get("role-to-assume") == "${{ vars.OIDC_ROLE_ARN }}"
    ] != []


def test_the_role_is_reconciled_only_after_the_declaration_passes_its_unit_tests() -> None:
    assert "unit-tests" in _workflow()["jobs"][RECONCILIATION]["needs"]


def test_the_unit_tests_job_runs_the_identity_pre_deployment_unit_tier() -> None:
    assert [run for run in _runs("unit-tests") if UNIT_TIER in run] != []


def test_a_change_to_the_identity_tests_starts_the_workflow() -> None:
    assert "test/www/identity/**" in _workflow()["on"]["push"]["paths"]
