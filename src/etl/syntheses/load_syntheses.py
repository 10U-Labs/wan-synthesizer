from __future__ import annotations

import argparse
import sys
import time
import urllib.error
from collections.abc import Iterable, Sequence
from functools import partial
from pathlib import Path
from typing import Any

import yaml

from loader import (
    DEFAULT_API, DEFAULT_SETTLE_SECONDS, Api, Sleep, changed_paths, key, rows, settled,
)
from repo_utils import REPO_ROOT

SYNTHESES = "wan-syntheses"
REGIONS = "hyperscale-cloud-service-provider-regions"
ETC = Path("etc")
TENANTS = Path("data") / "tenants"
STILL_RUNNING = 409
YES = "yes"

Configuration = dict[str, Any]
Listing = list[dict[str, Any]]


def configurations(repository: Path) -> list[Path]:
    return sorted((repository / ETC).glob("*.yml"))


def configuration_named(repository: Path, name: str) -> Path:
    return repository / ETC / f"{name}.yml"


def read_configuration(path: Path) -> Configuration:
    loaded: Configuration = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded


def sites_paths(configuration: Configuration) -> list[Path]:
    return [Path(path) for path in configuration["inputs"]["sites"].values()]


def site_body(row: dict[str, str]) -> dict[str, Any]:
    return {
        "name": row["Name"],
        "municipality": row["Municipality"],
        "state": row["State"],
        "country": row["Country"],
        "latitude": float(row["Latitude"]),
        "longitude": float(row["Longitude"]),
        "exempt_from_distance_constraint": (
            row["ExemptFromDistanceConstraint"].strip().lower() == YES),
    }


def sites_of(repository: Path, configuration: Configuration) -> list[dict[str, Any]]:
    paths = sites_paths(configuration)
    return [site_body(row) for path in paths for row in rows(repository / path)]


def region_given(region: dict[str, Any]) -> dict[str, Any]:
    return {field: value for field, value in region.items() if field != "id"}


def body(configuration: Configuration, sites: Listing, regions: Listing) -> dict[str, Any]:
    backbone, homing = configuration["backbone"], configuration["homing"]
    forced, prohibited = backbone["forced"], backbone["prohibited"]
    return {
        "label": configuration["label"],
        "wan_pop_count": backbone["wan_pop_count"],
        "backbone_number_of_diverse_circuits": backbone["number_of_diverse_circuits"],
        "homing_degree": homing["degree"],
        "convergence_promotion": backbone["promote_high_degree_convergences"],
        "knobs": {"backbone_coverage_target_miles": backbone["coverage_target_miles"]},
        "settings": configuration["settings"],
        "sites": sites,
        "hyperscale_cloud_service_provider_regions": [region_given(one) for one in regions],
        "off_net": [],
        "forced_wan_pops": forced["wan_pops"],
        "forced_circuits": forced["circuits"],
        "forced_homes": homing["forced"],
        "prohibited_wan_pops": prohibited["wan_pops"],
        "prohibited_circuits": prohibited["circuits"],
        "degree_exempt_wan_pops": backbone.get("degree_exempt", []),
    }


def touched(repository: Path, candidates: Iterable[Path], changed: Iterable[str]) -> list[Path]:
    changed_set = set(changed)

    def named(path: Path) -> bool:
        own = [path, *(repository / site for site in sites_paths(read_configuration(path)))]
        return any(str(one.relative_to(repository)) in changed_set for one in own)
    return [path for path in candidates if named(path)]


def changed_configurations(repository: Path, since: str) -> list[Path]:
    changed = changed_paths(repository, since, [str(ETC), str(TENANTS)])
    every = configurations(repository)
    return every if changed is None else touched(repository, every, changed)


def _ids_labelled(listing: Listing, label: str) -> list[int]:
    return sorted(int(one["id"]) for one in listing if one["label"] == label)


def _delete(api: Api, synthesis_id: int) -> bool:
    try:
        api.delete(f"{SYNTHESES}/{synthesis_id}")
    except urllib.error.HTTPError as refusal:
        if refusal.code == STILL_RUNNING:
            print(f"synthesis {synthesis_id} is still running and stays", flush=True)
            return True
        if refusal.code != 404:
            raise
        print(f"synthesis {synthesis_id} was already gone", flush=True)
        return False
    print(f"deleted synthesis {synthesis_id}", flush=True)
    return False


def _create(api: Api, repository: Path, path: Path, regions: Listing) -> tuple[str, int]:
    configuration = read_configuration(path)
    sites = sites_of(repository, configuration)
    created = api.post(SYNTHESES, body(configuration, sites, regions))
    label, synthesis_id = str(created["label"]), int(created["id"])
    print(f"{path.name}: created synthesis {synthesis_id} of {label} over {len(sites)} sites",
          flush=True)
    return label, synthesis_id


def _agrees(expected: dict[str, list[int]], listing: Listing) -> bool:
    return all(_ids_labelled(listing, label) == ids for label, ids in expected.items())


def _parse(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="load-syntheses",
        description="Create a wan synthesis for every run whose configuration changed.")
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--repository", type=Path, default=REPO_ROOT)
    parser.add_argument("--since", default="")
    parser.add_argument("--configuration", action="append", default=[])
    parser.add_argument("--settle-seconds", type=float, default=DEFAULT_SETTLE_SECONDS)
    return parser.parse_args(argv)


def _named(args: argparse.Namespace) -> list[Path]:
    if args.configuration:
        return [configuration_named(args.repository, name) for name in args.configuration]
    return changed_configurations(args.repository, args.since)


def main(argv: Sequence[str], sleep: Sleep = time.sleep) -> int:
    args = _parse(argv)
    bearer = key()
    if not bearer:
        print("the environment carries no key for the API", file=sys.stderr, flush=True)
        return 2
    paths = _named(args)
    if not paths:
        print(f"no configuration changed since {args.since}", flush=True)
        return 0
    api = Api(args.api, bearer, sleep)
    listing = api.get(SYNTHESES)
    regions = api.get(REGIONS)
    expected: dict[str, list[int]] = {}
    for path in paths:
        label, created = _create(api, args.repository, path, regions)
        kept = [one for one in _ids_labelled(listing, label) if _delete(api, one)]
        expected[label] = sorted([*kept, created])
    listed = partial(api.get, SYNTHESES)
    if not settled(listed, partial(_agrees, expected), args.settle_seconds, sleep):
        print("the listing has not caught up", file=sys.stderr, flush=True)
        return 1
    print(f"created {len(expected)} syntheses", flush=True)
    return 0
