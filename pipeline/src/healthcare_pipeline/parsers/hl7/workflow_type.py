from __future__ import annotations

from enum import StrEnum


class HL7WorkflowType(StrEnum):
    """High-level workflow classification derived from MSH-9 message code."""

    ADT = "adt"
    CLINICAL_ORDER = "clinical_order"
    OBSERVATION_RESULT = "observation_result"
    PHARMACY_ORDER = "pharmacy_order"
    MEDICATION_ADMINISTRATION = "medication_administration"
    GENERIC = "generic"

    @classmethod
    def from_message_code(cls, message_code: str) -> HL7WorkflowType:
        """Map an HL7 message code to the supported workflow family."""

        if not isinstance(message_code, str):
            raise TypeError("message_code must be a string")
        normalized = message_code.strip().upper()
        if not normalized:
            raise ValueError("message_code must not be blank")

        if normalized == "ADT":
            return cls.ADT
        if normalized in {"ORM", "OMG", "OML"}:
            return cls.CLINICAL_ORDER
        if normalized == "ORU":
            return cls.OBSERVATION_RESULT
        if normalized in {"RDE", "RDS"}:
            return cls.PHARMACY_ORDER
        if normalized in {"RAS", "RGV", "VXU"}:
            return cls.MEDICATION_ADMINISTRATION
        return cls.GENERIC
