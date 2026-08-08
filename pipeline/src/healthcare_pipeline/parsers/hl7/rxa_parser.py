"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.pharmacy.rxa_parser import RXAParser

__all__ = [
    "RXAParser",
]
