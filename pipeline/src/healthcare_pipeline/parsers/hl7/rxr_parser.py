from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.clinical_semantic import parse_optional_coded_field
from healthcare_pipeline.parsers.hl7.message import HL7Message
from healthcare_pipeline.parsers.hl7.pharmacy_route import PharmacyRoute
from healthcare_pipeline.parsers.hl7.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.semantic import field


class RXRParser:
    """Convert repeatable RXR segments into immutable PharmacyRoute values."""

    def parse_message(self, message: HL7Message) -> tuple[PharmacyRoute, ...]:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        return tuple(self.parse_segment(segment) for segment in message.segments_named("RXR"))

    def parse_segment(self, segment: HL7Segment) -> PharmacyRoute:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "RXR":
            raise InvalidMessageError("RXR parser requires an RXR segment")
        try:
            route = parse_optional_coded_field(field(segment, 1), "RXR-1 route")
            if route is None:
                raise ValueError("RXR-1 route is required")
            return PharmacyRoute(
                route=route,
                administration_site=parse_optional_coded_field(
                    field(segment, 2), "RXR-2 administration site"
                ),
                administration_device=parse_optional_coded_field(
                    field(segment, 3), "RXR-3 administration device"
                ),
                administration_method=parse_optional_coded_field(
                    field(segment, 4), "RXR-4 administration method"
                ),
                routing_instruction=parse_optional_coded_field(
                    field(segment, 5), "RXR-5 routing instruction"
                ),
                administration_site_modifier=parse_optional_coded_field(
                    field(segment, 6), "RXR-6 administration site modifier"
                ),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid RXR segment: {exc}") from exc
