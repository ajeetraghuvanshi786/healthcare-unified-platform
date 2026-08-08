from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.mapping.clinical_semantic import (
    parse_coded_repetitions,
    parse_decimal,
    parse_location,
    parse_optional_coded_field,
    parse_providers,
)
from healthcare_pipeline.parsers.hl7.mapping.semantic import (
    field,
    field_value,
    parse_hl7_date,
    parse_hl7_datetime,
)
from healthcare_pipeline.parsers.hl7.pharmacy.medication_administration import (
    MedicationAdministration,
)


class RXAParser:
    """Convert repeatable RXA segments into medication-administration values."""

    def parse_message(self, message: HL7Message) -> tuple[MedicationAdministration, ...]:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        return tuple(self.parse_segment(segment) for segment in message.segments_named("RXA"))

    def parse_segment(self, segment: HL7Segment) -> MedicationAdministration:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "RXA":
            raise InvalidMessageError("RXA parser requires an RXA segment")
        try:
            give_sub_id = self._required_non_negative_integer(
                field_value(segment, 1), "RXA-1 give sub-ID"
            )
            administration_sub_id = self._required_non_negative_integer(
                field_value(segment, 2), "RXA-2 administration sub-ID"
            )
            start_datetime = parse_hl7_datetime(
                field_value(segment, 3), "RXA-3 administration start date/time"
            )
            if start_datetime is None:
                raise ValueError("RXA-3 administration start date/time is required")
            administered_code = parse_optional_coded_field(
                field(segment, 5), "RXA-5 administered code"
            )
            if administered_code is None:
                raise ValueError("RXA-5 administered code is required")
            amount = parse_decimal(
                field_value(segment, 6), "RXA-6 administered amount", required=True
            )
            if amount is None:
                raise ValueError("RXA-6 administered amount is required")
            return MedicationAdministration(
                give_sub_id=give_sub_id,
                administration_sub_id=administration_sub_id,
                start_datetime=start_datetime,
                end_datetime=parse_hl7_datetime(
                    field_value(segment, 4), "RXA-4 administration end date/time"
                ),
                administered_code=administered_code,
                administered_amount=amount,
                administered_units=parse_optional_coded_field(
                    field(segment, 7), "RXA-7 administered units"
                ),
                administration_notes=parse_coded_repetitions(
                    field(segment, 9), "RXA-9 administration note"
                ),
                administering_providers=parse_providers(field(segment, 10)),
                administered_at_location=parse_location(field(segment, 11)),
                lot_number=field_value(segment, 15),
                expiration_date=parse_hl7_date(
                    field_value(segment, 16), "RXA-16 expiration date"
                ),
                manufacturer=parse_optional_coded_field(
                    field(segment, 17), "RXA-17 manufacturer"
                ),
                refusal_reason=parse_optional_coded_field(
                    field(segment, 18), "RXA-18 refusal reason"
                ),
                indication=parse_optional_coded_field(
                    field(segment, 19), "RXA-19 indication"
                ),
                completion_status=field_value(segment, 20),
                action_code=field_value(segment, 21),
                system_entry_datetime=parse_hl7_datetime(
                    field_value(segment, 22), "RXA-22 system entry date/time"
                ),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid RXA segment: {exc}") from exc

    @staticmethod
    def _required_non_negative_integer(value: str | None, field_label: str) -> int:
        if value is None:
            raise ValueError(f"{field_label} is required")
        try:
            parsed = int(value)
        except ValueError as exc:
            raise ValueError(f"{field_label} must be an integer") from exc
        if parsed < 0:
            raise ValueError(f"{field_label} must not be negative")
        return parsed
