from __future__ import annotations

from typing import Any

import fixtures
from synthesizer.input_graph import FiberSegment, Site, segment_key
from synthesizer.model import (
    HomingCircuit,
    Homings,
    Synthesis,
    SynthesisArtifacts,
    SynthesisMetrics,
)
from synthesizer.output import (
    synthesis_payload,
    homed_site_count,
    sorted_fiber_segments,
)

ARTIFACTS = fixtures.ring_artifacts()

_TENANT_HOMING = HomingCircuit("s", "b", 1.0)
_PROVIDER_HOMING = HomingCircuit("r", "b", 1.0)


def _synthesis(homings: Homings, metrics: SynthesisMetrics | None = None) -> Synthesis:
    return Synthesis(
        wan_pop_ids=(),
        transit_ids=(),
        homings=homings,
        fiber_segment_keys=set(),
        drawn_circuits=[],
        metrics=metrics or SynthesisMetrics(0.0, 0.0, 0.0, 0.0),
    )


def _payload_for(
    synthesis: Synthesis, sites: list[Site], fabricated_ids: frozenset[str] = frozenset()
) -> dict[str, Any]:
    fiber = {segment_key("b", "x"): FiberSegment("b", "x", 1.0)}
    artifacts = SynthesisArtifacts(
        [*sites, fixtures.carrier_pop("b")],
        fiber,
        synthesis,
        ARTIFACTS.validation,
        fabricated_ids,
    )
    return synthesis_payload(artifacts)


def _both_kinds(metrics: SynthesisMetrics | None = None) -> dict[str, Any]:
    return _payload_for(
        _synthesis(Homings([_TENANT_HOMING], [_PROVIDER_HOMING]), metrics),
        [fixtures.tenant_site("s"), fixtures.provider_region("r")],
    )


def test_synthesis_payload_includes_sites() -> None:
    assert "sites" in synthesis_payload(ARTIFACTS)


def test_synthesis_payload_sites_carry_location() -> None:
    sites = synthesis_payload(ARTIFACTS)["sites"]
    assert all(
        "municipality" in site["info"] and "state" in site["info"] for site in sites
    )


def test_synthesis_payload_summary_reports_wan_pop_count() -> None:
    summary = synthesis_payload(ARTIFACTS)["summary"]
    assert summary["wan_pop_count"] == len(ARTIFACTS.synthesis.wan_pop_ids)


def test_synthesis_payload_summary_lists_wan_pop_names() -> None:
    summary = synthesis_payload(ARTIFACTS)["summary"]
    assert len(summary["wan_pops"]) == len(ARTIFACTS.synthesis.wan_pop_ids)


def test_synthesis_payload_summary_publishes_the_floor_under_the_fiber_it_runs_over() -> None:
    summary = synthesis_payload(ARTIFACTS)["summary"]
    assert summary["backbone_lower_bound_miles"] <= summary["physical_carrier_miles"]


def test_sorted_fiber_segments_is_sorted() -> None:
    keys = sorted_fiber_segments(ARTIFACTS.synthesis)
    assert keys == sorted(keys)


def test_a_tenant_homing_circuit_is_labelled_tenant_to_backbone() -> None:
    payload = _payload_for(
        _synthesis(Homings([_TENANT_HOMING], [])), [fixtures.tenant_site("s")]
    )
    assert payload["homing_circuits"][0]["homing_kind"] == "tenant_to_backbone"


def test_a_provider_homing_circuit_is_labelled_provider_to_backbone() -> None:
    payload = _payload_for(
        _synthesis(Homings([], [_PROVIDER_HOMING])), [fixtures.provider_region("r")]
    )
    assert payload["homing_circuits"][0]["homing_kind"] == "provider_to_backbone"


def test_the_summary_counts_the_tenant_sites_a_wan_reaches() -> None:
    assert _both_kinds()["summary"]["tenant_site_count"] == 1


def test_the_summary_counts_the_provider_regions_a_wan_reaches_apart_from_them() -> None:
    assert _both_kinds()["summary"]["provider_region_count"] == 1


def test_the_summary_counts_the_homing_circuits_out_of_the_tenants_own_sites() -> None:
    assert _both_kinds()["summary"]["tenant_homing_circuit_count"] == 1


def test_the_summary_counts_the_homing_circuits_out_of_the_provider_regions() -> None:
    assert _both_kinds()["summary"]["provider_homing_circuit_count"] == 1


def test_the_summary_publishes_the_miles_run_to_the_tenants_own_sites() -> None:
    metrics = SynthesisMetrics(0.0, 120.5, 40.25, 0.0)
    assert _both_kinds(metrics)["summary"]["tenant_homing_miles"] == 120.5


def test_the_summary_publishes_the_miles_run_to_the_provider_regions_apart_from_them() -> None:
    metrics = SynthesisMetrics(0.0, 120.5, 40.25, 0.0)
    assert _both_kinds(metrics)["summary"]["provider_homing_miles"] == 40.25


def test_the_summary_totals_the_miles_of_both_kinds_with_the_fiber_run_over() -> None:
    metrics = SynthesisMetrics(0.0, 120.5, 40.25, 9.25)
    assert _both_kinds(metrics)["summary"]["total_synthesis_miles"] == 170.0


def test_a_site_that_homed_is_counted_once_however_many_circuits_it_holds() -> None:
    twice = [_TENANT_HOMING, HomingCircuit("s", "c", 2.0)]
    assert homed_site_count(twice) == 1


def test_a_site_that_homed_nowhere_is_counted_in_neither_kind() -> None:
    payload = _payload_for(
        _synthesis(Homings([_TENANT_HOMING], [])),
        [fixtures.tenant_site("s"), fixtures.tenant_site("stranded")],
    )
    assert payload["summary"]["tenant_site_count"] == 1


def _published_sites_with_a_twin() -> dict[str, dict[str, Any]]:
    payload = _payload_for(
        _synthesis(Homings([], [])),
        [fixtures.carrier_pop("fac_s")],
        frozenset({"fac_s"}),
    )
    return {site["id"]: site for site in payload["sites"]}


def test_a_site_the_synthesizer_fabricated_says_so() -> None:
    assert _published_sites_with_a_twin()["fac_s"]["fabricated"] is True


def test_a_carrier_pop_says_it_was_not_fabricated() -> None:
    assert _published_sites_with_a_twin()["b"]["fabricated"] is False


def test_every_published_site_says_whether_it_was_fabricated() -> None:
    assert all("fabricated" in site for site in synthesis_payload(ARTIFACTS)["sites"])
