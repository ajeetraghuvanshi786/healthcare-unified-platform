from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.mapping.clinical_semantic import (
    parse_coded_repetitions,
    parse_optional_coded_field,
    parse_providers,
)
from healthcare_pipeline.parsers.hl7.mapping.semantic import (
    field,
    field_value,
    parse_hl7_datetime,
    parse_positive_integer,
)
from healthcare_pipeline.parsers.hl7.orders.observation_result import ObservationResult


class OBXParser:
    """Convert repeatable OBX segments into immutable ObservationResult values."""

    def parse_message(self, message: HL7Message) -> tuple[ObservationResult, ...]:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        return tuple(self.parse_segment(segment) for segment in message.segments_named("OBX"))

    def parse_segment(self, segment: HL7Segment) -> ObservationResult:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "OBX":
            raise InvalidMessageError("OBX parser requires an OBX segment")
        try:
            set_id = parse_positive_integer(field_value(segment, 1), "OBX-1 set ID")
            if set_id is None:
                raise ValueError("OBX-1 set ID is required")
            value_type = field_value(segment, 2)
            if value_type is None:
                raise ValueError("OBX-2 value type is required")
            identifier = parse_optional_coded_field(
                field(segment, 3), "OBX-3 observation identifier"
            )
            if identifier is None:
                raise ValueError("OBX-3 observation identifier is required")
            value_field = field(segment, 5)
            values = (
                tuple(
                    repetition.raw_value
                    for repetition in value_field.repetitions
                    if repetition.raw_value.strip()
                )
                if value_field is not None
                else ()
            )
            status = field_value(segment, 11)
            if status is None:
                raise ValueError("OBX-11 result status is required")
            abnormal_field = field(segment, 8)
            equipment_field = field(segment, 18)
            return ObservationResult(
                set_id=set_id,
                value_type=value_type,
                observation_identifier=identifier,
                observation_sub_id=field_value(segment, 4),
                values=values,
                units=parse_optional_coded_field(field(segment, 6), "OBX-6 units"),
                reference_range=field_value(segment, 7),
                abnormal_flags=(
                    tuple(
                        repetition.raw_value.strip()
                        for repetition in abnormal_field.repetitions
                        if repetition.raw_value.strip()
                    )
                    if abnormal_field is not None
                    else ()
                ),
                result_status=status,
                observation_datetime=parse_hl7_datetime(
                    field_value(segment, 14), "OBX-14 observation date/time"
                ),
                producer_identifier=parse_optional_coded_field(
                    field(segment, 15), "OBX-15 producer identifier"
                ),
                responsible_observers=parse_providers(field(segment, 16)),
                observation_method=parse_coded_repetitions(
                    field(segment, 17), "OBX-17 observation method"
                ),
                equipment_instance_identifiers=(
                    tuple(
                        repetition.raw_value.strip()
                        for repetition in equipment_field.repetitions
                        if repetition.raw_value.strip()
                    )
                    if equipment_field is not None
                    else ()
                ),
                analysis_datetime=parse_hl7_datetime(
                    field_value(segment, 19), "OBX-19 analysis date/time"
                ),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid OBX segment: {exc}") from exc
