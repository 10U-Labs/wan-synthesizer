import json
import logging
import os
from typing import Any

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_CLIENTS: dict[str, Any] = {}
_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://www.10ulabs.com",
}

STATUSES_WITH_NO_WAN = frozenset({"fail", "timeout"})


def _s3() -> Any:
    if "s3" not in _CLIENTS:
        _CLIENTS["s3"] = boto3.client("s3", region_name="us-east-2")
    return _CLIENTS["s3"]


def clear_clients() -> None:
    _CLIENTS.clear()


def _response(status: int, body: Any) -> dict[str, Any]:
    return {"statusCode": status, "headers": dict(_HEADERS), "body": json.dumps(body)}


def _status_key(tenant: str) -> str:
    return f"tenants/{tenant}/wan-status.json"


def _read_status(tenant: str) -> dict[str, Any]:
    client = _s3()
    try:
        body = client.get_object(
            Bucket=os.environ["STORE_BUCKET"], Key=_status_key(tenant)
        )["Body"].read()
    except client.exceptions.NoSuchKey:
        return _response(404, {"error": f"no wan: {tenant}"})
    status = json.loads(body)
    code = 422 if status.get("status") in STATUSES_WITH_NO_WAN else 200
    return _response(code, status)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    tenant = (event.get("pathParameters") or {}).get("tenant")
    if not tenant:
        return _response(404, {"error": "tenant required"})
    return _read_status(tenant)
