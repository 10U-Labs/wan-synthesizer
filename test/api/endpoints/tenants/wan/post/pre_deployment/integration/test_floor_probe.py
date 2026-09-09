from __future__ import annotations

import random

import fixtures
from synthesizer.input_graph import segment_key

_ASKED_FOR = 2
_CITIES = 7
_GRAPHS = 60
_SEATS = 3


def _degrees(segments: dict[tuple[str, str], float]) -> dict[str, int]:
    degree: dict[str, int] = {}
    for left, right in segments:
        degree[left] = degree.get(left, 0) + 1
        degree[right] = degree.get(right, 0) + 1
    return degree


def _random_segments(rng: random.Random) -> dict[tuple[str, str], float]:
    cities = [f"c{index}" for index in range(_CITIES)]
    segments: dict[tuple[str, str], float] = {}
    for index in range(1, _CITIES):
        joined = cities[rng.randrange(index)]
        segments[segment_key(cities[index], joined)] = float(rng.randrange(10, 400))
    for _extra in range(rng.randrange(2, 5)):
        left, right = rng.sample(cities, 2)
        segments[segment_key(left, right)] = float(rng.randrange(10, 400))
    for city in cities:
        while _degrees(segments).get(city, 0) < 2:
            other = rng.choice([one for one in cities if one != city])
            segments[segment_key(city, other)] = float(rng.randrange(10, 400))
    return segments


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
        f"segments={sorted(segments.items())}",
    )


_MEASURED = [found for found in (_measured(seed) for seed in range(_GRAPHS)) if found]
_REPORT = f"measured {len(_MEASURED)} of {_GRAPHS}, worst {sorted(_MEASURED)[-4:]}"


def test_the_probe_reports_the_graphs_whose_floor_sits_highest() -> None:
    assert not _REPORT, _REPORT
