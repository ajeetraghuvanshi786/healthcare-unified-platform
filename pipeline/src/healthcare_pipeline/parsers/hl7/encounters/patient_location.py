from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.mapping.semantic import normalize_optional


@dataclass(frozen=True, slots=True)
class PatientLocation:
    """Patient location represented by the HL7 PL datatype."""

    point_of_care: str | None = None
    room: str | None = None
    bed: str | None = None
    facility: str | None = None
    location_status: str | None = None
    person_location_type: str | None = None
    building: str | None = None
    floor: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        fields = (
            "point_of_care",
            "room",
            "bed",
            "facility",
            "location_status",
            "person_location_type",
            "building",
            "floor",
            "description",
        )
        for field_name in fields:
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        if all(getattr(self, field_name) is None for field_name in fields):
            raise ValueError("patient location must contain at least one value")

    @property
    def location_key(self) -> tuple[str | None, ...]:
        return tuple(
            value.casefold() if value is not None else None
            for value in (
                self.facility,
                self.building,
                self.floor,
                self.point_of_care,
                self.room,
                self.bed,
            )
        )
