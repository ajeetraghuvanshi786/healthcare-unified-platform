from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.mapping.clinical_semantic import (
    parse_coded_repetitions,
    parse_optional_coded_field,
    parse_order_identifier,
    parse_providers,
)
from healthcare_pipeline.parsers.hl7.mapping.semantic import (
    field,
    field_value,
    parse_hl7_datetime,
    parse_positive_integer,
)
from healthcare_pipeline.parsers.hl7.orders.observation_request import ObservationRequest


class OBRParser:
    """Convert repeatable OBR segments into immutable ObservationRequest values."""

    def parse_message(self, message: HL7Message) -> tuple[ObservationRequest, ...]:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        return tuple(self.parse_segment(segment) for segment in message.segments_named("OBR"))

    def parse_segment(self, segment: HL7Segment) -> ObservationRequest:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "OBR":
            raise InvalidMessageError("OBR parser requires an OBR segment")
        try:
            set_id = parse_positive_integer(field_value(segment, 1), "OBR-1 set ID")
            if set_id is None:
                raise ValueError("OBR-1 set ID is required")
            service = parse_optional_coded_field(
                field(segment, 4), "OBR-4 universal service identifier"
            )
            if service is None:
                raise ValueError("OBR-4 universal service identifier is required")
            return ObservationRequest(
                set_id=set_id,
                placer_order_number=parse_order_identifier(
                    field(segment, 2), "OBR-2 placer order number"
                ),
                filler_order_number=parse_order_identifier(
                    field(segment, 3), "OBR-3 filler order number"
                ),
                universal_service_identifier=service,
                requested_datetime=parse_hl7_datetime(
                    field_value(segment, 6), "OBR-6 requested date/time"
                ),
                observation_datetime=parse_hl7_datetime(
                    field_value(segment, 7), "OBR-7 observation date/time"
                ),
                observation_end_datetime=parse_hl7_datetime(
                    field_value(segment, 8), "OBR-8 observation end date/time"
                ),
                collector_identifiers=parse_providers(field(segment, 10)),
                relevant_clinical_information=field_value(segment, 13),
                specimen_received_datetime=parse_hl7_datetime(
                    field_value(segment, 14), "OBR-14 specimen received date/time"
                ),
                specimen_source=parse_optional_coded_field(
                    field(segment, 15), "OBR-15 specimen source"
                ),
                ordering_providers=parse_providers(field(segment, 16)),
                placer_field_1=field_value(segment, 18),
                placer_field_2=field_value(segment, 19),
                filler_field_1=field_value(segment, 20),
                filler_field_2=field_value(segment, 21),
                result_status_change_datetime=parse_hl7_datetime(
                    field_value(segment, 22), "OBR-22 result status change date/time"
                ),
                diagnostic_service_section=field_value(segment, 24),
                result_status=field_value(segment, 25),
                quantity_timing=field_value(segment, 27),
                result_copy_providers=parse_providers(field(segment, 28)),
                reasons_for_study=parse_coded_repetitions(
                    field(segment, 31), "OBR-31 reason for study"
                ),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid OBR segment: {exc}") from exc
