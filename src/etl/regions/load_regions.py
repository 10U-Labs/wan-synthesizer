from __future__ import annotations

import argparse
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from loader import (
    GONE, Api, Loaded, Program, Sleep, changed_paths, place_body, removed, rows, run,
)

REGIONS = "hyperscale-cloud-service-provider-regions"
PROVIDERS = Path("data") / "providers" / "providers.csv"

Listing = list[dict[str, Any]]


def regions_of(repository: Path) -> list[dict[str, Any]]:
    return [place_body(row) for row in rows(repository / PROVIDERS)]


def changed(repository: Path, since: str) -> bool:
    paths = changed_paths(repository, since, [str(PROVIDERS)])
    return paths is None or paths != []


def _delete(api: Api, region_id: int) -> None:
    if removed(api, f"{REGIONS}/{region_id}") == GONE:
        print(f"region {region_id} was already gone", flush=True)
    else:
        print(f"deleted region {region_id}", flush=True)


def _ids(listing: Listing) -> list[int]:
    return sorted(int(region["id"]) for region in listing)


def _load(args: argparse.Namespace, api: Api) -> Loaded | None:
    if not changed(args.repository, args.since):
        print(f"{PROVIDERS.as_posix()} is unchanged since {args.since}", flush=True)
        return None
    stale = _ids(api.get(REGIONS))
    created = sorted(int(api.post(REGIONS, body)["id"]) for body in regions_of(args.repository))
    print(f"created {len(created)} regions", flush=True)
    for region_id in stale:
        _delete(api, region_id)
    return Loaded(REGIONS, lambda listing: _ids(listing) == created,
                  f"loaded {len(created)} regions")


PROGRAM = Program(
    "load-regions", f"Make the API's {REGIONS} match {PROVIDERS.as_posix()}.", _load)


def main(argv: Sequence[str], sleep: Sleep = time.sleep) -> int:
    return run(PROGRAM, argv, sleep)
