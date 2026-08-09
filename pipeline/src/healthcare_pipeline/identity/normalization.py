from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from healthcare_pipeline.canonical.common.contact_point import ContactPointSystem
from healthcare_pipeline.canonical.common.human_name import HumanName
from healthcare_pipeline.canonical.common.identifier import Identifier
from healthcare_pipeline.canonical.demographics.patient import Patient

_WHITESPACE = re.compile(r"\s+")
_NON_DIGIT = re.compile(r"\D+")


def _nfkc(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip()


def _fold(value: str) -> str:
    return _WHITESPACE.sub(" ", _nfkc(value)).casefold()


@dataclass(frozen=True, slots=True)
class NormalizedPatientIdentity:
    scoped_identifiers: tuple[str, ...]
    name_keys: tuple[str, ...]
    birth_date: str | None
    phones: tuple[str, ...]
    emails: tuple[str, ...]
    postal_codes: tuple[str, ...]


class PatientIdentityNormalizer:
    """Conservative deterministic normalization used only for identity candidate matching."""

    def normalize(self, patient: Patient) -> NormalizedPatientIdentity:
        if not isinstance(patient, Patient):
            raise TypeError("patient must be a canonical Patient")
        return NormalizedPatientIdentity(
            scoped_identifiers=self._identifier_keys(patient),
            name_keys=self._name_keys(patient.names),
            birth_date=patient.birth_date.isoformat() if patient.birth_date is not None else None,
            phones=self._phone_keys(patient),
            emails=self._email_keys(patient),
            postal_codes=self._postal_keys(patient),
        )

    @staticmethod
    def _identifier_keys(patient: Patient) -> tuple[str, ...]:
        keys: list[str] = []
        for identifier in (*patient.identifiers, *patient.account_identifiers):
            key = PatientIdentityNormalizer.identifier_key(identifier)
            if key is not None:
                keys.append(key)
        return tuple(dict.fromkeys(keys))

    @staticmethod
    def identifier_key(identifier: Identifier) -> str | None:
        namespace = identifier.system or identifier.assigner
        if namespace is None:
            return None
        # Identifier values remain case-sensitive to avoid unsafe coalescing.
        value = _nfkc(identifier.value)
        namespace_value = _nfkc(namespace)
        type_code = _nfkc(identifier.type_code) if identifier.type_code is not None else ""
        return f"{namespace_value}\x1f{type_code}\x1f{value}"

    @staticmethod
    def _name_keys(names: tuple[HumanName, ...]) -> tuple[str, ...]:
        keys: list[str] = []
        for name in names:
            parts = [*name.given, name.family or ""]
            normalized = " ".join(part for part in (_fold(item) for item in parts) if part)
            if normalized:
                keys.append(normalized)
        return tuple(dict.fromkeys(keys))

    @staticmethod
    def _phone_keys(patient: Patient) -> tuple[str, ...]:
        values: list[str] = []
        for contact in patient.telecom:
            if contact.system is not ContactPointSystem.PHONE:
                continue
            digits = _NON_DIGIT.sub("", _nfkc(contact.value))
            # Do not infer a country code. Very short values are too collision-prone.
            if len(digits) >= 7:
                values.append(digits)
        return tuple(dict.fromkeys(values))

    @staticmethod
    def _email_keys(patient: Patient) -> tuple[str, ...]:
        values = [
            _fold(contact.value)
            for contact in patient.telecom
            if contact.system is ContactPointSystem.EMAIL
        ]
        return tuple(dict.fromkeys(value for value in values if value))

    @staticmethod
    def _postal_keys(patient: Patient) -> tuple[str, ...]:
        values = [
            _fold(address.postal_code)
            for address in patient.addresses
            if address.postal_code is not None
        ]
        return tuple(dict.fromkeys(value for value in values if value))
