from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from healthcare_pipeline.parsers.hl7.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.patient_location import PatientLocation
from healthcare_pipeline.parsers.hl7.provider import Provider
from healthcare_pipeline.parsers.hl7.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class MedicationAdministration:
    """Immutable semantic medication-administration representation from RXA."""

    give_sub_id: int
    administration_sub_id: int
    start_datetime: datetime
    administered_code: CodedValue
    administered_amount: Decimal
    administered_units: CodedValue | None = None
    end_datetime: datetime | None = None
    administration_notes: tuple[CodedValue, ...] = ()
    administering_providers: tuple[Provider, ...] = ()
    administered_at_location: PatientLocation | None = None
    lot_number: str | None = None
    expiration_date: date | None = None
    manufacturer: CodedValue | None = None
    refusal_reason: CodedValue | None = None
    indication: CodedValue | None = None
    completion_status: str | None = None
    action_code: str | None = None
    system_entry_datetime: datetime | None = None

    def __post_init__(self) -> None:
        if self.give_sub_id < 0 or self.administration_sub_id < 0:
            raise ValueError("sub IDs must not be negative")
        if self.start_datetime.tzinfo is None:
            raise ValueError("start_datetime must be timezone-aware")
        if self.end_datetime is not None and self.end_datetime.tzinfo is None:
            raise ValueError("end_datetime must be timezone-aware")
        if self.end_datetime is not None and self.end_datetime < self.start_datetime:
            raise ValueError("end_datetime must not precede start_datetime")
        if not isinstance(self.administered_code, CodedValue):
            raise TypeError("administered_code must be a CodedValue")
        if self.administered_amount < 0:
            raise ValueError("administered_amount must not be negative")
        for field_name, expected_type in (
            ("administration_notes", CodedValue),
            ("administering_providers", Provider),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
        for field_name in ("lot_number", "completion_status", "action_code"):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        if self.system_entry_datetime is not None and self.system_entry_datetime.tzinfo is None:
            raise ValueError("system_entry_datetime must be timezone-aware")
