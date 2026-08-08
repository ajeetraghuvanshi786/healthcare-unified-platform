"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.orders.obr_parser import OBRParser

__all__ = [
    "OBRParser",
]
