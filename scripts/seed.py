from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, cast

DEFAULT_API = "https://api.10ulabs.com/wan-synthesizer"
API_KEY_VARIABLE = "WAN_SYNTHESIZER_API_KEY"
RETRY_PAUSE_SECONDS = 1.0


def _is_dropped_connection(failure: OSError) -> bool:
    if isinstance(failure, urllib.error.HTTPError):
        return False
    if isinstance(failure, urllib.error.URLError):
        return isinstance(failure.reason, ConnectionResetError)
    return isinstance(failure, ConnectionResetError)


def _send_once(request: urllib.request.Request, method: str, path: str) -> bytes:
    with urllib.request.urlopen(request, timeout=60) as response:
        print(f"  {method} /{path} -> {response.status}", flush=True)
        return cast("bytes", response.read())


def _authorization() -> dict[str, str]:
    key = os.environ.get(API_KEY_VARIABLE)
    return {"Authorization": f"Bearer {key}"} if key else {}


def _send(api: str, path: str, method: str, body: bytes | None) -> bytes:
    request = urllib.request.Request(
        f"{api}/{path}",
        data=body,
        method=method,
        headers={"Content-Type": "application/json", **_authorization()},
    )
    try:
        return _send_once(request, method, path)
    except OSError as failure:
        if not _is_dropped_connection(failure):
            raise
    print(f"  {method} /{path} -> connection reset, trying once more", flush=True)
    time.sleep(RETRY_PAUSE_SECONDS)
    return _send_once(request, method, path)


def _post_json(api: str, path: str, body: Any) -> Any:
    return json.loads(_send(api, path, "POST", json.dumps(body).encode()))


def prune_store(api: str) -> None:
    print("store: pruning collections nothing writes any more", flush=True)
    answer = _post_json(api, "store/prune", {"written": []})
    deleted = answer.get("deleted", []) if isinstance(answer, dict) else []
    for key in deleted:
        print(f"  deleted {key}", flush=True)


def main() -> None:
    api = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_API
    prune_store(api)
