"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.core.decoder import HL7PayloadDecoder

__all__ = [
    "HL7PayloadDecoder",
]
