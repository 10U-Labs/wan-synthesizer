from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

from repo_utils import REPO_ROOT

DEFAULT_API = "https://api.10ulabs.com/wan-synthesizer"
API_KEY_VARIABLE = "WAN_SYNTHESIZER_API_KEY"
RETRY_PAUSE_SECONDS = 1.0
DATA = REPO_ROOT / "data"
WRITTEN: set[str] = set()


def _rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise ValueError(f"Input file does not exist: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows: list[dict[str, Any]] = []
        for raw in csv.DictReader(handle):
            row: dict[str, Any] = {key.lower(): value.strip() for key, value in raw.items()}
            if "latitude" in row:
                row["latitude"] = float(row["latitude"])
                row["longitude"] = float(row["longitude"])
            rows.append(row)
        return rows


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


def _put(api: str, path: str, body: Any) -> None:
    _send(api, path, "PUT", json.dumps(body).encode())
    WRITTEN.add(f"{path}.json")


def _post_json(api: str, path: str, body: Any) -> Any:
    return json.loads(_send(api, path, "POST", json.dumps(body).encode()))


def push_providers(api: str) -> None:
    regions = _rows(DATA / "providers" / "providers.csv")
    print(f"providers: {len(regions)} regions", flush=True)
    _put(api, "providers/regions", regions)


def prune_store(api: str) -> None:
    print("store: pruning collections nothing writes any more", flush=True)
    answer = _post_json(api, "store/prune", {"written": sorted(WRITTEN)})
    deleted = answer.get("deleted", []) if isinstance(answer, dict) else []
    for key in deleted:
        print(f"  deleted {key}", flush=True)


def main() -> None:
    api = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_API
    push_providers(api)
    prune_store(api)
