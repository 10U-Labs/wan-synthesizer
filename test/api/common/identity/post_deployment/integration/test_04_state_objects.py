from __future__ import annotations

from typing import Any

from test_terraform_config import STATE_BUCKET, STATE_KEY_PREFIX, declared_state_keys


def _stored_keys(s3_client: Any) -> set[str]:
    pages = s3_client.get_paginator("list_objects_v2").paginate(
        Bucket=STATE_BUCKET, Prefix=STATE_KEY_PREFIX
    )
    return {
        stored["Key"]
        for page in pages
        for stored in page.get("Contents", [])
        if not stored["Key"].endswith(".tflock")
    }


def test_every_stored_state_object_is_a_stack_that_still_exists(s3_client: Any) -> None:
    assert _stored_keys(s3_client) - set(declared_state_keys().values()) == set()
