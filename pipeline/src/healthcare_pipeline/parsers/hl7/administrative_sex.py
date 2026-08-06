from __future__ import annotations

from enum import StrEnum


class AdministrativeSex(StrEnum):
    """HL7 Table 0001 administrative sex codes used by PID-8."""

    AMBIGUOUS = "A"
    FEMALE = "F"
    MALE = "M"
    NOT_APPLICABLE = "N"
    OTHER = "O"
    UNKNOWN = "U"

    @classmethod
    def from_code(cls, code: str | None) -> AdministrativeSex:
        """Return a validated administrative-sex value.

        Empty PID-8 values are represented as ``UNKNOWN`` so downstream code
        does not need to mix ``None`` with the standard HL7 unknown code.
        """

        if code is None:
            return cls.UNKNOWN
        if not isinstance(code, str):
            raise TypeError("administrative sex code must be a string or None")

        normalized = code.strip().upper()
        if not normalized:
            return cls.UNKNOWN

        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(
                f"unsupported HL7 administrative sex code: {normalized}"
            ) from exc
