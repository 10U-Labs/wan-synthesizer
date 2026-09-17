from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

from repo_utils import REPO_ROOT

DEFAULT_API = "https://api.10ulabs.com"
API_KEY_VARIABLE = "API_KEY"
CARRIERS = "carriers"
POPS = Path("data") / "pops"
FIBER_SEGMENTS = Path("data") / "fiber_segments"
SUBMARINE = "submarine"
KINDS = ("terrestrial", SUBMARINE)
RETRIED = frozenset({429, 502, 503, 504})
ATTEMPTS = 5
RETRY_PAUSE_SECONDS = 1.0
SETTLE_PAUSE_SECONDS = 5.0
DEFAULT_SETTLE_SECONDS = 300.0
NO_COMMIT = "0" * 40

Sleep = Callable[[float], None]
Listing = list[dict[str, Any]]


class Api:
    def __init__(self, base: str, key: str, sleep: Sleep) -> None:
        self._base = base.rstrip("/")
        self._headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        self._sleep = sleep

    def _once(self, method: str, path: str, body: bytes | None) -> Any:
        request = urllib.request.Request(
            f"{self._base}/{path}", data=body, method=method, headers=self._headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            answer = response.read()
        return json.loads(answer) if answer else None

    def _call(self, method: str, path: str, body: Any = None) -> Any:
        encoded = None if body is None else json.dumps(body).encode()
        for attempt in range(ATTEMPTS - 1):
            try:
                return self._once(method, path, encoded)
            except urllib.error.HTTPError as refusal:
                if refusal.code not in RETRIED:
                    raise
                print(f"  {method} /{path} -> {refusal.code}, trying again", flush=True)
                self._sleep(RETRY_PAUSE_SECONDS * 2 ** attempt)
        return self._once(method, path, encoded)

    def get(self, path: str) -> Any:
        return self._call("GET", path)

    def post(self, path: str, body: Any) -> Any:
        return self._call("POST", path, body)

    def delete(self, path: str) -> None:
        self._call("DELETE", path)


def carriers_in(paths: Iterable[str]) -> set[str]:
    listed = [Path(path) for path in paths]
    return {
        path.stem for path in listed
        if path.suffix == ".csv" and path.parts[:2] in (POPS.parts, FIBER_SEGMENTS.parts)
    }


def every_carrier(repository: Path) -> set[str]:
    found = [*(repository / POPS).glob("*.csv"), *(repository / FIBER_SEGMENTS).glob("*/*.csv")]
    return carriers_in(str(path.relative_to(repository)) for path in found)


def changed_carriers(repository: Path, since: str) -> set[str]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", since, "HEAD", "--",
         str(POPS), str(FIBER_SEGMENTS)],
        cwd=repository, capture_output=True, text=True, check=True)
    return carriers_in(completed.stdout.split())


def _rows(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def pop_body(row: dict[str, str]) -> dict[str, Any]:
    return {
        "municipality": row["Municipality"],
        "state": row["State"],
        "country": row["Country"],
        "latitude": float(row["Latitude"]),
        "longitude": float(row["Longitude"]),
    }


def fiber_segment_body(row: dict[str, str], submarine: bool) -> dict[str, Any]:
    return {
        "a_municipality": row["A_Municipality"],
        "a_state": row["A_State"],
        "z_municipality": row["Z_Municipality"],
        "z_state": row["Z_State"],
        SUBMARINE: submarine,
    }


def carrier_files(repository: Path, name: str) -> list[Path]:
    candidates = [repository / POPS / f"{name}.csv"]
    candidates += [repository / FIBER_SEGMENTS / kind / f"{name}.csv" for kind in KINDS]
    return [path for path in candidates if path.exists()]


def pops_of(repository: Path, name: str) -> list[dict[str, Any]]:
    path = repository / POPS / f"{name}.csv"
    return [pop_body(row) for row in _rows(path)] if path.exists() else []


def fiber_segments_of(repository: Path, name: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for kind in KINDS:
        path = repository / FIBER_SEGMENTS / kind / f"{name}.csv"
        if path.exists():
            segments.extend(fiber_segment_body(row, kind == SUBMARINE) for row in _rows(path))
    return segments


def _create(api: Api, repository: Path, name: str) -> int:
    created = int(api.post(CARRIERS, {"name": name})["id"])
    print(f"{name}: created carrier {created}", flush=True)
    pops = pops_of(repository, name)
    for pop in pops:
        api.post(f"{CARRIERS}/{created}/pops", pop)
    print(f"{name}: added {len(pops)} PoPs", flush=True)
    segments = fiber_segments_of(repository, name)
    for segment in segments:
        api.post(f"{CARRIERS}/{created}/fiber-segments", segment)
    print(f"{name}: added {len(segments)} fiber segments", flush=True)
    return created


def _delete(api: Api, name: str, carrier_id: int) -> None:
    try:
        api.delete(f"{CARRIERS}/{carrier_id}")
    except urllib.error.HTTPError as refusal:
        if refusal.code != 404:
            raise
        print(f"{name}: carrier {carrier_id} was already gone", flush=True)
        return
    print(f"{name}: deleted carrier {carrier_id}", flush=True)


def load_carrier(api: Api, repository: Path, name: str, stale: Sequence[int]) -> list[int]:
    created = [_create(api, repository, name)] if carrier_files(repository, name) else []
    for carrier_id in stale:
        _delete(api, name, carrier_id)
    return created


def _ids_named(listing: Listing, name: str) -> list[int]:
    return sorted(int(carrier["id"]) for carrier in listing if carrier["name"] == name)


def settled(api: Api, expected: dict[str, list[int]], settle_seconds: float, sleep: Sleep) -> bool:
    for _ in range(int(settle_seconds // SETTLE_PAUSE_SECONDS) + 1):
        listing = api.get(CARRIERS)
        if all(_ids_named(listing, name) == ids for name, ids in expected.items()):
            return True
        print("the listing has not caught up yet", flush=True)
        sleep(SETTLE_PAUSE_SECONDS)
    return False


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="load-carriers",
        description="Make the API's carriers match data/pops and data/fiber_segments.")
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--repository", type=Path, default=REPO_ROOT)
    parser.add_argument("--since", default="")
    parser.add_argument("--carrier", action="append", default=[])
    parser.add_argument("--settle-seconds", type=float, default=DEFAULT_SETTLE_SECONDS)
    return parser.parse_args(argv)


def _named(args: argparse.Namespace) -> set[str]:
    if args.carrier:
        return set(args.carrier)
    if args.since and args.since != NO_COMMIT:
        return changed_carriers(args.repository, args.since)
    return every_carrier(args.repository)


def main(argv: Sequence[str], sleep: Sleep = time.sleep) -> int:
    args = _parse(argv)
    key = os.environ.get(API_KEY_VARIABLE, "")
    if not key:
        print(f"{API_KEY_VARIABLE} is not set", file=sys.stderr, flush=True)
        return 2
    api = Api(args.api, key, sleep)
    listing = api.get(CARRIERS)
    expected: dict[str, list[int]] = {}
    for name in sorted(_named(args)):
        expected[name] = load_carrier(api, args.repository, name, _ids_named(listing, name))
    if not settled(api, expected, args.settle_seconds, sleep):
        print("the listing has not caught up", file=sys.stderr, flush=True)
        return 1
    print(f"loaded {len(expected)} carriers", flush=True)
    return 0
