from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from healthcare_pipeline.parsers.hl7.administrative_sex import (
    AdministrativeSex,
)
from healthcare_pipeline.parsers.hl7.patient_address import PatientAddress
from healthcare_pipeline.parsers.hl7.patient_identifier import PatientIdentifier
from healthcare_pipeline.parsers.hl7.patient_name import PatientName
from healthcare_pipeline.parsers.hl7.patient_phone import PatientPhone


@dataclass(frozen=True, slots=True)
class Patient:
    """Immutable semantic patient representation produced from PID data."""

    identifiers: tuple[PatientIdentifier, ...]
    names: tuple[PatientName, ...]
    birth_date: date | None = None
    administrative_sex: AdministrativeSex = AdministrativeSex.UNKNOWN
    addresses: tuple[PatientAddress, ...] = ()
    phones: tuple[PatientPhone, ...] = ()
    set_id: int | None = None
    patient_account_number: PatientIdentifier | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "identifiers", tuple(self.identifiers))
        object.__setattr__(self, "names", tuple(self.names))
        object.__setattr__(self, "addresses", tuple(self.addresses))
        object.__setattr__(self, "phones", tuple(self.phones))

        if not self.identifiers:
            raise ValueError("patient must contain at least one identifier")
        if not self.names:
            raise ValueError("patient must contain at least one name")

        if not all(
            isinstance(identifier, PatientIdentifier)
            for identifier in self.identifiers
        ):
            raise TypeError("identifiers must contain PatientIdentifier values")
        if not all(isinstance(name, PatientName) for name in self.names):
            raise TypeError("names must contain PatientName values")
        if not all(
            isinstance(address, PatientAddress) for address in self.addresses
        ):
            raise TypeError("addresses must contain PatientAddress values")
        if not all(isinstance(phone, PatientPhone) for phone in self.phones):
            raise TypeError("phones must contain PatientPhone values")

        if self.birth_date is not None:
            if not isinstance(self.birth_date, date):
                raise TypeError("birth_date must be a date or None")
            if self.birth_date > date.today():
                raise ValueError("birth_date must not be in the future")

        if not isinstance(self.administrative_sex, AdministrativeSex):
            raise TypeError(
                "administrative_sex must be an AdministrativeSex value"
            )

        if self.set_id is not None:
            if not isinstance(self.set_id, int):
                raise TypeError("set_id must be an integer or None")
            if self.set_id < 1:
                raise ValueError("set_id must be greater than zero")

        if self.patient_account_number is not None and not isinstance(
            self.patient_account_number,
            PatientIdentifier,
        ):
            raise TypeError(
                "patient_account_number must be a PatientIdentifier or None"
            )

        identity_keys = [identifier.identity_key for identifier in self.identifiers]
        if len(identity_keys) != len(set(identity_keys)):
            raise ValueError("patient identifiers must not contain duplicates")

    @property
    def primary_identifier(self) -> PatientIdentifier:
        """Return the first identifier in source-system priority order."""

        return self.identifiers[0]

    @property
    def official_name(self) -> PatientName:
        """Return the first name in source-system priority order."""

        return self.names[0]
