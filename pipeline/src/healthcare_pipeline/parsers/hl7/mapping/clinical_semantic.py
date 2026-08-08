from __future__ import annotations

from decimal import Decimal, InvalidOperation

from healthcare_pipeline.parsers.hl7.core.field import HL7Field, HL7Repetition
from healthcare_pipeline.parsers.hl7.datatypes.coded_value import CodedValue
from healthcare_pipeline.parsers.hl7.datatypes.order_identifier import OrderIdentifier
from healthcare_pipeline.parsers.hl7.encounters.patient_location import PatientLocation
from healthcare_pipeline.parsers.hl7.encounters.provider import Provider
from healthcare_pipeline.parsers.hl7.mapping.semantic import component_value, family_name


def parse_coded_value(repetition: HL7Repetition, label: str) -> CodedValue:
    try:
        return CodedValue(
            identifier=component_value(repetition, 1),
            text=component_value(repetition, 2),
            coding_system=component_value(repetition, 3),
            alternate_identifier=component_value(repetition, 4),
            alternate_text=component_value(repetition, 5),
            alternate_coding_system=component_value(repetition, 6),
        )
    except ValueError as exc:
        raise ValueError(f"{label} must contain an identifier or text") from exc


def parse_optional_coded_field(value: HL7Field | None, label: str) -> CodedValue | None:
    if value is None or not value.value.strip():
        return None
    return parse_coded_value(value.repetition(1), label)


def parse_coded_repetitions(value: HL7Field | None, label: str) -> tuple[CodedValue, ...]:
    if value is None:
        return ()
    return tuple(
        parse_coded_value(repetition, label)
        for repetition in value.repetitions
        if repetition.raw_value.strip()
    )


def parse_order_identifier(value: HL7Field | None, label: str) -> OrderIdentifier | None:
    if value is None or not value.value.strip():
        return None
    repetition = value.repetition(1)
    entity_identifier = component_value(repetition, 1)
    if entity_identifier is None:
        raise ValueError(f"{label} entity identifier is required")
    return OrderIdentifier(
        entity_identifier=entity_identifier,
        namespace_id=component_value(repetition, 2),
        universal_id=component_value(repetition, 3),
        universal_id_type=component_value(repetition, 4),
    )


def parse_provider(repetition: HL7Repetition) -> Provider:
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


def parse_providers(value: HL7Field | None) -> tuple[Provider, ...]:
    if value is None:
        return ()
    return tuple(
        parse_provider(repetition)
        for repetition in value.repetitions
        if repetition.raw_value.strip()
    )


def parse_location(value: HL7Field | None) -> PatientLocation | None:
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


def parse_decimal(value: str | None, field_label: str, *, required: bool = False) -> Decimal | None:
    if value is None:
        if required:
            raise ValueError(f"{field_label} is required")
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_label} must be numeric") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_label} must be finite")
    return parsed


def parse_non_negative_integer(value: str | None, field_label: str) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{field_label} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{field_label} must not be negative")
    return parsed
