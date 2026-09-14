from __future__ import annotations

from repo_utils import REPO_ROOT
from test_terraform_config import output_values

STORAGE_DIR = REPO_ROOT / "src" / "api" / "common" / "storage"


def test_outputs_declare_the_bucket_name_and_arn() -> None:
    outputs = output_values(STORAGE_DIR / "outputs.tf")
    assert set(outputs) == {"bucket_name", "bucket_arn"}


def test_bucket_name_output_references_the_declared_store() -> None:
    outputs = output_values(STORAGE_DIR / "outputs.tf")
    assert "aws_s3_bucket.store" in str(outputs["bucket_name"])
