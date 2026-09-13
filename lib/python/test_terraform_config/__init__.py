from __future__ import annotations

import re
from pathlib import Path
from typing import cast

from hcl2.api import load as hcl2_load

from repo_utils import REPO_ROOT

COMMON_OUTPUTS_FILE: Path = REPO_ROOT / "lib" / "opentofu" / "common" / "outputs.tf"
STORAGE_MAIN_FILE: Path = REPO_ROOT / "src" / "api" / "common" / "storage" / "main.tf"
ROUTING_AUTHORIZER_FILE: Path = (
    REPO_ROOT / "src" / "api" / "common" / "routing" / "authorizer.tf"
)
STACKS_DIR: Path = REPO_ROOT / "src" / "api"
STATE_KEY_PREFIX = "wan-synthesizer/"
STATE_KEY_LINE = re.compile(r'^\s*key\s*=\s*"([^"]+)"', re.M)


def load_tf(path: Path) -> dict[str, object]:
    with open(path, encoding="utf-8") as handle:
        return cast("dict[str, object]", hcl2_load(handle))


def find_resource(
    tf_config: dict[str, object],
    resource_type: str,
    resource_name: str,
) -> dict[str, object] | None:
    resources = tf_config.get("resource", [])
    if not isinstance(resources, list):
        return None
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        by_name = resource.get(resource_type)
        if isinstance(by_name, dict) and resource_name in by_name:
            body = by_name[resource_name]
            if isinstance(body, dict):
                return cast("dict[str, object]", body)
    return None


def output_values(path: Path) -> dict[str, object]:
    document = load_tf(path)
    blocks = document.get("output", [])
    values: dict[str, object] = {}
    if not isinstance(blocks, list):
        return values
    for block in blocks:
        if not isinstance(block, dict):
            continue
        for name, body in block.items():
            if isinstance(body, dict) and "value" in body:
                values[name] = body["value"]
    return values


def common_outputs() -> dict[str, object]:
    return output_values(COMMON_OUTPUTS_FILE)


def lambda_handler_names() -> dict[str, str]:
    raw = common_outputs().get("lambda_handler_names", {})
    if not isinstance(raw, dict):
        return {}
    return {str(key): str(value) for key, value in raw.items()}


def store_bucket_name() -> str:
    bucket = find_resource(load_tf(STORAGE_MAIN_FILE), "aws_s3_bucket", "store")
    if bucket is None:
        raise AssertionError("aws_s3_bucket.store is not declared in the storage stack")
    return str(bucket["bucket"])


def api_key_parameter_name() -> str:
    parameter = find_resource(load_tf(ROUTING_AUTHORIZER_FILE), "aws_ssm_parameter", "api_key")
    if parameter is None:
        raise AssertionError("aws_ssm_parameter.api_key is not declared in the routing stack")
    return str(parameter["name"])


def declared_state_keys(stacks: Path = STACKS_DIR) -> dict[str, str]:
    keys = {}
    for backend in sorted(stacks.rglob("backend.tf")):
        match = STATE_KEY_LINE.search(backend.read_text(encoding="utf-8"))
        if match is not None:
            keys[str(backend.parent.relative_to(stacks))] = match.group(1)
    return keys


def _string_output(name: str, fallback: str) -> str:
    value = common_outputs().get(name, fallback)
    return value if isinstance(value, str) else fallback


TEST_AWS_REGION: str = _string_output("aws_region", "us-east-2")
STATE_BUCKET: str = _string_output("state_bucket", "10ulabs-terraform-state-us-east-2")
