"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.orders.orc_parser import ORCParser

__all__ = [
    "ORCParser",
]
