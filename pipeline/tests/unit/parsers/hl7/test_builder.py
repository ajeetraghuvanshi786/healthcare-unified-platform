import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7MessageBuilder


def test_builder_creates_complete_message_hierarchy() -> None:
    message = HL7MessageBuilder().build_message(
        raw_value=(
            "MSH|^~\\&|EPIC|HOSPITAL|LAB|HOSPITAL|202608051030||"
            "ADT^A01|MSG1|P|2.5\rPID|1||123^^^HOSPITAL^MR||DOE^JOHN"
        ),
        normalized_value=(
            "MSH|^~\\&|EPIC|HOSPITAL|LAB|HOSPITAL|202608051030||"
            "ADT^A01|MSG1|P|2.5\rPID|1||123^^^HOSPITAL^MR||DOE^JOHN"
        ),
    )

    assert len(message.segments) == 2
    assert message.segment("MSH").field(1).value == "|"
    assert message.segment("MSH").field(2).value == "^~\\&"
    assert message.segment("PID").field(3).component(1).value == "123"
    assert message.segment("PID").field(5).component(2).value == "JOHN"


def test_builder_preserves_empty_fields_components_and_subcomponents() -> None:
    message = HL7MessageBuilder().build_message(
        raw_value="MSH|^~\\&|A|B|C|D|20260805||ADT^A01|1|P|2.5\rZXX|A^^C|X&&Z||",
        normalized_value=(
            "MSH|^~\\&|A|B|C|D|20260805||ADT^A01|1|P|2.5\rZXX|A^^C|X&&Z||"
        ),
    )

    zxx = message.segment("ZXX")
    assert zxx.field(1).component(2).value == ""
    assert zxx.field(2).component(1).subcomponent(2) == ""
    assert zxx.field(3).value == ""
    assert zxx.field(4).value == ""


def test_builder_supports_repeating_fields() -> None:
    message = HL7MessageBuilder().build_message(
        raw_value="MSH|^~\\&|A|B|C|D|20260805||ADT^A01|1|P|2.5\rPID|1||111~222",
        normalized_value=(
            "MSH|^~\\&|A|B|C|D|20260805||ADT^A01|1|P|2.5\rPID|1||111~222"
        ),
    )

    patient_ids = message.segment("PID").field(3)
    assert patient_ids.repetition(1).component(1).value == "111"
    assert patient_ids.repetition(2).component(1).value == "222"


def test_builder_supports_custom_delimiters() -> None:
    message = HL7MessageBuilder().build_message(
        raw_value="MSH*$%!@*APP*FAC*REC*RFAC*20260805**ADT$A01*1*P*2.5\rPID*1**123$LOCAL",
        normalized_value=(
            "MSH*$%!@*APP*FAC*REC*RFAC*20260805**ADT$A01*1*P*2.5\rPID*1**123$LOCAL"
        ),
    )

    assert message.delimiters.field == "*"
    assert message.delimiters.component == "$"
    assert message.segment("PID").field(3).component(2).value == "LOCAL"


def test_builder_rejects_non_msh_first_segment() -> None:
    with pytest.raises(InvalidMessageError, match="begin with an MSH"):
        HL7MessageBuilder().build_message(
            raw_value="PID|1||123",
            normalized_value="PID|1||123",
        )
