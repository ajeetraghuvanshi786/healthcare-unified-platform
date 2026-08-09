from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from healthcare_pipeline.canonical.clinical.provider import Provider
from healthcare_pipeline.canonical.common._validation import ensure_aware, normalize_optional
from healthcare_pipeline.canonical.common.coding import Coding
from healthcare_pipeline.canonical.common.location import Location
from healthcare_pipeline.canonical.common.quantity import Quantity
from healthcare_pipeline.canonical.medication.route import MedicationRoute


@dataclass(frozen=True, slots=True)
class MedicationAdministration:
    """Canonical record of medication actually administered to a patient."""

    medication: Coding
    amount: Quantity
    start_datetime: datetime
    end_datetime: datetime | None = None
    routes: tuple[MedicationRoute, ...] = ()
    performers: tuple[Provider, ...] = ()
    location: Location | None = None
    lot_number: str | None = None
    expiration_date: date | None = None
    manufacturer: Coding | None = None
    refusal_reason: Coding | None = None
    indication: Coding | None = None
    status: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.medication, Coding):
            raise TypeError("medication must be a Coding")
        if not isinstance(self.amount, Quantity):
            raise TypeError("amount must be a Quantity")
        ensure_aware(self.start_datetime, "start_datetime")
        ensure_aware(self.end_datetime, "end_datetime")
        if self.end_datetime is not None and self.end_datetime < self.start_datetime:
            raise ValueError("end_datetime must not precede start_datetime")
        for field_name, expected_type in (("routes", MedicationRoute), ("performers", Provider)):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
        if self.location is not None and not isinstance(self.location, Location):
            raise TypeError("location must be a Location or None")
        object.__setattr__(
            self,
            "lot_number",
            normalize_optional(self.lot_number, "lot_number"),
        )
        object.__setattr__(self, "status", normalize_optional(self.status, "status"))
