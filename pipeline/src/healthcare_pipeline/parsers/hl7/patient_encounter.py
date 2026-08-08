"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.encounters.patient_encounter import PatientEncounter

__all__ = [
    "PatientEncounter",
]
