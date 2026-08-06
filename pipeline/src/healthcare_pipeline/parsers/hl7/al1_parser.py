from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.allergy import Allergy
from healthcare_pipeline.parsers.hl7.clinical_semantic import parse_optional_coded_field
from healthcare_pipeline.parsers.hl7.message import HL7Message
from healthcare_pipeline.parsers.hl7.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.semantic import (
    field,
    field_value,
    parse_hl7_date,
    parse_positive_integer,
)


class AL1Parser:
    """Convert repeatable AL1 segments into immutable Allergy values."""

    def parse_message(self, message: HL7Message) -> tuple[Allergy, ...]:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        return tuple(self.parse_segment(segment) for segment in message.segments_named("AL1"))

    def parse_segment(self, segment: HL7Segment) -> Allergy:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "AL1":
            raise InvalidMessageError("AL1 parser requires an AL1 segment")
        try:
            set_id = parse_positive_integer(field_value(segment, 1), "AL1-1 set ID")
            if set_id is None:
                raise ValueError("AL1-1 set ID is required")
            allergen = parse_optional_coded_field(field(segment, 3), "AL1-3 allergen")
            if allergen is None:
                raise ValueError("AL1-3 allergen is required")
            reaction_field = field(segment, 5)
            reactions = (
                tuple(
                    repetition.raw_value.strip()
                    for repetition in reaction_field.repetitions
                    if repetition.raw_value.strip()
                )
                if reaction_field is not None
                else ()
            )
            return Allergy(
                set_id=set_id,
                allergy_type=parse_optional_coded_field(field(segment, 2), "AL1-2 allergy type"),
                allergen=allergen,
                severity=parse_optional_coded_field(field(segment, 4), "AL1-4 severity"),
                reactions=reactions,
                identification_date=parse_hl7_date(
                    field_value(segment, 6),
                    "AL1-6 identification date",
                ),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid AL1 segment: {exc}") from exc
