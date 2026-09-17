from __future__ import annotations

import argparse
import sys
import time
import urllib.error
from collections.abc import Iterable, Sequence
from functools import partial
from pathlib import Path
from typing import Any

from loader import (
    DEFAULT_API, DEFAULT_SETTLE_SECONDS, Api, Sleep, changed_paths, key, rows, settled,
)
from repo_utils import REPO_ROOT

CARRIERS = "carriers"
POPS = Path("data") / "pops"
FIBER_SEGMENTS = Path("data") / "fiber_segments"
SUBMARINE = "submarine"
KINDS = ("terrestrial", SUBMARINE)

Listing = list[dict[str, Any]]


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
    changed = changed_paths(repository, since, [str(POPS), str(FIBER_SEGMENTS)])
    return every_carrier(repository) if changed is None else carriers_in(changed)


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
    return [pop_body(row) for row in rows(path)] if path.exists() else []


def fiber_segments_of(repository: Path, name: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for kind in KINDS:
        path = repository / FIBER_SEGMENTS / kind / f"{name}.csv"
        if path.exists():
            segments.extend(fiber_segment_body(row, kind == SUBMARINE) for row in rows(path))
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


def _agrees(expected: dict[str, list[int]], listing: Listing) -> bool:
    return all(_ids_named(listing, name) == ids for name, ids in expected.items())


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


def main(argv: Sequence[str], sleep: Sleep = time.sleep) -> int:
    args = _parse(argv)
    bearer = key()
    if not bearer:
        print("the environment carries no key for the API", file=sys.stderr, flush=True)
        return 2
    api = Api(args.api, bearer, sleep)
    listing = api.get(CARRIERS)
    names = set(args.carrier) or changed_carriers(args.repository, args.since)
    expected: dict[str, list[int]] = {}
    for name in sorted(names):
        expected[name] = load_carrier(api, args.repository, name, _ids_named(listing, name))
    listed = partial(api.get, CARRIERS)
    if not settled(listed, partial(_agrees, expected), args.settle_seconds, sleep):
        print("the listing has not caught up", file=sys.stderr, flush=True)
        return 1
    print(f"loaded {len(expected)} carriers", flush=True)
    return 0
