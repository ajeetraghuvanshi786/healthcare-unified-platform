from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.canonical.clinical.provider import Provider
from healthcare_pipeline.canonical.common._validation import ensure_aware, normalize_optional
from healthcare_pipeline.canonical.common.coding import Coding


@dataclass(frozen=True, slots=True)
class Diagnosis:
    """Canonical diagnosis associated with care, independent of source encoding."""

    code: Coding
    recorded_datetime: datetime | None = None
    diagnosis_type: str | None = None
    priority: int | None = None
    diagnosing_providers: tuple[Provider, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.code, Coding):
            raise TypeError("code must be a Coding")
        ensure_aware(self.recorded_datetime, "recorded_datetime")
        object.__setattr__(
            self,
            "diagnosis_type",
            normalize_optional(self.diagnosis_type, "diagnosis_type"),
        )
        if self.priority is not None and self.priority < 1:
            raise ValueError("priority must be greater than zero")
        providers = tuple(self.diagnosing_providers)
        if not all(isinstance(value, Provider) for value in providers):
            raise TypeError("diagnosing_providers must contain Provider values")
        object.__setattr__(self, "diagnosing_providers", providers)
