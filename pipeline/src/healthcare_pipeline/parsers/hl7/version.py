"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.message_header.version import HL7Version

__all__ = [
    "HL7Version",
]
