"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.pharmacy.rxe_parser import RXEParser

__all__ = [
    "RXEParser",
]
