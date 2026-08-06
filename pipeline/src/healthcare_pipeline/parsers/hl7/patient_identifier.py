from __future__ import annotations

from dataclasses import dataclass


def _normalize_required(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{field_name} must not contain control characters")
    return normalized


def _normalize_optional(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    normalized = value.strip()
    if not normalized:
        return None
    if any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{field_name} must not contain control characters")
    return normalized


@dataclass(frozen=True, slots=True)
class PatientIdentifier:
    """A patient identifier from HL7 PID-3 (CX data type).

    ``value`` identifies the patient inside a namespace. ``assigning_authority``
    identifies that namespace. An identifier may be accepted without an
    assigning authority because legacy interfaces sometimes omit it, but such
    identifiers must not be treated as globally unique by matching services.
    """

    value: str
    assigning_authority: str | None = None
    identifier_type: str | None = None
    assigning_facility: str | None = None
    check_digit: str | None = None
    check_digit_scheme: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalize_required(self.value, "value"),
        )
        for field_name in (
            "assigning_authority",
            "identifier_type",
            "assigning_facility",
            "check_digit",
            "check_digit_scheme",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional(getattr(self, field_name), field_name),
            )

    @property
    def is_scoped(self) -> bool:
        """Whether the identifier has an explicit assigning namespace."""

        return self.assigning_authority is not None

    @property
    def identity_key(self) -> tuple[str | None, str, str | None]:
        """Stable key suitable for deduplication inside a tenant."""

        authority = (
            self.assigning_authority.casefold()
            if self.assigning_authority is not None
            else None
        )
        identifier_type = (
            self.identifier_type.upper()
            if self.identifier_type is not None
            else None
        )
        return authority, self.value, identifier_type
