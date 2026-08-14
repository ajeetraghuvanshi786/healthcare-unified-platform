from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from healthcare_pipeline.canonical.common.address import Address
from healthcare_pipeline.canonical.common.contact_point import ContactPoint, ContactPointSystem
from healthcare_pipeline.canonical.common.human_name import HumanName
from healthcare_pipeline.canonical.common.identifier import Identifier
from healthcare_pipeline.canonical.demographics.patient import AdministrativeGender, Patient


@dataclass(frozen=True, slots=True)
class PatientIdentitySnapshotSerializer:
    """Serialize only canonical patient identity data for encrypted EMPI candidate storage."""

    def dumps(self, patient: Patient) -> bytes:
        if not isinstance(patient, Patient):
            raise TypeError("patient must be a canonical Patient")
        payload = {
            "identifiers": [self._identifier(value) for value in patient.identifiers],
            "names": [self._name(value) for value in patient.names],
            "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
            "administrative_gender": patient.administrative_gender.value,
            "addresses": [self._address(value) for value in patient.addresses],
            "telecom": [self._contact(value) for value in patient.telecom],
            "account_identifiers": [
                self._identifier(value) for value in patient.account_identifiers
            ],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

    def loads(self, payload: bytes) -> Patient:
        if not isinstance(payload, bytes) or not payload:
            raise ValueError("payload must be non-empty bytes")
        raw: dict[str, Any] = json.loads(payload.decode())
        birth_date = date.fromisoformat(raw["birth_date"]) if raw.get("birth_date") else None
        return Patient(
            identifiers=tuple(self._identifier_from(value) for value in raw["identifiers"]),
            names=tuple(self._name_from(value) for value in raw["names"]),
            birth_date=birth_date,
            administrative_gender=AdministrativeGender(raw["administrative_gender"]),
            addresses=tuple(self._address_from(value) for value in raw.get("addresses", [])),
            telecom=tuple(self._contact_from(value) for value in raw.get("telecom", [])),
            account_identifiers=tuple(
                self._identifier_from(value) for value in raw.get("account_identifiers", [])
            ),
        )

    @staticmethod
    def _identifier(value: Identifier) -> dict[str, Any]:
        return {
            "value": value.value,
            "system": value.system,
            "type_code": value.type_code,
            "assigner": value.assigner,
        }

    @staticmethod
    def _identifier_from(value: dict[str, Any]) -> Identifier:
        return Identifier(**value)

    @staticmethod
    def _name(value: HumanName) -> dict[str, Any]:
        return {
            "family": value.family,
            "given": list(value.given),
            "prefix": list(value.prefix),
            "suffix": list(value.suffix),
            "use": value.use,
        }

    @staticmethod
    def _name_from(value: dict[str, Any]) -> HumanName:
        return HumanName(
            family=value.get("family"),
            given=tuple(value.get("given", [])),
            prefix=tuple(value.get("prefix", [])),
            suffix=tuple(value.get("suffix", [])),
            use=value.get("use"),
        )

    @staticmethod
    def _address(value: Address) -> dict[str, Any]:
        return {
            "lines": list(value.lines),
            "city": value.city,
            "state": value.state,
            "postal_code": value.postal_code,
            "country": value.country,
            "district": value.district,
            "use": value.use,
        }

    @staticmethod
    def _address_from(value: dict[str, Any]) -> Address:
        return Address(
            lines=tuple(value.get("lines", [])),
            city=value.get("city"),
            state=value.get("state"),
            postal_code=value.get("postal_code"),
            country=value.get("country"),
            district=value.get("district"),
            use=value.get("use"),
        )

    @staticmethod
    def _contact(value: ContactPoint) -> dict[str, Any]:
        return {
            "system": value.system.value,
            "value": value.value,
            "use": value.use,
            "rank": value.rank,
        }

    @staticmethod
    def _contact_from(value: dict[str, Any]) -> ContactPoint:
        return ContactPoint(
            system=ContactPointSystem(value["system"]),
            value=value["value"],
            use=value.get("use"),
            rank=value.get("rank"),
        )
