import pytest

from healthcare_pipeline.parsers.hl7 import HL7MessageType


def test_message_type_normalizes_codes_and_builds_event_code() -> None:
    message_type = HL7MessageType("adt", "a01", "adt_a01")

    assert message_type.message_code == "ADT"
    assert message_type.trigger_event == "A01"
    assert message_type.message_structure == "ADT_A01"
    assert message_type.event_code == "ADT^A01"


def test_message_type_rejects_blank_required_values() -> None:
    with pytest.raises(ValueError, match="message_code must not be blank"):
        HL7MessageType(" ", "A01")
