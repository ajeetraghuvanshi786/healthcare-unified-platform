from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.clinical_semantic import (
    parse_coded_repetitions,
    parse_decimal,
    parse_non_negative_integer,
    parse_optional_coded_field,
    parse_providers,
)
from healthcare_pipeline.parsers.hl7.message import HL7Message
from healthcare_pipeline.parsers.hl7.pharmacy_encoded_order import PharmacyEncodedOrder
from healthcare_pipeline.parsers.hl7.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.semantic import field, field_value


class RXEParser:
    """Convert repeatable RXE segments into pharmacy encoded orders."""

    def parse_message(self, message: HL7Message) -> tuple[PharmacyEncodedOrder, ...]:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        return tuple(self.parse_segment(segment) for segment in message.segments_named("RXE"))

    def parse_segment(self, segment: HL7Segment) -> PharmacyEncodedOrder:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "RXE":
            raise InvalidMessageError("RXE parser requires an RXE segment")
        try:
            give_code = parse_optional_coded_field(field(segment, 2), "RXE-2 give code")
            if give_code is None:
                raise ValueError("RXE-2 give code is required")
            return PharmacyEncodedOrder(
                quantity_timing=field_value(segment, 1),
                give_code=give_code,
                give_amount_minimum=parse_decimal(
                    field_value(segment, 3), "RXE-3 give amount minimum"
                ),
                give_amount_maximum=parse_decimal(
                    field_value(segment, 4), "RXE-4 give amount maximum"
                ),
                give_units=parse_optional_coded_field(field(segment, 5), "RXE-5 give units"),
                give_dosage_form=parse_optional_coded_field(
                    field(segment, 6), "RXE-6 give dosage form"
                ),
                provider_instructions=parse_coded_repetitions(
                    field(segment, 7), "RXE-7 provider instruction"
                ),
                dispense_amount=parse_decimal(
                    field_value(segment, 10), "RXE-10 dispense amount"
                ),
                dispense_units=parse_optional_coded_field(
                    field(segment, 11), "RXE-11 dispense units"
                ),
                number_of_refills=parse_non_negative_integer(
                    field_value(segment, 12), "RXE-12 number of refills"
                ),
                ordering_providers=parse_providers(field(segment, 13)),
                provider_dea_number=field_value(segment, 14),
                pharmacist_verification_identifier=field_value(segment, 15),
                pharmacy_treatment_supplier_instructions=parse_coded_repetitions(
                    field(segment, 21), "RXE-21 supplier instruction"
                ),
                give_rate_amount=parse_decimal(
                    field_value(segment, 23), "RXE-23 give rate amount"
                ),
                give_rate_units=parse_optional_coded_field(
                    field(segment, 24), "RXE-24 give rate units"
                ),
                give_strength=parse_decimal(field_value(segment, 25), "RXE-25 give strength"),
                give_strength_units=parse_optional_coded_field(
                    field(segment, 26), "RXE-26 give strength units"
                ),
                supplemental_codes=parse_coded_repetitions(
                    field(segment, 31), "RXE-31 supplemental code"
                ),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid RXE segment: {exc}") from exc
