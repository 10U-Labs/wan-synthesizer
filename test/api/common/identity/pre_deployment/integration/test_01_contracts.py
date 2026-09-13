from __future__ import annotations

import os
from typing import Any

from test_terraform_config import output_values


def test_the_outputs_declare_the_role_and_the_subject(identity_dir: Any) -> None:
    outputs = output_values(identity_dir / "outputs.tf")
    assert set(outputs) == {"role_arn", "role_name", "seed_role_arn", "seed_role_name", "subject"}


def test_the_role_arn_output_reads_the_declared_role(identity_dir: Any) -> None:
    assert "aws_iam_role.deploy.arn" in str(output_values(identity_dir / "outputs.tf")["role_arn"])


def test_the_subject_names_the_repository_this_run_is_in(
        declared_subject: str, matched_subject: Any) -> None:
    match = matched_subject(declared_subject)
    assert f"{match.group(1)}/{match.group(2)}" == os.environ["GITHUB_REPOSITORY"]


def test_the_subject_carries_the_id_github_gives_this_repository(declared_subject: str) -> None:
    assert f"@{os.environ['GITHUB_REPOSITORY_ID']}:" in declared_subject


def test_the_subject_carries_the_id_github_gives_this_owner(declared_subject: str) -> None:
    assert f"@{os.environ['GITHUB_REPOSITORY_OWNER_ID']}/" in declared_subject


def test_the_role_the_workflows_assume_is_the_declared_one(
        role_name: str, config: dict[str, object]) -> None:
    expected = f"arn:aws:iam::{config['aws_account_id']}:role/{role_name}"
    assert os.environ["OIDC_ROLE_ARN"] == expected


def test_the_role_the_seed_assumes_is_the_declared_one(
        seed_role_name: str, config: dict[str, object]) -> None:
    expected = f"arn:aws:iam::{config['aws_account_id']}:role/{seed_role_name}"
    assert os.environ["SEED_ROLE_ARN"] == expected
