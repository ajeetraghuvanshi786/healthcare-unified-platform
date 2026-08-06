from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.parsers.hl7.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.provider import Provider
from healthcare_pipeline.parsers.hl7.semantic import normalize_optional, normalize_required


@dataclass(frozen=True, slots=True)
class ObservationResult:
    """Immutable semantic observation-result representation from OBX."""

    set_id: int
    value_type: str
    observation_identifier: CodedValue
    values: tuple[str, ...]
    result_status: str
    observation_sub_id: str | None = None
    units: CodedValue | None = None
    reference_range: str | None = None
    abnormal_flags: tuple[str, ...] = ()
    observation_datetime: datetime | None = None
    producer_identifier: CodedValue | None = None
    responsible_observers: tuple[Provider, ...] = ()
    observation_method: tuple[CodedValue, ...] = ()
    equipment_instance_identifiers: tuple[str, ...] = ()
    analysis_datetime: datetime | None = None

    def __post_init__(self) -> None:
        if self.set_id < 1:
            raise ValueError("set_id must be greater than zero")
        object.__setattr__(
            self,
            "value_type",
            normalize_required(self.value_type, "value_type").upper(),
        )
        if not isinstance(self.observation_identifier, CodedValue):
            raise TypeError("observation_identifier must be a CodedValue")
        object.__setattr__(
            self,
            "result_status",
            normalize_required(self.result_status, "result_status").upper(),
        )
        object.__setattr__(
            self,
            "observation_sub_id",
            normalize_optional(self.observation_sub_id, "observation_sub_id"),
        )
        normalized_values = tuple(value.strip() for value in self.values if value.strip())
        if not normalized_values:
            raise ValueError("values must contain at least one non-blank value")
        object.__setattr__(self, "values", normalized_values)
        object.__setattr__(
            self,
            "reference_range",
            normalize_optional(self.reference_range, "reference_range"),
        )
        for field_name in ("abnormal_flags", "equipment_instance_identifiers"):
            values = tuple(
                normalized
                for value in getattr(self, field_name)
                if (normalized := normalize_optional(value, field_name)) is not None
            )
            object.__setattr__(self, field_name, values)
        for field_name, expected_type in (
            ("responsible_observers", Provider),
            ("observation_method", CodedValue),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
        for field_name in ("observation_datetime", "analysis_datetime"):
            value = getattr(self, field_name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware")
