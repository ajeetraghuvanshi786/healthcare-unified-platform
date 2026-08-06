from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.parsers.hl7.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.provider import Provider
from healthcare_pipeline.parsers.hl7.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class Diagnosis:
    """Immutable semantic diagnosis representation from DG1."""

    set_id: int
    code: CodedValue
    coding_method: str | None = None
    description: str | None = None
    diagnosis_datetime: datetime | None = None
    diagnosis_type: str | None = None
    priority: int | None = None
    diagnosing_providers: tuple[Provider, ...] = ()
    attestation_datetime: datetime | None = None

    def __post_init__(self) -> None:
        if self.set_id < 1:
            raise ValueError("set_id must be greater than zero")
        if not isinstance(self.code, CodedValue):
            raise TypeError("code must be a CodedValue")
        object.__setattr__(self, "diagnosing_providers", tuple(self.diagnosing_providers))
        if not all(isinstance(value, Provider) for value in self.diagnosing_providers):
            raise TypeError("diagnosing_providers must contain Provider values")
        if self.priority is not None and self.priority < 1:
            raise ValueError("priority must be greater than zero")
        for field_name in ("coding_method", "description", "diagnosis_type"):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        for field_name in ("diagnosis_datetime", "attestation_datetime"):
            value = getattr(self, field_name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware")
