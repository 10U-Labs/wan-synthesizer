from __future__ import annotations

from dataclasses import dataclass, field

from synthesizer.model import ForcedCircuits, Tuning


@dataclass(frozen=True)
class _SearchPlan:
    backbone_candidates: list[str]
    strength_by_id: dict[str, float]
    tuning: Tuning = field(default_factory=Tuning)
    forced_circuits: ForcedCircuits = field(default_factory=ForcedCircuits)
    seat_cap: int | None = None

    @property
    def required_backbone(self) -> frozenset[str]:
        return self.forced_circuits.required_backbone
