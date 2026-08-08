"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.clinical.dg1_parser import DG1Parser

__all__ = [
    "DG1Parser",
]
