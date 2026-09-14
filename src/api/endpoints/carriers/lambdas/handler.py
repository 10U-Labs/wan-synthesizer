import json
import os
from typing import Any

import boto3

_CLIENTS: dict[str, Any] = {}
_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://www.10ulabs.com",
}
_ONLY_VERSION = "null"


def _s3() -> Any:
    if "s3" not in _CLIENTS:
        _CLIENTS["s3"] = boto3.client("s3", region_name="us-east-2")
    return _CLIENTS["s3"]


def clear_clients() -> None:
    _CLIENTS.clear()


def _response(status: int, body: Any) -> dict[str, Any]:
    return {"statusCode": status, "headers": dict(_HEADERS), "body": json.dumps(body)}


def _delete(client: Any, carrier: str) -> dict[str, Any]:
    bucket = os.environ["STORE_BUCKET"]
    listing = client.list_objects_v2(Bucket=bucket, Prefix=f"carriers/{carrier}/")
    for item in listing.get("Contents", []):
        client.delete_object(Bucket=bucket, Key=item["Key"], VersionId=_ONLY_VERSION)
    return _response(200, {"deleted": carrier})


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    client = _s3()
    method = event.get("httpMethod", "GET")
    carrier = (event.get("pathParameters") or {}).get("carrier")
    if not carrier:
        return _response(404, {"error": "carrier required"})
    if method == "DELETE":
        return _delete(client, carrier)
    return _response(404, {"error": method})
