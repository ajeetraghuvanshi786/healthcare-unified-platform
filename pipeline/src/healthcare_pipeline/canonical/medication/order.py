from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from healthcare_pipeline.canonical.clinical.provider import Provider
from healthcare_pipeline.canonical.common._validation import ensure_non_negative, normalize_optional
from healthcare_pipeline.canonical.common.coding import Coding
from healthcare_pipeline.canonical.common.identifier import Identifier
from healthcare_pipeline.canonical.common.quantity import Quantity
from healthcare_pipeline.canonical.medication.route import MedicationRoute


@dataclass(frozen=True, slots=True)
class MedicationOrder:
    """Canonical prescribed/encoded medication order."""

    medication: Coding
    identifiers: tuple[Identifier, ...] = ()
    dose_minimum: Quantity | None = None
    dose_maximum: Quantity | None = None
    dispense_quantity: Quantity | None = None
    number_of_refills: int | None = None
    ordering_providers: tuple[Provider, ...] = ()
    routes: tuple[MedicationRoute, ...] = ()
    status: str | None = None
    instructions: tuple[Coding, ...] = ()
    strength: Decimal | None = None
    strength_unit: Coding | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.medication, Coding):
            raise TypeError("medication must be a Coding")
        for field_name, expected_type in (
            ("identifiers", Identifier),
            ("ordering_providers", Provider),
            ("routes", MedicationRoute),
            ("instructions", Coding),
        ):
            values = tuple(getattr(self, field_name))
            if not all(isinstance(value, expected_type) for value in values):
                raise TypeError(f"{field_name} contains an invalid value")
            object.__setattr__(self, field_name, values)
        if self.number_of_refills is not None and self.number_of_refills < 0:
            raise ValueError("number_of_refills must not be negative")
        ensure_non_negative(self.strength, "strength")
        object.__setattr__(self, "status", normalize_optional(self.status, "status"))
