from datetime import UTC, datetime

import pytest

from healthcare_pipeline.parsers.hl7 import (
    HL7Delimiters,
    HL7MessageHeader,
    HL7MessageType,
    HL7ProcessingId,
    HL7Version,
)


def build_header() -> HL7MessageHeader:
    return HL7MessageHeader(
        delimiters=HL7Delimiters.default(),
        sending_application="EPIC",
        sending_facility="GENERAL_HOSPITAL",
        receiving_application="LAB",
        receiving_facility="GENERAL_HOSPITAL",
        message_datetime=datetime(2026, 8, 6, 10, 30, tzinfo=UTC),
        security=None,
        message_type=HL7MessageType("ADT", "A01"),
        message_control_id="MSG00001",
        processing_id=HL7ProcessingId.from_code("P"),
        version=HL7Version("2.5"),
    )


def test_header_is_immutable_and_typed() -> None:
    header = build_header()

    assert header.message_type.event_code == "ADT^A01"
    assert str(header.version) == "2.5"

    with pytest.raises(AttributeError):
        header.message_control_id = "CHANGED"  # type: ignore[misc]


def test_header_requires_timezone_aware_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        HL7MessageHeader(
            delimiters=HL7Delimiters.default(),
            sending_application="EPIC",
            sending_facility="GENERAL_HOSPITAL",
            receiving_application="LAB",
            receiving_facility="GENERAL_HOSPITAL",
            message_datetime=datetime(2026, 8, 6, 10, 30),
            security=None,
            message_type=HL7MessageType("ADT", "A01"),
            message_control_id="MSG00001",
            processing_id=HL7ProcessingId.from_code("P"),
            version=HL7Version("2.5"),
        )
