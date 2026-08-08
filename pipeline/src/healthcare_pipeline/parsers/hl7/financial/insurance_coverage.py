from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from healthcare_pipeline.parsers.hl7.datatypes.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.demographics.patient_address import PatientAddress
from healthcare_pipeline.parsers.hl7.demographics.patient_identifier import PatientIdentifier
from healthcare_pipeline.parsers.hl7.demographics.patient_name import PatientName
from healthcare_pipeline.parsers.hl7.demographics.patient_phone import PatientPhone
from healthcare_pipeline.parsers.hl7.mapping.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class InsuranceCoverage:
    """Immutable semantic insurance coverage representation from IN1."""

    set_id: int
    plan_identifier: CodedValue | None = None
    company_identifiers: tuple[PatientIdentifier, ...] = ()
    company_name: str | None = None
    company_addresses: tuple[PatientAddress, ...] = ()
    contact_names: tuple[PatientName, ...] = ()
    contact_phones: tuple[PatientPhone, ...] = ()
    group_number: str | None = None
    group_name: str | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    plan_type: str | None = None
    insured_names: tuple[PatientName, ...] = ()
    insured_relationship: CodedValue | None = None
    insured_birth_date: date | None = None
    insured_addresses: tuple[PatientAddress, ...] = ()
    policy_number: str | None = None
    insured_identifiers: tuple[PatientIdentifier, ...] = ()

    def __post_init__(self) -> None:
        if self.set_id < 1:
            raise ValueError("set_id must be greater than zero")
        for field_name in (
            "company_identifiers",
            "company_addresses",
            "contact_names",
            "contact_phones",
            "insured_names",
            "insured_addresses",
            "insured_identifiers",
        ):
            object.__setattr__(self, field_name, tuple(getattr(self, field_name)))
        for field_name in (
            "company_name",
            "group_number",
            "group_name",
            "plan_type",
            "policy_number",
        ):
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        if (
            self.effective_date is not None
            and self.expiration_date is not None
            and self.expiration_date < self.effective_date
        ):
            raise ValueError("expiration_date must not precede effective_date")
