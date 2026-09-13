from __future__ import annotations

from typing import Any

import pytest
import yaml

from repo_utils import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "api_common_routing.yml"
PASSED = {
    "TF_VAR_api_key_rotation": "${{ vars.WAN_SYNTHESIZER_API_KEY_ROTATION }}",
    "TF_VAR_authorized_accounts": "${{ vars.WAN_SYNTHESIZER_AUTHORIZED_ACCOUNTS }}",
}


def _workflow() -> dict[str, Any]:
    loaded: dict[str, Any] = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return loaded


def _steps(job: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = _workflow()["jobs"][job]["steps"]
    return steps


@pytest.mark.parametrize(("job", "verb"), [
    ("reconciliation", "tofu -chdir=src/api/common/routing apply"),
    ("pre-deployment-integration-tests", "python3 -m pytest"),
])
def test_the_deploy_passes_both_variables_wherever_the_stack_is_planned_or_applied(
        job: str, verb: str) -> None:
    assert [
        step.get("env") for step in _steps(job) if verb in str(step.get("run", ""))
    ] == [PASSED]


def test_the_workflow_runs_weekly_so_an_overdue_key_is_measured_without_a_push() -> None:
    assert _workflow()[True]["schedule"] == [{"cron": "37 4 * * 1"}]
