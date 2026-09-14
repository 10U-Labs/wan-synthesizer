import json
import os
from typing import Any

import boto3

_CLIENTS: dict[str, Any] = {}
_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://www.10ulabs.com",
}
_MERGE_KEYS = {
    "fiber-segments": "carriers/merge/fiber-segments.json",
}


def _s3() -> Any:
    if "s3" not in _CLIENTS:
        _CLIENTS["s3"] = boto3.client("s3", region_name="us-east-2")
    return _CLIENTS["s3"]


def clear_clients() -> None:
    _CLIENTS.clear()


def _response(status: int, body: Any) -> dict[str, Any]:
    return {"statusCode": status, "headers": dict(_HEADERS), "body": json.dumps(body)}


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    client = _s3()
    collection = event.get("path", "").rsplit("/", 1)[-1]
    if collection not in _MERGE_KEYS:
        return _response(404, {"error": collection})
    try:
        body = client.get_object(Bucket=os.environ["STORE_BUCKET"], Key=_MERGE_KEYS[collection])
    except client.exceptions.NoSuchKey:
        return _response(404, {"error": "not built: merged carriers"})
    return _response(200, json.loads(body["Body"].read()))
