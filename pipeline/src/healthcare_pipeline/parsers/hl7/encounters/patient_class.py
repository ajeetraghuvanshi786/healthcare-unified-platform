from __future__ import annotations

from enum import StrEnum


class PatientClass(StrEnum):
    """Administrative patient class from PV1-2."""

    OBSTETRICS = "B"
    COMMERCIAL_ACCOUNT = "C"
    EMERGENCY = "E"
    INPATIENT = "I"
    NOT_APPLICABLE = "N"
    OUTPATIENT = "O"
    PREADMIT = "P"
    RECURRING = "R"
    UNKNOWN = "U"

    @classmethod
    def from_code(cls, value: str | None) -> PatientClass:
        if value is None or not value.strip():
            return cls.UNKNOWN
        if not isinstance(value, str):
            raise TypeError("patient class code must be a string or None")
        normalized = value.strip().upper()
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"unsupported patient class code: {value!r}") from exc
