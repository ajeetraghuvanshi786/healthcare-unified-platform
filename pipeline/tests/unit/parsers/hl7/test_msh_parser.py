from datetime import timedelta

import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import (
    HL7Parser,
    HL7ProcessingMode,
    MSHParser,
)

VALID_MESSAGE = (
    b"MSH|^~\\&|EPIC|GENERAL_HOSPITAL|LAB|REFERENCE_LAB|"
    b"20260806103045.1234-0400||ADT^A01^ADT_A01|MSG00001|P|2.5.1|"
    b"7||AL|NE|USA|UNICODE UTF-8|en-US\r"
    b"PID|1||123456^^^GENERAL_HOSPITAL^MR||DOE^JOHN"
)


def test_msh_parser_extracts_semantic_header() -> None:
    message = HL7Parser().parse_message(VALID_MESSAGE)

    header = MSHParser().parse_message(message)

    assert header.sending_application == "EPIC"
    assert header.sending_facility == "GENERAL_HOSPITAL"
    assert header.receiving_application == "LAB"
    assert header.receiving_facility == "REFERENCE_LAB"
    assert header.message_type.message_code == "ADT"
    assert header.message_type.trigger_event == "A01"
    assert header.message_type.message_structure == "ADT_A01"
    assert header.message_control_id == "MSG00001"
    assert header.processing_id.mode is HL7ProcessingMode.PRODUCTION
    assert str(header.version) == "2.5.1"
    assert header.sequence_number == "7"
    assert header.accept_acknowledgment_type == "AL"
    assert header.application_acknowledgment_type == "NE"
    assert header.country_code == "USA"
    assert header.character_set == "UNICODE UTF-8"
    assert header.principal_language == "en-US"
    assert header.message_datetime.utcoffset() == -timedelta(hours=4)
    assert header.message_datetime.microsecond == 123400


def test_msh_parser_defaults_timezone_to_utc_when_offset_missing() -> None:
    payload = (
        b"MSH|^~\\&|EPIC|HOSPITAL|LAB|HOSPITAL|202608061030||"
        b"ORU^R01|MSG-2|T|2.5\rPID|1"
    )

    header = MSHParser().parse_message(HL7Parser().parse_message(payload))

    assert header.message_datetime.utcoffset() == timedelta(0)
    assert header.processing_id.mode is HL7ProcessingMode.TRAINING


def test_msh_parser_rejects_missing_required_field() -> None:
    payload = (
        b"MSH|^~\\&||HOSPITAL|LAB|HOSPITAL|202608061030||"
        b"ADT^A01|MSG-3|P|2.5\rPID|1"
    )

    message = HL7Parser().parse_message(payload)

    with pytest.raises(InvalidMessageError, match="MSH-3 sending application"):
        MSHParser().parse_message(message)


def test_msh_parser_rejects_invalid_timestamp() -> None:
    payload = (
        b"MSH|^~\\&|EPIC|HOSPITAL|LAB|HOSPITAL|202613011030||"
        b"ADT^A01|MSG-4|P|2.5\rPID|1"
    )

    message = HL7Parser().parse_message(payload)

    with pytest.raises(InvalidMessageError, match="invalid MSH segment"):
        MSHParser().parse_message(message)


def test_msh_parser_requires_msh_segment() -> None:
    message = HL7Parser().parse_message(VALID_MESSAGE)

    with pytest.raises(InvalidMessageError, match="requires an MSH segment"):
        MSHParser().parse_segment(
            message.segment("PID"),
            delimiters=message.delimiters,
        )
