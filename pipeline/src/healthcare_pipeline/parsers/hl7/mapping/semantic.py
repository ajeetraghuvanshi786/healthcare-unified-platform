from __future__ import annotations

import re
from datetime import (
    UTC,
    date,
    datetime,
    timedelta,
    timezone,
)

from healthcare_pipeline.parsers.hl7.core.field import HL7Field, HL7Repetition
from healthcare_pipeline.parsers.hl7.core.segment import HL7Segment
from healthcare_pipeline.parsers.hl7.demographics.patient_address import PatientAddress
from healthcare_pipeline.parsers.hl7.demographics.patient_identifier import (
    PatientIdentifier,
)
from healthcare_pipeline.parsers.hl7.demographics.patient_name import PatientName
from healthcare_pipeline.parsers.hl7.demographics.patient_phone import PatientPhone

_TIMESTAMP_PATTERN = re.compile(
    r"^(?P<value>\d{4}(?:\d{2}){0,5})(?:\.(?P<fraction>\d{1,6}))?"
    r"(?P<offset>[+-]\d{4})?$"
)


def normalize_optional(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string or None")
    normalized = value.strip()
    if not normalized:
        return None
    if any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{field_name} must not contain control characters")
    return normalized


def normalize_required(value: str, field_name: str) -> str:
    normalized = normalize_optional(value, field_name)
    if normalized is None:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


def field(segment: HL7Segment, position: int) -> HL7Field | None:
    try:
        return segment.field(position)
    except IndexError:
        return None


def field_value(segment: HL7Segment, position: int) -> str | None:
    value = field(segment, position)
    if value is None:
        return None
    normalized = value.value.strip()
    return normalized or None


def component_value(repetition: HL7Repetition, position: int) -> str | None:
    try:
        value = repetition.component(position).value.strip()
    except IndexError:
        return None
    return value or None


def family_name(repetition: HL7Repetition, position: int = 1) -> str | None:
    try:
        component = repetition.component(position)
        value = component.subcomponent(1).strip()
    except IndexError:
        return None
    return value or None


def parse_positive_integer(value: str | None, field_label: str) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{field_label} must be an integer") from exc
    if parsed < 1:
        raise ValueError(f"{field_label} must be greater than zero")
    return parsed


def parse_hl7_date(value: str | None, field_label: str) -> date | None:
    if value is None:
        return None
    if len(value) < 8 or not value[:8].isdigit():
        raise ValueError(f"{field_label} must begin with YYYYMMDD")
    try:
        return datetime.strptime(value[:8], "%Y%m%d").date()
    except ValueError as exc:
        raise ValueError(f"{field_label} is not a valid calendar date") from exc


def parse_hl7_datetime(value: str | None, field_label: str) -> datetime | None:
    if value is None:
        return None
    match = _TIMESTAMP_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(f"{field_label} is not a valid HL7 date/time")

    digits = match.group("value")
    if len(digits) not in {4, 6, 8, 10, 12, 14}:
        raise ValueError(f"{field_label} has unsupported precision")

    parsed = datetime.strptime(digits.ljust(14, "0"), "%Y%m%d%H%M%S")
    fraction = match.group("fraction")
    if fraction:
        parsed = parsed.replace(microsecond=int(fraction.ljust(6, "0")))

    offset = match.group("offset")
    if offset is None:
        return parsed.replace(tzinfo=UTC)

    sign = 1 if offset[0] == "+" else -1
    hours = int(offset[1:3])
    minutes = int(offset[3:5])
    if hours > 23 or minutes > 59:
        raise ValueError(f"{field_label} has an invalid timezone offset")
    return parsed.replace(
        tzinfo=timezone(sign * timedelta(hours=hours, minutes=minutes))
    )


def parse_identifier(repetition: HL7Repetition, label: str) -> PatientIdentifier:
    identifier_value = component_value(repetition, 1)
    if identifier_value is None:
        raise ValueError(f"{label} identifier value is required")
    return PatientIdentifier(
        value=identifier_value,
        check_digit=component_value(repetition, 2),
        check_digit_scheme=component_value(repetition, 3),
        assigning_authority=component_value(repetition, 4),
        identifier_type=component_value(repetition, 5),
        assigning_facility=component_value(repetition, 6),
    )


def parse_name(repetition: HL7Repetition) -> PatientName:
    return PatientName(
        family_name=family_name(repetition),
        given_name=component_value(repetition, 2),
        middle_name=component_value(repetition, 3),
        suffix=component_value(repetition, 4),
        prefix=component_value(repetition, 5),
        degree=component_value(repetition, 6),
        name_type=component_value(repetition, 7),
    )


def parse_address(repetition: HL7Repetition) -> PatientAddress:
    return PatientAddress(
        street_address=component_value(repetition, 1),
        other_designation=component_value(repetition, 2),
        city=component_value(repetition, 3),
        state_or_province=component_value(repetition, 4),
        postal_code=component_value(repetition, 5),
        country=component_value(repetition, 6),
        address_type=component_value(repetition, 7),
        county=component_value(repetition, 9),
        census_tract=component_value(repetition, 10),
    )


def parse_phone(repetition: HL7Repetition) -> PatientPhone:
    return PatientPhone(
        number=component_value(repetition, 1),
        use_code=component_value(repetition, 2),
        equipment_type=component_value(repetition, 3),
        email=component_value(repetition, 4),
        country_code=component_value(repetition, 5),
        area_code=component_value(repetition, 6),
        local_number=component_value(repetition, 7),
        extension=component_value(repetition, 8),
    )
