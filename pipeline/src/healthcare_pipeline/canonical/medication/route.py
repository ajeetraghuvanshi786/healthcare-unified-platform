from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common.coding import Coding


@dataclass(frozen=True, slots=True)
class MedicationRoute:
    """Canonical route/site/method information for medication delivery."""

    route: Coding
    site: Coding | None = None
    method: Coding | None = None
    device: Coding | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.route, Coding):
            raise TypeError("route must be a Coding")
