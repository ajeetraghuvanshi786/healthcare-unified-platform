"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.encounters.pv1_parser import PV1Parser

__all__ = [
    "PV1Parser",
]
