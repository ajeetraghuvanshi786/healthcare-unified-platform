from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from healthcare_pipeline.parsers.hl7.datatypes.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.datatypes.order_identifier import OrderIdentifier
from healthcare_pipeline.parsers.hl7.demographics.patient_address import PatientAddress
from healthcare_pipeline.parsers.hl7.demographics.patient_phone import PatientPhone
from healthcare_pipeline.parsers.hl7.encounters.patient_location import PatientLocation
from healthcare_pipeline.parsers.hl7.encounters.provider import Provider
from healthcare_pipeline.parsers.hl7.mapping.semantic import normalize_optional, normalize_required


@dataclass(frozen=True, slots=True)
class CommonOrder:
    """Immutable semantic common-order representation from ORC."""

    order_control: str
    placer_order_number: OrderIdentifier | None = None
    filler_order_number: OrderIdentifier | None = None
    placer_group_number: OrderIdentifier | None = None
    order_status: str | None = None
    quantity_timing: str | None = None
    transaction_datetime: datetime | None = None
    entered_by: tuple[Provider, ...] = ()
    ordering_providers: tuple[Provider, ...] = ()
    enterer_location: PatientLocation | None = None
    effective_datetime: datetime | None = None
    order_control_reason: CodedValue | None = None
    entering_organization: CodedValue | None = None
    ordering_facility_name: str | None = None
    ordering_facility_addresses: tuple[PatientAddress, ...] = ()
    ordering_facility_phones: tuple[PatientPhone, ...] = ()
    order_type: CodedValue | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "order_control",
            normalize_required(self.order_control, "order_control").upper(),
        )
        for field_name in (
            "order_status",
            "quantity_timing",
            "ordering_facility_name",
        ):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        for field_name, expected_type in (
            ("entered_by", Provider),
            ("ordering_providers", Provider),
            ("ordering_facility_addresses", PatientAddress),
            ("ordering_facility_phones", PatientPhone),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
        for field_name in ("transaction_datetime", "effective_datetime"):
            value = getattr(self, field_name)
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware")
