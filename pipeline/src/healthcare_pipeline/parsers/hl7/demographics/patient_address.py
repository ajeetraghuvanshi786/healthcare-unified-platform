from __future__ import annotations

from dataclasses import dataclass


def _normalize_address_part(value: str | None, field_name: str) -> str | None:
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
class PatientAddress:
    """A patient address from PID-11 using the HL7 XAD data type."""

    street_address: str | None = None
    other_designation: str | None = None
    city: str | None = None
    state_or_province: str | None = None
    postal_code: str | None = None
    country: str | None = None
    address_type: str | None = None
    county: str | None = None
    census_tract: str | None = None

    def __post_init__(self) -> None:
        fields = (
            "street_address",
            "other_designation",
            "city",
            "state_or_province",
            "postal_code",
            "country",
            "address_type",
            "county",
            "census_tract",
        )
        for field_name in fields:
            object.__setattr__(
                self,
                field_name,
                _normalize_address_part(getattr(self, field_name), field_name),
            )

        if all(getattr(self, field_name) is None for field_name in fields):
            raise ValueError("patient address must contain at least one value")

    @property
    def single_line(self) -> str:
        """Return a readable address without asserting postal deliverability."""

        locality = ", ".join(
            part
            for part in (self.city, self.state_or_province, self.postal_code)
            if part is not None
        )
        parts = (
            self.street_address,
            self.other_designation,
            locality or None,
            self.country,
        )
        return ", ".join(part for part in parts if part is not None)
