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

import yaml

from repo_utils import REPO_ROOT

DEFAULT_API = "https://api.10ulabs.com/wan-synthesizer"
API_KEY_VARIABLE = "WAN_SYNTHESIZER_API_KEY"
RETRY_PAUSE_SECONDS = 1.0
DATA = REPO_ROOT / "data"
ETC = REPO_ROOT / "etc"
FIBER_SEGMENTS = "fiber_segments"
TERRESTRIAL = "terrestrial"
SUBMARINE = "submarine"
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


def _slug(stem: str) -> str:
    return stem.replace("_", "-")


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


def _post(api: str, path: str) -> None:
    _send(api, path, "POST", b"")


def _post_json(api: str, path: str, body: Any) -> Any:
    return json.loads(_send(api, path, "POST", json.dumps(body).encode()))


def _carrier_names() -> list[str]:
    return sorted({path.stem for path in (DATA / FIBER_SEGMENTS).glob("*/*.csv")})


def _fiber_segment_rows(carrier: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for water, directory in ((False, TERRESTRIAL), (True, SUBMARINE)):
        path = DATA / FIBER_SEGMENTS / directory / f"{carrier}.csv"
        if not path.exists():
            continue
        rows.extend({**row, "submarine": water} for row in _rows(path))
    return rows


def push_carriers(api: str) -> None:
    for carrier in _carrier_names():
        cid = _slug(carrier)
        pops = _rows(DATA / "pops" / f"{carrier}.csv")
        fiber_segments = _fiber_segment_rows(carrier)
        print(f"carrier {cid}: {len(pops)} points, "
              f"{len(fiber_segments)} fiber segments", flush=True)
        _put(api, f"carriers/{cid}/pops", pops)
        _put(api, f"carriers/{cid}/fiber-segments", fiber_segments)


def push_providers(api: str) -> None:
    regions = _rows(DATA / "providers" / "providers.csv")
    print(f"providers: {len(regions)} regions", flush=True)
    _put(api, "providers/regions", regions)


def push_tenants(api: str) -> list[str]:
    tenant_ids: list[str] = []
    for path in sorted(ETC.glob("*.yml")):
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not config:
            continue
        tid = _slug(path.stem)
        tenant_ids.append(tid)
        homing = config["homing"]
        backbone = config["backbone"]
        prohibited = backbone.get("prohibited", {})
        homes = homing.get("forced", [])
        print(f"tenant {tid}", flush=True)
        _put(api, f"tenants/{tid}/forced-homes", homes)
        _put(api, f"tenants/{tid}/prohibited-wan-pops", prohibited.get("wan_pops", []))
        _put(api, f"tenants/{tid}/prohibited-circuits", prohibited.get("circuits", []))
        _put(api, f"tenants/{tid}/degree-exempt-wan-pops",
             backbone.get("degree_exempt", []))
    return tenant_ids


def prune_store(api: str) -> None:
    print("store: pruning collections nothing writes any more", flush=True)
    answer = _post_json(api, "store/prune", {"written": sorted(WRITTEN)})
    deleted = answer.get("deleted", []) if isinstance(answer, dict) else []
    for key in deleted:
        print(f"  deleted {key}", flush=True)


def build_merged_carriers(api: str) -> None:
    print("merge: rebuilding the merged carriers", flush=True)
    _post(api, "carriers/merge")


def main() -> None:
    api = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_API
    push_carriers(api)
    build_merged_carriers(api)
    push_providers(api)
    push_tenants(api)
    prune_store(api)
