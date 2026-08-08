from __future__ import annotations

from dataclasses import dataclass


def _normalize_name_part(value: str | None, field_name: str) -> str | None:
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
class PatientName:
    """A patient name from PID-5 using the HL7 XPN data type."""

    family_name: str | None = None
    given_name: str | None = None
    middle_name: str | None = None
    suffix: str | None = None
    prefix: str | None = None
    degree: str | None = None
    name_type: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "family_name",
            "given_name",
            "middle_name",
            "suffix",
            "prefix",
            "degree",
            "name_type",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_name_part(getattr(self, field_name), field_name),
            )

        if self.family_name is None and self.given_name is None:
            raise ValueError(
                "patient name must include a family name or given name"
            )

    @property
    def display_name(self) -> str:
        """Human-readable name without changing the stored components."""

        parts = (
            self.prefix,
            self.given_name,
            self.middle_name,
            self.family_name,
            self.suffix,
            self.degree,
        )
        return " ".join(part for part in parts if part is not None)
