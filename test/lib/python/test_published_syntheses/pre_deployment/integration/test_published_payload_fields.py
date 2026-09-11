from __future__ import annotations

from dataclasses import replace
from typing import Any

import fixtures
from synthesizer import collections as published
from synthesizer.model import OperatorCircuits, Tuning
from synthesizer.output import synthesis_payload

_SEATED_RING = replace(
    fixtures.ring_params(),
    forced_wan_pop_names=("P0", "P1", "P2", "P3", "P4", "P5"),
    tuning=Tuning(backbone_number_of_diverse_circuits=2),
)
_PAYLOAD = synthesis_payload(
    fixtures.forced_circuit_artifacts(
        _SEATED_RING, OperatorCircuits(), fixtures.ring_inputs_with_demand("S1", "P0")
    )
)

_WAN_POP_FIELDS = ("id", "name", "kind", "coords")
_SITE_FIELDS = (*_WAN_POP_FIELDS, "exempt_from_distance_constraint")
_CIRCUIT_FIELDS = ("source_id", "target_id", "distance_miles", "route")
_HOMING_FIELDS = ("source_id", "target_id", "distance_miles", "homing_kind")
_SEGMENT_FIELDS = ("source_id", "target_id", "distance_miles", "submarine")


def _subjects() -> list[tuple[str, list[dict[str, Any]], tuple[str, ...]]]:
    return [
        ("wan-pops", published.wan_pops(_PAYLOAD), _WAN_POP_FIELDS),
        ("tenant-nodes", published.tenant_nodes(_PAYLOAD), _SITE_FIELDS),
        ("backbone-circuits", published.backbone_circuits(_PAYLOAD), _CIRCUIT_FIELDS),
        ("homing-circuits", published.homing_circuits(_PAYLOAD), _HOMING_FIELDS),
        ("fiber-segments", published.fiber_segments(_PAYLOAD), _SEGMENT_FIELDS),
    ]


def test_every_collection_the_helpers_read_has_a_record_in_it() -> None:
    assert [name for name, records, _ in _subjects() if not records] == []


def test_every_field_the_helpers_read_is_one_the_collections_publish() -> None:
    absent = [
        (name, field)
        for name, records, fields in _subjects()
        for field in fields
        for record in records
        if field not in record
    ]
    assert absent == []
