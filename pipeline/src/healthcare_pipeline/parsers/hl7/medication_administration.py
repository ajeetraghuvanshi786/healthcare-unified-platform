"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.pharmacy.medication_administration import (
    MedicationAdministration,
)

__all__ = [
    "MedicationAdministration",
]
