"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.clinical.al1_parser import AL1Parser

__all__ = [
    "AL1Parser",
]
