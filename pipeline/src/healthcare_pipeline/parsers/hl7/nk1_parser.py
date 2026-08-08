"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.demographics.nk1_parser import NK1Parser

__all__ = [
    "NK1Parser",
]
