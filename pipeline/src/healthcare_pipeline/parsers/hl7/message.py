"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.core.message import HL7Message

__all__ = [
    "HL7Message",
]
