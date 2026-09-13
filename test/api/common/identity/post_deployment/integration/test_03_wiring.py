from __future__ import annotations

from fnmatch import fnmatch
from typing import Any

import pytest

from test_terraform_config import (
    STATE_BUCKET,
    api_key_parameter_name,
    lambda_handler_names,
    store_bucket_name,
)


def test_the_state_bucket_the_role_may_read_is_the_declared_one(
        live_resources: set[str]) -> None:
    assert f"arn:aws:s3:::{STATE_BUCKET}" in live_resources


def test_the_role_may_write_only_this_repository_s_state(live_resources: set[str]) -> None:
    objects = {r for r in live_resources if r.startswith(f"arn:aws:s3:::{STATE_BUCKET}/")}
    assert objects == {f"arn:aws:s3:::{STATE_BUCKET}/wan-synthesizer/*"}


def test_the_store_the_role_may_configure_is_the_declared_one(
        live_resources: set[str]) -> None:
    assert f"arn:aws:s3:::{store_bucket_name()}" in live_resources


def test_the_role_may_touch_no_object_in_the_store(live_resources: set[str]) -> None:
    assert [r for r in live_resources if r.startswith(f"arn:aws:s3:::{store_bucket_name()}/")] == []


def test_the_api_key_is_within_reach(
        live_resources: set[str], config: dict[str, object]) -> None:
    parameter = (
        f"arn:aws:ssm:{config['aws_region']}:{config['aws_account_id']}"
        f":parameter{api_key_parameter_name()}"
    )
    assert any(fnmatch(parameter, pattern) for pattern in live_resources)


def test_no_parameter_outside_the_product_prefix_is_within_reach(
        live_resources: set[str]) -> None:
    assert [
        pattern for pattern in live_resources
        if ":parameter/" in pattern and ":parameter/wan-synthesizer/" not in pattern
    ] == []


@pytest.mark.parametrize("handler", sorted(lambda_handler_names()))
def test_each_handler_function_is_within_reach(
        live_resources: set[str], config: dict[str, object], handler: str) -> None:
    function = (
        f"arn:aws:lambda:{config['aws_region']}:{config['aws_account_id']}"
        f":function:{lambda_handler_names()[handler]}"
    )
    assert any(fnmatch(function, pattern) for pattern in live_resources)


def test_the_distribution_the_role_may_invalidate_serves_the_site(
        cloudfront_client: Any, live_resources: set[str]) -> None:
    distributions = [r for r in live_resources if ":distribution/" in r]
    served = [
        "10ulabs.com" in cloudfront_client.get_distribution(
            Id=arn.rsplit("/", 1)[-1])["Distribution"]["DistributionConfig"]["Aliases"]["Items"]
        for arn in distributions
    ]
    assert served == [True]


def test_the_site_prefix_the_role_may_write_is_the_product_s(live_resources: set[str]) -> None:
    objects = {r for r in live_resources if r.startswith("arn:aws:s3:::www-10ulabs-com/")}
    assert objects == {"arn:aws:s3:::www-10ulabs-com/wan-synthesizer/*"}


def test_the_role_may_describe_log_groups(
        live_resources: set[str], config: dict[str, object]) -> None:
    region, account = config["aws_region"], config["aws_account_id"]
    assert f"arn:aws:logs:{region}:{account}:log-group::log-stream:" in live_resources
