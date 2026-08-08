"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.core.normalizer import HL7MessageNormalizer

__all__ = [
    "HL7MessageNormalizer",
]
