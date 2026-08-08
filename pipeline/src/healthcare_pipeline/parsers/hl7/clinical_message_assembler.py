"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.workflow.clinical_message_assembler import (
    HL7ClinicalMessageAssembler,
)

__all__ = [
    "HL7ClinicalMessageAssembler",
]
