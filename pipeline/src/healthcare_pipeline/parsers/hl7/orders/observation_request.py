from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.parsers.hl7.datatypes.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.datatypes.order_identifier import OrderIdentifier
from healthcare_pipeline.parsers.hl7.encounters.provider import Provider
from healthcare_pipeline.parsers.hl7.mapping.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class ObservationRequest:
    """Immutable semantic observation-request representation from OBR."""

    set_id: int
    universal_service_identifier: CodedValue
    placer_order_number: OrderIdentifier | None = None
    filler_order_number: OrderIdentifier | None = None
    requested_datetime: datetime | None = None
    observation_datetime: datetime | None = None
    observation_end_datetime: datetime | None = None
    collector_identifiers: tuple[Provider, ...] = ()
    relevant_clinical_information: str | None = None
    specimen_received_datetime: datetime | None = None
    specimen_source: CodedValue | None = None
    ordering_providers: tuple[Provider, ...] = ()
    placer_field_1: str | None = None
    placer_field_2: str | None = None
    filler_field_1: str | None = None
    filler_field_2: str | None = None
    result_status_change_datetime: datetime | None = None
    diagnostic_service_section: str | None = None
    result_status: str | None = None
    quantity_timing: str | None = None
    result_copy_providers: tuple[Provider, ...] = ()
    reasons_for_study: tuple[CodedValue, ...] = ()

    def __post_init__(self) -> None:
        if self.set_id < 1:
            raise ValueError("set_id must be greater than zero")
        if not isinstance(self.universal_service_identifier, CodedValue):
            raise TypeError("universal_service_identifier must be a CodedValue")
        for field_name in (
            "relevant_clinical_information",
            "placer_field_1",
            "placer_field_2",
            "filler_field_1",
            "filler_field_2",
            "diagnostic_service_section",
            "result_status",
            "quantity_timing",
        ):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        for field_name, expected_type in (
            ("collector_identifiers", Provider),
            ("ordering_providers", Provider),
            ("result_copy_providers", Provider),
            ("reasons_for_study", CodedValue),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
        for field_name in (
            "requested_datetime",
            "observation_datetime",
            "observation_end_datetime",
            "specimen_received_datetime",
            "result_status_change_datetime",
        ):
            value = getattr(self, field_name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware")
        if (
            self.observation_datetime is not None
            and self.observation_end_datetime is not None
            and self.observation_end_datetime < self.observation_datetime
        ):
            raise ValueError("observation_end_datetime must not precede observation_datetime")
