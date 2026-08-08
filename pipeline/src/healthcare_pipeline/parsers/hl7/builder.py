"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.core.builder import HL7MessageBuilder

__all__ = [
    "HL7MessageBuilder",
]
