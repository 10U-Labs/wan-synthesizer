from __future__ import annotations

import sys
import time
import urllib.error
from collections.abc import Sequence
from functools import partial
from pathlib import Path
from typing import Any

from loader import (
    NO_KEY, Api, Sleep, changed_paths, place_body, rows, settled, started,
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
    try:
        api.delete(f"{REGIONS}/{region_id}")
    except urllib.error.HTTPError as refusal:
        if refusal.code != 404:
            raise
        print(f"region {region_id} was already gone", flush=True)
        return
    print(f"deleted region {region_id}", flush=True)


def _ids(listing: Listing) -> list[int]:
    return sorted(int(region["id"]) for region in listing)


def main(argv: Sequence[str], sleep: Sleep = time.sleep) -> int:
    args, api = started(
        argv, sleep, "load-regions", f"Make the API's {REGIONS} match {PROVIDERS.as_posix()}.")
    if api is None:
        return NO_KEY
    if not changed(args.repository, args.since):
        print(f"{PROVIDERS.as_posix()} is unchanged since {args.since}", flush=True)
        return 0
    stale = _ids(api.get(REGIONS))
    created = sorted(int(api.post(REGIONS, body)["id"]) for body in regions_of(args.repository))
    print(f"created {len(created)} regions", flush=True)
    for region_id in stale:
        _delete(api, region_id)
    listed = partial(api.get, REGIONS)
    if not settled(listed, lambda listing: _ids(listing) == created, args.settle_seconds, sleep):
        print("the listing has not caught up", file=sys.stderr, flush=True)
        return 1
    print(f"loaded {len(created)} regions", flush=True)
    return 0
