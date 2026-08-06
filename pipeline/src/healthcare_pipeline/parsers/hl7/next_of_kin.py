from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from healthcare_pipeline.parsers.hl7.administrative_sex import AdministrativeSex
from healthcare_pipeline.parsers.hl7.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.patient_address import PatientAddress
from healthcare_pipeline.parsers.hl7.patient_name import PatientName
from healthcare_pipeline.parsers.hl7.patient_phone import PatientPhone
from healthcare_pipeline.parsers.hl7.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class NextOfKin:
    """Immutable semantic representation of one NK1 segment."""

    names: tuple[PatientName, ...]
    set_id: int | None = None
    relationship: CodedValue | None = None
    addresses: tuple[PatientAddress, ...] = ()
    phones: tuple[PatientPhone, ...] = ()
    business_phones: tuple[PatientPhone, ...] = ()
    contact_roles: tuple[CodedValue, ...] = ()
    start_date: date | None = None
    end_date: date | None = None
    organization_name: str | None = None
    administrative_sex: AdministrativeSex = AdministrativeSex.UNKNOWN
    birth_date: date | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "names", tuple(self.names))
        object.__setattr__(self, "addresses", tuple(self.addresses))
        object.__setattr__(self, "phones", tuple(self.phones))
        object.__setattr__(self, "business_phones", tuple(self.business_phones))
        object.__setattr__(self, "contact_roles", tuple(self.contact_roles))

        if not self.names:
            raise ValueError("next of kin must contain at least one name")
        if self.set_id is not None and self.set_id < 1:
            raise ValueError("set_id must be greater than zero")
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError(
                "end_date must not precede start_date"
            )
        object.__setattr__(
            self,
            "organization_name",
            normalize_optional(self.organization_name, "organization_name"),
        )

    @property
    def primary_name(self) -> PatientName:
        return self.names[0]
