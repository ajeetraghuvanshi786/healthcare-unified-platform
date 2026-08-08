"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.financial.in1_parser import IN1Parser

__all__ = [
    "IN1Parser",
]
