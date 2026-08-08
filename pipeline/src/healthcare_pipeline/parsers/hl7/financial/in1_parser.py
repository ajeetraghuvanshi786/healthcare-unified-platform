from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.core.field import HL7Field
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.datatypes.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.demographics.patient_address import PatientAddress
from healthcare_pipeline.parsers.hl7.demographics.patient_identifier import PatientIdentifier
from healthcare_pipeline.parsers.hl7.demographics.patient_name import PatientName
from healthcare_pipeline.parsers.hl7.demographics.patient_phone import PatientPhone
from healthcare_pipeline.parsers.hl7.financial.insurance_coverage import InsuranceCoverage
from healthcare_pipeline.parsers.hl7.mapping.semantic import (
    component_value,
    field,
    field_value,
    parse_address,
    parse_hl7_date,
    parse_identifier,
    parse_name,
    parse_phone,
    parse_positive_integer,
)


class IN1Parser:
    """Convert HL7 IN1 segments into immutable InsuranceCoverage values."""

    def parse_message(self, message: HL7Message) -> tuple[InsuranceCoverage, ...]:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        return tuple(self.parse_segment(segment) for segment in message.segments_named("IN1"))

    def parse_segment(self, segment: HL7Segment) -> InsuranceCoverage:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "IN1":
            raise InvalidMessageError("IN1 parser requires an IN1 segment")
        try:
            set_id = parse_positive_integer(field_value(segment, 1), "IN1-1 set ID")
            if set_id is None:
                raise ValueError("IN1-1 set ID is required")
            return InsuranceCoverage(
                set_id=set_id,
                plan_identifier=self._parse_code(field(segment, 2)),
                company_identifiers=self._parse_identifiers(field(segment, 3), "IN1-3"),
                company_name=self._organization_name(field(segment, 4)),
                company_addresses=self._parse_addresses(field(segment, 5)),
                contact_names=self._parse_names(field(segment, 6)),
                contact_phones=self._parse_phones(field(segment, 7)),
                group_number=field_value(segment, 8),
                group_name=field_value(segment, 9),
                effective_date=parse_hl7_date(field_value(segment, 12), "IN1-12 effective date"),
                expiration_date=parse_hl7_date(field_value(segment, 13), "IN1-13 expiration date"),
                plan_type=field_value(segment, 15),
                insured_names=self._parse_names(field(segment, 16)),
                insured_relationship=self._parse_code(field(segment, 17)),
                insured_birth_date=parse_hl7_date(
                    field_value(segment, 18),
                    "IN1-18 insured birth date",
                ),
                insured_addresses=self._parse_addresses(field(segment, 19)),
                policy_number=field_value(segment, 36),
                insured_identifiers=self._parse_identifiers(field(segment, 49), "IN1-49"),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid IN1 segment: {exc}") from exc

    @staticmethod
    def _parse_identifiers(
        value: HL7Field | None,
        label: str,
    ) -> tuple[PatientIdentifier, ...]:
        if value is None:
            return ()
        return tuple(
            parse_identifier(repetition, label)
            for repetition in value.repetitions
            if repetition.raw_value.strip()
        )

    @staticmethod
    def _parse_names(value: HL7Field | None) -> tuple[PatientName, ...]:
        if value is None:
            return ()
        return tuple(
            parse_name(repetition)
            for repetition in value.repetitions
            if repetition.raw_value.strip()
        )

    @staticmethod
    def _parse_addresses(value: HL7Field | None) -> tuple[PatientAddress, ...]:
        if value is None:
            return ()
        return tuple(
            parse_address(repetition)
            for repetition in value.repetitions
            if repetition.raw_value.strip()
        )

    @staticmethod
    def _parse_phones(value: HL7Field | None) -> tuple[PatientPhone, ...]:
        if value is None:
            return ()
        return tuple(
            parse_phone(repetition)
            for repetition in value.repetitions
            if repetition.raw_value.strip()
        )

    @classmethod
    def _parse_code(cls, value: HL7Field | None) -> CodedValue | None:
        if value is None or not value.value.strip():
            return None
        repetition = value.repetition(1)
        return CodedValue(
            identifier=component_value(repetition, 1),
            text=component_value(repetition, 2),
            coding_system=component_value(repetition, 3),
            alternate_identifier=component_value(repetition, 4),
            alternate_text=component_value(repetition, 5),
            alternate_coding_system=component_value(repetition, 6),
        )

    @staticmethod
    def _organization_name(value: HL7Field | None) -> str | None:
        if value is None or not value.value.strip():
            return None
        return component_value(value.repetition(1), 1)
