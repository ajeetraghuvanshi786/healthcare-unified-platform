from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.orders.common_order import CommonOrder
from healthcare_pipeline.parsers.hl7.pharmacy.medication_administration import (
    MedicationAdministration,
)
from healthcare_pipeline.parsers.hl7.pharmacy.pharmacy_encoded_order import PharmacyEncodedOrder
from healthcare_pipeline.parsers.hl7.pharmacy.pharmacy_route import PharmacyRoute


@dataclass(frozen=True, slots=True)
class MedicationOrderGroup:
    """One medication workflow group assembled from ORC/RXE/RXR/RXA segments."""

    encoded_order: PharmacyEncodedOrder | None = None
    administrations: tuple[MedicationAdministration, ...] = ()
    routes: tuple[PharmacyRoute, ...] = ()
    common_order: CommonOrder | None = None
    source_segment_sequences: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if self.common_order is not None and not isinstance(self.common_order, CommonOrder):
            raise TypeError("common_order must be a CommonOrder or None")
        if self.encoded_order is not None and not isinstance(
            self.encoded_order, PharmacyEncodedOrder
        ):
            raise TypeError("encoded_order must be a PharmacyEncodedOrder or None")

        administrations = tuple(self.administrations)
        if not all(isinstance(value, MedicationAdministration) for value in administrations):
            raise TypeError(
                "administrations must contain only MedicationAdministration values"
            )
        object.__setattr__(self, "administrations", administrations)

        routes = tuple(self.routes)
        if not all(isinstance(value, PharmacyRoute) for value in routes):
            raise TypeError("routes must contain only PharmacyRoute values")
        object.__setattr__(self, "routes", routes)

        if self.encoded_order is None and not administrations:
            raise ValueError(
                "medication group requires an encoded order or an administration"
            )

        sequences = tuple(self.source_segment_sequences)
        if not sequences:
            raise ValueError("source_segment_sequences must not be empty")
        if any(not isinstance(value, int) or value < 1 for value in sequences):
            raise ValueError("source_segment_sequences must contain positive integers")
        if sequences != tuple(sorted(set(sequences))):
            raise ValueError("source_segment_sequences must be unique and increasing")
        object.__setattr__(self, "source_segment_sequences", sequences)
