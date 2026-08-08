"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.core.field import HL7Field, HL7Repetition

__all__ = [
    "HL7Repetition",
    "HL7Field",
]
