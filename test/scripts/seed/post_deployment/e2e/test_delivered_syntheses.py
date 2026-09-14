from __future__ import annotations

from typing import Any

_SPLIT_REFUSAL = "splits the WAN at: "


def _refused_for_a_split(status: dict[str, Any]) -> bool:
    return status.get("status") == "fail" and _SPLIT_REFUSAL in status.get("reason", "")


def test_every_tenant_the_roster_declares_is_published_or_refused_for_a_split(
        delivered_syntheses: list[dict[str, Any]]) -> None:
    unfinished = {
        synthesis["tenant"]: synthesis["status"].get("status")
        for synthesis in delivered_syntheses
        if synthesis["status"].get("status") != "success"
        and not _refused_for_a_split(synthesis["status"])
    }
    assert unfinished == {}


def test_every_split_refusal_names_the_pop_whose_loss_would_split_the_wan(
        delivered_syntheses: list[dict[str, Any]]) -> None:
    unnamed = [
        synthesis["tenant"]
        for synthesis in delivered_syntheses
        if _refused_for_a_split(synthesis["status"])
        and not synthesis["status"]["reason"].split(_SPLIT_REFUSAL, 1)[1].strip()
    ]
    assert unnamed == []


def test_every_published_network_reports_the_coverage_it_delivered(
        published_syntheses: list[dict[str, Any]]) -> None:
    silent = [
        synthesis["tenant"]
        for synthesis in published_syntheses
        if "coverage" not in synthesis["status"]
    ]
    assert silent == []


def test_every_report_is_measured_against_the_target_its_tenant_declares(
        published_syntheses: list[dict[str, Any]]) -> None:
    reported = {
        synthesis["tenant"]: synthesis["status"]["coverage"]["target_miles"]
        for synthesis in published_syntheses
    }
    declared = {synthesis["tenant"]: synthesis["target_miles"] for synthesis in published_syntheses}
    assert reported == declared


def test_no_published_status_carries_a_backup_path_multiple(
        published_syntheses: list[dict[str, Any]]) -> None:
    assert [
        synthesis["tenant"]
        for synthesis in published_syntheses
        if "max_backup_path_multiple" in synthesis["status"]
    ] == []


def test_no_published_network_leaves_a_site_short_of_the_circuits_it_was_asked_for(
        published_syntheses: list[dict[str, Any]]) -> None:
    short = {
        synthesis["tenant"]: synthesis["status"]["diverse_circuits"]["short"]
        for synthesis in published_syntheses
    }
    assert {tenant: sites for tenant, sites in short.items() if sites} == {}
