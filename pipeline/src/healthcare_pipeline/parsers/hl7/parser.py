"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.core.parser import HL7Parser

__all__ = [
    "HL7Parser",
]
