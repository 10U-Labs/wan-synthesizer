from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Iterable, Sequence
from functools import partial
from pathlib import Path
from typing import Any

import yaml

from loader import (
    GONE, Api, Loaded, Program, Sleep, changed_paths, place_body, removed, rows, run,
)

SYNTHESES = "wan-syntheses"
REGIONS = "hyperscale-cloud-service-provider-regions"
REGIONS_INPUT = "hyperscale_cloud_service_provider_regions"
ETC = Path("etc")
TENANTS = Path("data") / "tenants"
STILL_RUNNING = 409
STILL_RUNNING_SECONDS = 1200.0
STILL_RUNNING_PAUSE_SECONDS = 30.0
STILL_RUNNING_EXIT = 3
YES = "yes"

Configuration = dict[str, Any]
Listing = list[dict[str, Any]]


class StillRunning(Exception):
    pass


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
        **place_body(row),
        "exempt_from_distance_constraint": (
            row["ExemptFromDistanceConstraint"].strip().lower() == YES),
    }


def sites_of(repository: Path, configuration: Configuration) -> list[dict[str, Any]]:
    paths = sites_paths(configuration)
    return [site_body(row) for path in paths for row in rows(repository / path)]


def region_given(region: dict[str, Any]) -> dict[str, Any]:
    return {field: value for field, value in region.items() if field != "id"}


def takes_regions(configuration: Configuration) -> bool:
    return bool(configuration["inputs"].get(REGIONS_INPUT, True))


def regions_given(configuration: Configuration, regions: Listing) -> Listing:
    return [region_given(one) for one in regions] if takes_regions(configuration) else []


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
        REGIONS_INPUT: regions_given(configuration, regions),
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


def _newest(listing: Listing, created: dict[str, int]) -> dict[str, int]:
    listed = {str(one["label"]): max(_ids_labelled(listing, one["label"])) for one in listing}
    return {**listed, **created}


def stale(listing: Listing, created: dict[str, int]) -> list[int]:
    newest = _newest(listing, created)
    return sorted(int(one["id"]) for one in listing if int(one["id"]) != newest[one["label"]])


def _delete(api: Api, synthesis_id: int, sleep: Sleep) -> None:
    for _ in range(int(STILL_RUNNING_SECONDS // STILL_RUNNING_PAUSE_SECONDS) + 1):
        code = removed(api, f"{SYNTHESES}/{synthesis_id}", (GONE, STILL_RUNNING))
        if code != STILL_RUNNING:
            gone = f"synthesis {synthesis_id} was already gone"
            print(gone if code == GONE else f"deleted synthesis {synthesis_id}", flush=True)
            return
        print(f"synthesis {synthesis_id} is still running; waiting to delete it", flush=True)
        sleep(STILL_RUNNING_PAUSE_SECONDS)
    raise StillRunning(
        f"synthesis {synthesis_id} was still running after {STILL_RUNNING_SECONDS:.0f} seconds")


def _create(api: Api, repository: Path, path: Path, regions: Listing) -> tuple[str, int]:
    configuration = read_configuration(path)
    sites = sites_of(repository, configuration)
    created = api.post(SYNTHESES, body(configuration, sites, regions))
    label, synthesis_id = str(created["label"]), int(created["id"])
    print(f"{path.name}: created synthesis {synthesis_id} of {label} over {len(sites)} sites",
          flush=True)
    return label, synthesis_id


def _agrees(expected: dict[str, int], listing: Listing) -> bool:
    return all(_ids_labelled(listing, label) == [one] for label, one in expected.items())


def _named(args: argparse.Namespace) -> list[Path]:
    if args.configuration:
        return [configuration_named(args.repository, name) for name in args.configuration]
    return changed_configurations(args.repository, args.since)


def _created(args: argparse.Namespace, api: Api, paths: list[Path]) -> dict[str, int]:
    if not paths:
        print(f"no configuration changed since {args.since}", flush=True)
        return {}
    regions = api.get(REGIONS)
    return dict(_create(api, args.repository, path, regions) for path in paths)


def _load(args: argparse.Namespace, api: Api, sleep: Sleep) -> Loaded:
    listing = api.get(SYNTHESES)
    created = _created(args, api, _named(args))
    swept = stale(listing, created)
    for synthesis_id in swept:
        _delete(api, synthesis_id, sleep)
    return Loaded(
        SYNTHESES, partial(_agrees, _newest(listing, created)),
        f"created {len(created)} syntheses and deleted {len(swept)}")


def _program(sleep: Sleep) -> Program:
    return Program(
        "load-syntheses", "Create a wan synthesis for every run whose configuration changed.",
        partial(_load, sleep=sleep), ["--configuration"])


def main(argv: Sequence[str], sleep: Sleep = time.sleep) -> int:
    try:
        return run(_program(sleep), argv, sleep)
    except StillRunning as running:
        print(running, file=sys.stderr, flush=True)
        return STILL_RUNNING_EXIT
