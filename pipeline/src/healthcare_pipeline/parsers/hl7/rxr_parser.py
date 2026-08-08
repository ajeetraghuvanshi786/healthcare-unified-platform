"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.pharmacy.rxr_parser import RXRParser

__all__ = [
    "RXRParser",
]
