from __future__ import annotations

from datetime import date, datetime

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7.core.field import HL7Field, HL7Repetition
from healthcare_pipeline.parsers.hl7.core.message import HL7Message
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.demographics.administrative_sex import AdministrativeSex
from healthcare_pipeline.parsers.hl7.demographics.patient import Patient
from healthcare_pipeline.parsers.hl7.demographics.patient_address import PatientAddress
from healthcare_pipeline.parsers.hl7.demographics.patient_identifier import PatientIdentifier
from healthcare_pipeline.parsers.hl7.demographics.patient_name import PatientName
from healthcare_pipeline.parsers.hl7.demographics.patient_phone import PatientPhone


class PIDParser:
    """Convert an HL7 PID segment into an immutable :class:`Patient`.

    The parser maps transport-level PID fields into the patient domain models
    created by the preceding sprint. It does not perform canonical
    normalization, identity matching, USPS address verification, or E.164
    telephone normalization. Those operations belong to later pipeline stages
    so that the source-derived semantics remain traceable.
    """

    def parse_message(
        self,
        message: HL7Message,
        *,
        occurrence: int = 1,
    ) -> Patient:
        """Parse one PID occurrence from a structurally parsed HL7 message."""

        if not isinstance(message, HL7Message):
            raise TypeError("message must be an HL7Message")
        if not isinstance(occurrence, int):
            raise TypeError("occurrence must be an integer")
        if occurrence < 1:
            raise ValueError("occurrence must be greater than zero")

        try:
            segment = message.segment("PID", occurrence=occurrence)
        except IndexError as exc:
            raise InvalidMessageError(
                f"PID segment occurrence {occurrence} is missing"
            ) from exc

        return self.parse_segment(segment)

    def parse_segment(self, segment: HL7Segment) -> Patient:
        """Parse a PID segment into the patient domain aggregate."""

        if not isinstance(segment, HL7Segment):
            raise TypeError("segment must be an HL7Segment")
        if segment.name != "PID":
            raise InvalidMessageError("PID parser requires a PID segment")

        try:
            return Patient(
                set_id=self._parse_set_id(self._field_value(segment, 1)),
                identifiers=self._parse_identifiers(self._field(segment, 3)),
                names=self._parse_names(self._field(segment, 5)),
                birth_date=self._parse_birth_date(
                    self._field_value(segment, 7)
                ),
                administrative_sex=AdministrativeSex.from_code(
                    self._field_value(segment, 8)
                ),
                addresses=self._parse_addresses(self._field(segment, 11)),
                phones=(
                    *self._parse_phones(self._field(segment, 13)),
                    *self._parse_phones(self._field(segment, 14)),
                ),
                patient_account_number=self._parse_account_number(
                    self._field(segment, 18)
                ),
            )
        except (TypeError, ValueError) as exc:
            raise InvalidMessageError(f"invalid PID segment: {exc}") from exc

    @staticmethod
    def _field(segment: HL7Segment, position: int) -> HL7Field | None:
        try:
            return segment.field(position)
        except IndexError:
            return None

    @classmethod
    def _field_value(cls, segment: HL7Segment, position: int) -> str | None:
        field = cls._field(segment, position)
        if field is None:
            return None
        value = field.value.strip()
        return value or None

    @staticmethod
    def _parse_set_id(value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError("PID-1 set ID must be an integer") from exc

    @classmethod
    def _parse_identifiers(
        cls,
        field: HL7Field | None,
    ) -> tuple[PatientIdentifier, ...]:
        if field is None:
            return ()

        identifiers = tuple(
            cls._parse_identifier(repetition)
            for repetition in field.repetitions
            if repetition.raw_value.strip()
        )
        return identifiers

    @classmethod
    def _parse_identifier(
        cls,
        repetition: HL7Repetition,
    ) -> PatientIdentifier:
        identifier_value = cls._component_value(
            repetition,
            1,
            required=True,
        )

        if identifier_value is None:
            raise InvalidMessageError(
                "PID identifier value is required"
            )

        return PatientIdentifier(
            value=identifier_value,
            check_digit=cls._component_value(repetition, 2),
            check_digit_scheme=cls._component_value(repetition, 3),
            assigning_authority=cls._component_value(repetition, 4),
            identifier_type=cls._component_value(repetition, 5),
            assigning_facility=cls._component_value(repetition, 6),
        )

    @classmethod
    def _parse_names(
        cls,
        field: HL7Field | None,
    ) -> tuple[PatientName, ...]:
        if field is None:
            return ()

        return tuple(
            PatientName(
                family_name=cls._family_name(repetition),
                given_name=cls._component_value(repetition, 2),
                middle_name=cls._component_value(repetition, 3),
                suffix=cls._component_value(repetition, 4),
                prefix=cls._component_value(repetition, 5),
                degree=cls._component_value(repetition, 6),
                name_type=cls._component_value(repetition, 7),
            )
            for repetition in field.repetitions
            if repetition.raw_value.strip()
        )

    @staticmethod
    def _family_name(repetition: HL7Repetition) -> str | None:
        try:
            component = repetition.component(1)
        except IndexError:
            return None
        value = component.subcomponent(1).strip()
        return value or None

    @staticmethod
    def _parse_birth_date(value: str | None) -> date | None:
        if value is None:
            return None
        if len(value) < 8 or not value[:8].isdigit():
            raise ValueError("PID-7 birth date must begin with YYYYMMDD")
        try:
            return datetime.strptime(value[:8], "%Y%m%d").date()
        except ValueError as exc:
            raise ValueError("PID-7 birth date is not a valid calendar date") from exc

    @classmethod
    def _parse_addresses(
        cls,
        field: HL7Field | None,
    ) -> tuple[PatientAddress, ...]:
        if field is None:
            return ()

        return tuple(
            PatientAddress(
                street_address=cls._component_value(repetition, 1),
                other_designation=cls._component_value(repetition, 2),
                city=cls._component_value(repetition, 3),
                state_or_province=cls._component_value(repetition, 4),
                postal_code=cls._component_value(repetition, 5),
                country=cls._component_value(repetition, 6),
                address_type=cls._component_value(repetition, 7),
                county=cls._component_value(repetition, 9),
                census_tract=cls._component_value(repetition, 10),
            )
            for repetition in field.repetitions
            if repetition.raw_value.strip()
        )

    @classmethod
    def _parse_phones(
        cls,
        field: HL7Field | None,
    ) -> tuple[PatientPhone, ...]:
        if field is None:
            return ()

        return tuple(
            PatientPhone(
                number=cls._component_value(repetition, 1),
                use_code=cls._component_value(repetition, 2),
                equipment_type=cls._component_value(repetition, 3),
                email=cls._component_value(repetition, 4),
                country_code=cls._component_value(repetition, 5),
                area_code=cls._component_value(repetition, 6),
                local_number=cls._component_value(repetition, 7),
                extension=cls._component_value(repetition, 8),
            )
            for repetition in field.repetitions
            if repetition.raw_value.strip()
        )

    @classmethod
    def _parse_account_number(
        cls,
        field: HL7Field | None,
    ) -> PatientIdentifier | None:
        if field is None or not field.value.strip():
            return None
        return cls._parse_identifier(field.repetition(1))

    @staticmethod
    def _component_value(
        repetition: HL7Repetition,
        position: int,
        *,
        required: bool = False,
    ) -> str | None:
        try:
            value = repetition.component(position).value.strip()
        except IndexError:
            value = ""

        if value:
            return value
        if required:
            raise ValueError(
                f"required component {position} is missing from {repetition.raw_value!r}"
            )
        return None
