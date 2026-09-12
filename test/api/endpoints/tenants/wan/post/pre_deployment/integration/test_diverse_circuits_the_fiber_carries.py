from __future__ import annotations

import pytest

import fixtures
from synthesizer.input_graph import FiberSegment, Site
from synthesizer.model import (
    RoleExclusions,
    SynthesisArtifacts,
    SynthesisParams,
    Tuning,
)

_SEATS = 3


def _artifacts(
    sites: list[Site],
    fiber_segments: dict[tuple[str, str], FiberSegment],
    transit_names: tuple[str, ...],
) -> SynthesisArtifacts:
    return fixtures.run_synthesis(
        sites,
        fiber_segments,
        SynthesisParams(
            min_wan_pop_count=_SEATS,
            max_wan_pop_count=_SEATS,
            exclusions=RoleExclusions(prohibited_wan_pop_names=transit_names),
            promote_high_degree_convergences=False,
            tuning=Tuning(backbone_number_of_diverse_circuits=2),
        ),
    )


@pytest.fixture(name="crossing", scope="module")
def _crossing() -> SynthesisArtifacts:
    return _artifacts(
        fixtures.crossing_sites(),
        fixtures.CROSSING_FIBER,
        fixtures.crossing_transit_names(),
    )


@pytest.fixture(name="distant_peer", scope="module")
def _distant_peer() -> SynthesisArtifacts:
    return _artifacts(
        fixtures.distant_peer_sites(),
        fixtures.DISTANT_PEER_FIBER,
        fixtures.distant_peer_transit_names(),
    )


@pytest.fixture(name="express", scope="module")
def _express() -> SynthesisArtifacts:
    return _artifacts(
        fixtures.express_sites(),
        fixtures.EXPRESS_FIBER,
        fixtures.express_transit_names(),
    )


def _cities_crossed(artifacts: SynthesisArtifacts) -> set[str]:
    return {
        city
        for drawn_circuit in artifacts.synthesis.drawn_circuits
        if drawn_circuit.purpose == "backbone_mesh"
        for city in drawn_circuit.pop_ids
    }


def _mesh_miles(artifacts: SynthesisArtifacts) -> float:
    return sum(
        drawn_circuit.distance_miles for drawn_circuit in artifacts.synthesis.drawn_circuits
        if drawn_circuit.purpose == "backbone_mesh"
    )


def test_a_crossing_is_taken_where_it_is_a_sites_second_diverse_circuit(
    crossing: SynthesisArtifacts,
) -> None:
    assert "tok" in _cities_crossed(crossing)


def test_a_wan_a_crossing_would_answer_but_a_circuit_over_land_holds_off_is_refused_as_split(
) -> None:
    with pytest.raises(ValueError, match="splits the WAN at: pdx"):
        _artifacts(
            fixtures.crossing_sites(),
            fixtures.CROSSING_SUBMARINE_FIBER,
            fixtures.crossing_transit_names(),
        )


def test_the_synthesis_wires_every_site_into_one_backbone(
    crossing: SynthesisArtifacts,
) -> None:
    assert crossing.validation["connected"]


def test_no_site_is_credited_with_a_diverse_circuit_its_fiber_does_not_carry(
    crossing: SynthesisArtifacts,
) -> None:
    assert crossing.validation["backbone_diverse_circuits_ceiling_limited"] == []


def test_no_site_is_asked_for_a_circuit_its_fiber_cannot_lay(
    distant_peer: SynthesisArtifacts,
) -> None:
    assert distant_peer.validation["backbone_mesh_independence_deficient"] == []


def test_the_finished_synthesis_orders_the_fewest_fiber_miles_it_can_be_wired_with(
    express: SynthesisArtifacts,
) -> None:
    assert _mesh_miles(express) == 6.0


def test_the_ring_synthesis_holds_every_site_to_the_two_circuits_its_fiber_carries(
    express: SynthesisArtifacts,
) -> None:
    assert express.validation["backbone_mesh_independence_deficient"] == []
