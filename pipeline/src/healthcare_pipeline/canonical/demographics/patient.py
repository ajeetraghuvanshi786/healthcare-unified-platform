from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from healthcare_pipeline.canonical.common.address import Address
from healthcare_pipeline.canonical.common.contact_point import ContactPoint
from healthcare_pipeline.canonical.common.human_name import HumanName
from healthcare_pipeline.canonical.common.identifier import Identifier


class AdministrativeGender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Patient:
    """Canonical patient independent of HL7, FHIR, CDA, or other source formats."""

    identifiers: tuple[Identifier, ...]
    names: tuple[HumanName, ...]
    birth_date: date | None = None
    administrative_gender: AdministrativeGender = AdministrativeGender.UNKNOWN
    addresses: tuple[Address, ...] = ()
    telecom: tuple[ContactPoint, ...] = ()
    account_identifiers: tuple[Identifier, ...] = ()

    def __post_init__(self) -> None:
        for field_name, expected_type in (
            ("identifiers", Identifier),
            ("names", HumanName),
            ("addresses", Address),
            ("telecom", ContactPoint),
            ("account_identifiers", Identifier),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
        if not self.identifiers:
            raise ValueError("patient must contain at least one identifier")
        if not self.names:
            raise ValueError("patient must contain at least one name")
        if not isinstance(self.administrative_gender, AdministrativeGender):
            raise TypeError("administrative_gender must be an AdministrativeGender")
        if self.birth_date is not None and self.birth_date > date.today():
            raise ValueError("birth_date must not be in the future")
        keys = [identifier.identity_key for identifier in self.identifiers]
        if len(keys) != len(set(keys)):
            raise ValueError("patient identifiers must not contain duplicates")

    @property
    def primary_identifier(self) -> Identifier:
        return self.identifiers[0]
