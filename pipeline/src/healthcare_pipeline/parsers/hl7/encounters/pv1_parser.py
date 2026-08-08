from __future__ import annotations

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.core.field import HL7Field, HL7Repetition
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.demographics.patient_identifier import PatientIdentifier
from healthcare_pipeline.parsers.hl7.encounters.patient_class import PatientClass
from healthcare_pipeline.parsers.hl7.encounters.patient_encounter import PatientEncounter
from healthcare_pipeline.parsers.hl7.encounters.patient_location import PatientLocation
from healthcare_pipeline.parsers.hl7.encounters.provider import Provider
from healthcare_pipeline.parsers.hl7.mapping.semantic import (
    component_value,
    family_name,
    field,
    field_value,
    parse_hl7_datetime,
    parse_identifier,
    parse_positive_integer,
)


class PV1Parser:
    """Convert an HL7 PV1 segment into an immutable PatientEncounter."""

    def parse_message(self, message: HL7Message, *, occurrence: int = 1) -> PatientEncounter:
        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        if not isinstance(occurrence, int):
            raise TypeError("occurrence must be an integer")
        if occurrence < 1:
            raise ValueError("occurrence must be greater than zero")
        try:
            segment = message.segment("PV1", occurrence=occurrence)
        except IndexError as exc:
            raise InvalidMessageError(f"PV1 segment occurrence {occurrence} is missing") from exc
        return self.parse_segment(segment)

    def parse_segment(self, segment: HL7Segment) -> PatientEncounter:
        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "PV1":
            raise InvalidMessageError("PV1 parser requires a PV1 segment")
        try:
            return PatientEncounter(
                set_id=parse_positive_integer(field_value(segment, 1), "PV1-1 set ID"),
                patient_class=PatientClass.from_code(field_value(segment, 2)),
                assigned_location=self._parse_location(field(segment, 3)),
                prior_location=self._parse_location(field(segment, 6)),
                attending_provider=self._first_provider(field(segment, 7)),
                referring_provider=self._first_provider(field(segment, 8)),
                consulting_providers=self._parse_providers(field(segment, 9)),
                hospital_service=field_value(segment, 10),
                admission_type=field_value(segment, 14),
                patient_type=field_value(segment, 18),
                visit_number=self._parse_visit_number(field(segment, 19)),
                financial_class=self._first_component(field(segment, 20)),
                discharge_disposition=field_value(segment, 36),
                servicing_facility=field_value(segment, 39),
                admit_datetime=parse_hl7_datetime(
                    field_value(segment, 44),
                    "PV1-44 admit date/time",
                ),
                discharge_datetime=parse_hl7_datetime(
                    field_value(segment, 45), "PV1-45 discharge date/time"
                ),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid PV1 segment: {exc}") from exc

    @classmethod
    def _parse_location(cls, value: HL7Field | None) -> PatientLocation | None:
        if value is None or not value.value.strip():
            return None
        repetition = value.repetition(1)
        return PatientLocation(
            point_of_care=component_value(repetition, 1),
            room=component_value(repetition, 2),
            bed=component_value(repetition, 3),
            facility=component_value(repetition, 4),
            location_status=component_value(repetition, 5),
            person_location_type=component_value(repetition, 6),
            building=component_value(repetition, 7),
            floor=component_value(repetition, 8),
            description=component_value(repetition, 9),
        )

    @classmethod
    def _parse_provider(cls, repetition: HL7Repetition) -> Provider:
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

    @classmethod
    def _parse_providers(cls, value: HL7Field | None) -> tuple[Provider, ...]:
        if value is None:
            return ()
        return tuple(
            cls._parse_provider(repetition)
            for repetition in value.repetitions
            if repetition.raw_value.strip()
        )

    @classmethod
    def _first_provider(cls, value: HL7Field | None) -> Provider | None:
        providers = cls._parse_providers(value)
        return providers[0] if providers else None

    @staticmethod
    def _parse_visit_number(value: HL7Field | None) -> PatientIdentifier | None:
        if value is None or not value.value.strip():
            return None
        return parse_identifier(value.repetition(1), "PV1-19 visit")

    @staticmethod
    def _first_component(value: HL7Field | None) -> str | None:
        if value is None or not value.value.strip():
            return None
        return component_value(value.repetition(1), 1)
