from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.core.field import HL7Field
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.datatypes.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.mapping.clinical_semantic import (
    parse_coded_repetitions,
    parse_location,
    parse_optional_coded_field,
    parse_order_identifier,
    parse_providers,
)
from healthcare_pipeline.parsers.hl7.mapping.semantic import (
    field,
    field_value,
    parse_address,
    parse_hl7_datetime,
    parse_phone,
)
from healthcare_pipeline.parsers.hl7.orders.common_order import CommonOrder


class ORCParser:
    """Convert repeatable ORC segments into immutable CommonOrder values."""

    def parse_message(self, message: HL7Message) -> tuple[CommonOrder, ...]:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        return tuple(self.parse_segment(segment) for segment in message.segments_named("ORC"))

    def parse_segment(self, segment: HL7Segment) -> CommonOrder:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "ORC":
            raise InvalidMessageError("ORC parser requires an ORC segment")
        try:
            order_control = field_value(segment, 1)
            if order_control is None:
                raise ValueError("ORC-1 order control is required")
            address_field = field(segment, 22)
            phone_field = field(segment, 23)
            return CommonOrder(
                order_control=order_control,
                placer_order_number=parse_order_identifier(
                    field(segment, 2), "ORC-2 placer order number"
                ),
                filler_order_number=parse_order_identifier(
                    field(segment, 3), "ORC-3 filler order number"
                ),
                placer_group_number=parse_order_identifier(
                    field(segment, 4), "ORC-4 placer group number"
                ),
                order_status=field_value(segment, 5),
                quantity_timing=field_value(segment, 7),
                transaction_datetime=parse_hl7_datetime(
                    field_value(segment, 9), "ORC-9 transaction date/time"
                ),
                entered_by=parse_providers(field(segment, 10)),
                ordering_providers=parse_providers(field(segment, 12)),
                enterer_location=parse_location(field(segment, 13)),
                effective_datetime=parse_hl7_datetime(
                    field_value(segment, 15), "ORC-15 effective date/time"
                ),
                order_control_reason=parse_optional_coded_field(
                    field(segment, 16), "ORC-16 order control reason"
                ),
                entering_organization=parse_optional_coded_field(
                    field(segment, 17), "ORC-17 entering organization"
                ),
                ordering_facility_name=field_value(segment, 21),
                ordering_facility_addresses=(
                    tuple(
                        parse_address(repetition)
                        for repetition in address_field.repetitions
                        if repetition.raw_value.strip()
                    )
                    if address_field is not None
                    else ()
                ),
                ordering_facility_phones=(
                    tuple(
                        parse_phone(repetition)
                        for repetition in phone_field.repetitions
                        if repetition.raw_value.strip()
                    )
                    if phone_field is not None
                    else ()
                ),
                order_type=self._first_coded_value(field(segment, 29)),
            )
        except (IndexError, TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid ORC segment: {exc}") from exc

    @staticmethod
    def _first_coded_value(value: HL7Field | None) -> CodedValue | None:
        values = parse_coded_repetitions(value, "ORC-29 order type")
        return values[0] if values else None
