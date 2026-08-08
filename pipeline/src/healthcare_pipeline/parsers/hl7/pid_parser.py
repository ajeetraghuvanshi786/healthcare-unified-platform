"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.demographics.pid_parser import PIDParser

__all__ = [
    "PIDParser",
]
