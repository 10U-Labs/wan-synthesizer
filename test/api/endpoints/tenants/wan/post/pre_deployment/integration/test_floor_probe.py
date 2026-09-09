from __future__ import annotations

import random

import fixtures
from synthesizer.input_graph import FiberSegment, segment_key
from synthesizer.model import SynthesisArtifacts, SynthesisParams, Tuning

_ASKED_FOR = 2
_SLACK = 1e-6
_CITIES = 7
_GRAPHS = 40
_SEATS = 3


def _over_chosen_seats(
    fiber: dict[tuple[str, str], FiberSegment], seats: int
) -> SynthesisArtifacts:
    cities = sorted({city for pair in fiber for city in pair})
    return fixtures.run_synthesis(
        [
            fixtures.carrier_pop(city, 38.0, -115.0 + 2.0 * index)
            for index, city in enumerate(cities)
        ],
        fiber,
        SynthesisParams(
            min_backbone_count=seats,
            max_backbone_count=seats,
            promote_high_degree_convergences=False,
            tuning=Tuning(backbone_number_of_diverse_circuits=_ASKED_FOR),
        ),
    )


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
    return segments


def _measured(seed: int) -> str | None:
    segments = _random_segments(random.Random(seed))
    if len(_degrees(segments)) < _CITIES or min(_degrees(segments).values()) < 2:
        return None
    try:
        artifacts = _over_chosen_seats(fixtures.fiber_segments_from(segments), _SEATS)
    except ValueError:
        return None
    run = artifacts.synthesis.metrics.physical_miles
    floor = artifacts.synthesis.metrics.backbone_lower_bound_miles
    if run >= floor - _SLACK:
        return None
    return (
        f"seed={seed} seats={artifacts.synthesis.backbone_ids} "
        f"run={run} floor={floor} segments={sorted(segments.items())}"
    )


_FOUND = [found for found in (_measured(seed) for seed in range(_GRAPHS)) if found]


def test_no_random_graph_is_floored_above_the_miles_it_runs_over() -> None:
    assert not _FOUND, _FOUND
