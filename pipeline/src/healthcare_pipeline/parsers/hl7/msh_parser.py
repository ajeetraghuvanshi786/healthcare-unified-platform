"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.message_header.msh_parser import MSHParser

__all__ = [
    "MSHParser",
]
