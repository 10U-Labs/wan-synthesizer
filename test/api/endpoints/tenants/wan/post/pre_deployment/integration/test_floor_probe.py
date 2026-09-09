from __future__ import annotations

import random

import fixtures
from synthesizer.input_graph import segment_key

_ASKED_FOR = 2
_GRAPHS = 60
_SEATS = 3


_LEFT = ("l0", "l1", "l2")
_RIGHT = ("r0", "r1", "r2")
_HUB = "h"


def _blob(group: tuple[str, ...], rng: random.Random) -> dict[tuple[str, str], float]:
    ring = list(group) + [_HUB]
    segments = {
        segment_key(ring[index], ring[(index + 1) % len(ring)]): float(
            rng.randrange(10, 400)
        )
        for index in range(len(ring))
    }
    if rng.random() < 0.5:
        segments[segment_key(ring[0], ring[2])] = float(rng.randrange(10, 400))
    return segments


def _random_segments(rng: random.Random) -> dict[tuple[str, str], float]:
    return {**_blob(_LEFT, rng), **_blob(_RIGHT, rng)}


def _measured(seed: int) -> tuple[float, str] | None:
    segments = _random_segments(random.Random(seed))
    try:
        artifacts = fixtures.synthesis_over_chosen_fiber(
            fixtures.fiber_segments_from(segments), _SEATS, _ASKED_FOR
        )
    except ValueError:
        return None
    run = artifacts.synthesis.metrics.physical_miles
    floor = artifacts.synthesis.metrics.backbone_lower_bound_miles
    return (
        floor / run if run else 0.0,
        f"seed={seed} run={run} floor={floor} "
        f"seats={artifacts.synthesis.backbone_ids} "
        f"over={len(artifacts.synthesis.fiber_segment_keys)} "
        f"circuits={len(artifacts.synthesis.drawn_circuits)} "
        f"segments={sorted(segments.items())}",
    )


_MEASURED = [found for found in (_measured(seed) for seed in range(_GRAPHS)) if found]
_REPORT = f"measured {len(_MEASURED)} of {_GRAPHS}, worst {sorted(_MEASURED)[-4:]}"


def test_the_probe_reports_the_graphs_whose_floor_sits_highest() -> None:
    assert not _REPORT, _REPORT
