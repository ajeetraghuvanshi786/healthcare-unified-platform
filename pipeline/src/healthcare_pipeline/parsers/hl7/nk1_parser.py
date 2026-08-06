from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.administrative_sex import AdministrativeSex
from healthcare_pipeline.parsers.hl7.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.field import HL7Field, HL7Repetition
from healthcare_pipeline.parsers.hl7.message import HL7Message
from healthcare_pipeline.parsers.hl7.next_of_kin import NextOfKin
from healthcare_pipeline.parsers.hl7.patient_address import PatientAddress
from healthcare_pipeline.parsers.hl7.patient_name import PatientName
from healthcare_pipeline.parsers.hl7.patient_phone import PatientPhone
from healthcare_pipeline.parsers.hl7.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.semantic import (
    component_value,
    field,
    field_value,
    parse_address,
    parse_hl7_date,
    parse_name,
    parse_phone,
    parse_positive_integer,
)


class NK1Parser:
    """Convert one or more HL7 NK1 segments into NextOfKin values."""

    def parse_message(self, message: HL7Message) -> tuple[NextOfKin, ...]:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        segments = message.segments_named("NK1")
        return tuple(self.parse_segment(segment) for segment in segments)

    def parse_segment(self, segment: HL7Segment) -> NextOfKin:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "NK1":
            raise InvalidMessageError("NK1 parser requires an NK1 segment")
        try:
            return NextOfKin(
                set_id=parse_positive_integer(field_value(segment, 1), "NK1-1 set ID"),
                names=self._parse_names(field(segment, 2)),
                relationship=self._parse_code(field(segment, 3)),
                addresses=self._parse_addresses(field(segment, 4)),
                phones=self._parse_phones(field(segment, 5)),
                business_phones=self._parse_phones(field(segment, 6)),
                contact_roles=self._parse_codes(field(segment, 7)),
                start_date=parse_hl7_date(field_value(segment, 8), "NK1-8 start date"),
                end_date=parse_hl7_date(field_value(segment, 9), "NK1-9 end date"),
                organization_name=self._organization_name(field(segment, 13)),
                administrative_sex=AdministrativeSex.from_code(
                    field_value(segment, 15)
                ),
                birth_date=parse_hl7_date(field_value(segment, 16), "NK1-16 birth date"),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid NK1 segment: {exc}") from exc

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
        return cls._code_from_repetition(value.repetition(1))

    @classmethod
    def _parse_codes(cls, value: HL7Field | None) -> tuple[CodedValue, ...]:
        if value is None:
            return ()
        return tuple(
            cls._code_from_repetition(repetition)
            for repetition in value.repetitions
            if repetition.raw_value.strip()
        )

    @staticmethod
    def _code_from_repetition(repetition: HL7Repetition) -> CodedValue:
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
