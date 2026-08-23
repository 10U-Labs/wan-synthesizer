from __future__ import annotations

from dataclasses import dataclass, field

from synthesizer.model import ForcedPaths, Tuning


@dataclass(frozen=True)
class _SearchPlan:
    backbone_candidates: list[str]
    strength_by_id: dict[str, float]
    tuning: Tuning = field(default_factory=Tuning)
    forced_paths: ForcedPaths = field(default_factory=ForcedPaths)
    seat_cap: int | None = None

    @property
    def required_backbone(self) -> frozenset[str]:
        return self.forced_paths.required_backbone
