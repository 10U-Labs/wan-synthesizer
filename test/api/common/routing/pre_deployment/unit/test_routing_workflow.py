from __future__ import annotations

from typing import Any

import pytest
import yaml

from repo_utils import REPO_ROOT

WORKFLOW = REPO_ROOT / ".github" / "workflows" / "api_common_routing.yml"
PASSED = {"TF_VAR_authorized_accounts": "${{ vars.WAN_SYNTHESIZER_AUTHORIZED_ACCOUNTS }}"}


def _steps(job: str) -> list[dict[str, Any]]:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps: list[dict[str, Any]] = workflow["jobs"][job]["steps"]
    return steps


@pytest.mark.parametrize(("job", "verb"), [
    ("reconciliation", "tofu -chdir=src/api/common/routing apply"),
    ("pre-deployment-integration-tests", "python3 -m pytest"),
])
def test_the_deploy_passes_the_authorized_accounts_wherever_the_stack_is_planned_or_applied(
        job: str, verb: str) -> None:
    assert [
        step.get("env") for step in _steps(job) if verb in str(step.get("run", ""))
    ] == [PASSED]
