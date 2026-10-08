from __future__ import annotations

import argparse
import time
from collections.abc import Iterable, Sequence
from functools import partial
from pathlib import Path
from typing import Any

from loader import (
    GONE, Api, Loaded, Program, Sleep, changed_paths, location_body, removed, rows, run,
)

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
    return [location_body(row) for row in rows(path)] if path.exists() else []


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
    if pops:
        api.put(f"{CARRIERS}/{created}/pops", pops)
    print(f"{name}: added {len(pops)} PoPs", flush=True)
    segments = fiber_segments_of(repository, name)
    if segments:
        api.put(f"{CARRIERS}/{created}/fiber-segments", segments)
    print(f"{name}: added {len(segments)} fiber segments", flush=True)
    return created


def _delete(api: Api, name: str, carrier_id: int) -> None:
    if removed(api, f"{CARRIERS}/{carrier_id}") == GONE:
        print(f"{name}: carrier {carrier_id} was already gone", flush=True)
    else:
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


def _load(args: argparse.Namespace, api: Api) -> Loaded:
    listing = api.get(CARRIERS)
    names = set(args.carrier) or changed_carriers(args.repository, args.since)
    expected: dict[str, list[int]] = {}
    for name in sorted(names):
        expected[name] = load_carrier(api, args.repository, name, _ids_named(listing, name))
    return Loaded(CARRIERS, partial(_agrees, expected), f"loaded {len(expected)} carriers")


PROGRAM = Program(
    "load-carriers", "Make the API's carriers match data/pops and data/fiber_segments.",
    _load, ["--carrier"])


def main(argv: Sequence[str], sleep: Sleep = time.sleep) -> int:
    return run(PROGRAM, argv, sleep)
