from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.clinical.diagnosis import Diagnosis
from healthcare_pipeline.parsers.hl7.core.field import HL7Field, HL7Repetition
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.datatypes.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.encounters.provider import Provider
from healthcare_pipeline.parsers.hl7.mapping.semantic import (
    component_value,
    family_name,
    field,
    field_value,
    parse_hl7_datetime,
    parse_positive_integer,
)


class DG1Parser:
    """Convert HL7 DG1 segments into immutable Diagnosis values."""

    def parse_message(self, message: HL7Message) -> tuple[Diagnosis, ...]:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        return tuple(self.parse_segment(segment) for segment in message.segments_named("DG1"))

    def parse_segment(self, segment: HL7Segment) -> Diagnosis:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "DG1":
            raise InvalidMessageError("DG1 parser requires a DG1 segment")
        try:
            set_id = parse_positive_integer(field_value(segment, 1), "DG1-1 set ID")
            if set_id is None:
                raise ValueError("DG1-1 set ID is required")
            code = self._parse_code(field(segment, 3))
            if code is None:
                raise ValueError("DG1-3 diagnosis code is required")
            priority = parse_positive_integer(field_value(segment, 15), "DG1-15 priority")
            return Diagnosis(
                set_id=set_id,
                coding_method=field_value(segment, 2),
                code=code,
                description=field_value(segment, 4),
                diagnosis_datetime=parse_hl7_datetime(
                    field_value(segment, 5), "DG1-5 diagnosis date/time"
                ),
                diagnosis_type=field_value(segment, 6),
                priority=priority,
                diagnosing_providers=self._parse_providers(field(segment, 16)),
                attestation_datetime=parse_hl7_datetime(
                    field_value(segment, 19), "DG1-19 attestation date/time"
                ),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid DG1 segment: {exc}") from exc

    @staticmethod
    def _parse_code(value: HL7Field | None) -> CodedValue | None:
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

    @classmethod
    def _parse_providers(cls, value: HL7Field | None) -> tuple[Provider, ...]:
        if value is None:
            return ()
        return tuple(
            cls._parse_provider(repetition)
            for repetition in value.repetitions
            if repetition.raw_value.strip()
        )

    @staticmethod
    def _parse_provider(repetition: HL7Repetition) -> Provider:
        return Provider(
            identifier=component_value(repetition, 1),
            family_name=family_name(repetition, 2),
            given_name=component_value(repetition, 3),
            middle_name=component_value(repetition, 4),
            suffix=component_value(repetition, 5),
            prefix=component_value(repetition, 6),
            professional_degree=component_value(repetition, 7),
            source_table=component_value(repetition, 8),
            assigning_authority=component_value(repetition, 9),
            name_type=component_value(repetition, 10),
            identifier_type=component_value(repetition, 13),
        )
