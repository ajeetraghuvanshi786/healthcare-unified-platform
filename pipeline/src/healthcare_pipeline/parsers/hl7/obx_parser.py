"""Backward-compatible import facade for the modular HL7 package."""

from healthcare_pipeline.parsers.hl7.orders.obx_parser import OBXParser

__all__ = [
    "OBXParser",
]
