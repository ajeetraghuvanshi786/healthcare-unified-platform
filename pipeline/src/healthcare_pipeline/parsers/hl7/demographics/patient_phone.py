from __future__ import annotations

from dataclasses import dataclass


def _normalize_phone_part(value: str | None, field_name: str) -> str | None:
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
class PatientPhone:
    """A telecom value from PID-13/PID-14 using the HL7 XTN data type."""

    number: str | None = None
    use_code: str | None = None
    equipment_type: str | None = None
    email: str | None = None
    country_code: str | None = None
    area_code: str | None = None
    local_number: str | None = None
    extension: str | None = None

    def __post_init__(self) -> None:
        fields = (
            "number",
            "use_code",
            "equipment_type",
            "email",
            "country_code",
            "area_code",
            "local_number",
            "extension",
        )
        for field_name in fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_phone_part(getattr(self, field_name), field_name),
            )

        if self.number is None and self.email is None and self.local_number is None:
            raise ValueError(
                "patient phone must contain a number, local number, or email"
            )

    @property
    def dialable_number(self) -> str | None:
        """Return the best available unformatted dialable representation."""

        if self.number is not None:
            return self.number
        if self.local_number is None:
            return None
        return "".join(
            part
            for part in (self.country_code, self.area_code, self.local_number)
            if part is not None
        )
