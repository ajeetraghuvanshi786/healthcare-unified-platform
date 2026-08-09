from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.canonical.common._validation import normalize_optional


@dataclass(frozen=True, slots=True)
class Location:
    """Source-neutral care location hierarchy."""

    facility: str | None = None
    building: str | None = None
    floor: str | None = None
    point_of_care: str | None = None
    room: str | None = None
    bed: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        fields = (
            "facility",
            "building",
            "floor",
            "point_of_care",
            "room",
            "bed",
            "description",
        )
        for field_name in fields:
            object.__setattr__(
                self,
                field_name,
                normalize_optional(getattr(self, field_name), field_name),
            )
        if all(getattr(self, field_name) is None for field_name in fields):
            raise ValueError("location must contain at least one value")
