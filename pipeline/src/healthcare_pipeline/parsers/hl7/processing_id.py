"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.message_header.processing_id import (
    HL7ProcessingId,
    HL7ProcessingMode,
)

__all__ = [
    "HL7ProcessingMode",
    "HL7ProcessingId",
]
