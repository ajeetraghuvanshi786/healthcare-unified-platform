from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.canonical.clinical.observation import Observation
from healthcare_pipeline.canonical.clinical.provider import Provider
from healthcare_pipeline.canonical.common._validation import ensure_aware, normalize_optional
from healthcare_pipeline.canonical.common.coding import Coding
from healthcare_pipeline.canonical.common.identifier import Identifier


@dataclass(frozen=True, slots=True)
class ObservationOrder:
    """Canonical diagnostic/clinical observation request with attached results."""

    service: Coding
    identifiers: tuple[Identifier, ...] = ()
    status: str | None = None
    requested_datetime: datetime | None = None
    observation_datetime: datetime | None = None
    ordering_providers: tuple[Provider, ...] = ()
    reasons: tuple[Coding, ...] = ()
    results: tuple[Observation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.service, Coding):
            raise TypeError("service must be a Coding")
        for field_name, expected_type in (
            ("identifiers", Identifier),
            ("ordering_providers", Provider),
            ("reasons", Coding),
            ("results", Observation),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
        object.__setattr__(self, "status", normalize_optional(self.status, "status"))
        ensure_aware(self.requested_datetime, "requested_datetime")
        ensure_aware(self.observation_datetime, "observation_datetime")
