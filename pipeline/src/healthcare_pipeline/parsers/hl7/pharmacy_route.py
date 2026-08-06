from __future__ import annotations

from dataclasses import dataclass

from healthcare_pipeline.parsers.hl7.coded_value import CodedValue


@dataclass(frozen=True, slots=True)
class PharmacyRoute:
    """Immutable medication-route representation from RXR."""

    route: CodedValue
    administration_site: CodedValue | None = None
    administration_device: CodedValue | None = None
    administration_method: CodedValue | None = None
    routing_instruction: CodedValue | None = None
    administration_site_modifier: CodedValue | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.route, CodedValue):
            raise TypeError("route must be a CodedValue")
