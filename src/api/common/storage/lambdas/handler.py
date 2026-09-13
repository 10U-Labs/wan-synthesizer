import json
import os
from typing import Any

import boto3

_CLIENTS: dict[str, Any] = {}
_HEADERS = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "https://www.10ulabs.com"}

CARRIER_FILES = frozenset({"pops.json", "fiber-segments.json"})
PROVIDER_FILES = frozenset({"regions.json"})
TENANT_FILES = frozenset({
    "backbone-number-of-diverse-circuits.json",
    "convergence-promotion.json",
    "degree-exempt-wan-pops.json",
    "forced-circuits.json",
    "forced-homes.json",
    "forced-wan-pops.json",
    "homing-degree.json",
    "knobs.json",
    "label.json",
    "locations.json",
    "off-net.json",
    "prohibited-circuits.json",
    "prohibited-wan-pops.json",
    "provider-regions.json",
    "settings.json",
    "wan-pop-count.json",
    "wan-status.json",
    "wan.json",
})
_KEPT_BY_PREFIX = {
    "carriers": CARRIER_FILES,
    "providers": PROVIDER_FILES,
    "tenants": TENANT_FILES,
}


def _s3() -> Any:
    if "s3" not in _CLIENTS:
        _CLIENTS["s3"] = boto3.client("s3", region_name="us-east-2")
    return _CLIENTS["s3"]


def clear_clients() -> None:
    _CLIENTS.clear()


def _response(status: int, body: Any) -> dict[str, Any]:
    return {"statusCode": status, "headers": dict(_HEADERS), "body": json.dumps(body)}


def is_current(key: str, written: frozenset[str] = frozenset()) -> bool:
    if key in written:
        return True
    prefix, _, rest = key.partition("/")
    kept = _KEPT_BY_PREFIX.get(prefix)
    if kept is None or not rest:
        return False
    return rest.rsplit("/", 1)[-1] in kept


def _stale_versions(
    client: Any, bucket: str, written: frozenset[str] = frozenset()
) -> list[tuple[str, str]]:
    stale: list[tuple[str, str]] = []
    for page in client.get_paginator("list_object_versions").paginate(Bucket=bucket):
        stale += [
            (version["Key"], version["VersionId"])
            for version in page.get("Versions", [])
            if not is_current(version["Key"], written)
        ]
        stale += [(marker["Key"], marker["VersionId"]) for marker in page.get("DeleteMarkers", [])]
    return sorted(stale)


def _written(event: dict[str, Any]) -> frozenset[str]:
    body = json.loads(event.get("body") or "{}")
    return frozenset(body.get("written", []))


def _prune(client: Any, written: frozenset[str]) -> dict[str, Any]:
    bucket = os.environ["STORE_BUCKET"]
    stale = _stale_versions(client, bucket, written)
    for key, version in stale:
        client.delete_object(Bucket=bucket, Key=key, VersionId=version)
    return {"deleted": [key for key, _version in stale]}


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    client = _s3()
    if event.get("httpMethod") == "POST":
        return _response(200, _prune(client, _written(event)))
    stale = _stale_versions(client, os.environ["STORE_BUCKET"])
    return _response(200, {"stale": [key for key, _version in stale]})
