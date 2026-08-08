"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.message_header.header import HL7MessageHeader

__all__ = [
    "HL7MessageHeader",
]
