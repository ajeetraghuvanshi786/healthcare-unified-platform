import pytest

from healthcare_pipeline.parsers.hl7 import (
    HL7Component,
    HL7Delimiters,
    HL7Field,
    HL7Message,
    HL7Repetition,
    HL7Segment,
)


def build_field(value: str) -> HL7Field:
    component = HL7Component(raw_value=value, subcomponents=(value,))
    repetition = HL7Repetition(raw_value=value, components=(component,))
    return HL7Field(raw_value=value, repetitions=(repetition,))


def test_component_uses_one_based_subcomponent_access() -> None:
    component = HL7Component(raw_value="AUTH&ISO", subcomponents=("AUTH", "ISO"))

    assert component.subcomponent(1) == "AUTH"
    assert component.subcomponent(2) == "ISO"


def test_field_supports_repetitions_and_components() -> None:
    first = HL7Repetition(
        raw_value="DOE^JOHN",
        components=(
            HL7Component("DOE", ("DOE",)),
            HL7Component("JOHN", ("JOHN",)),
        ),
    )
    second = HL7Repetition(
        raw_value="SMITH^JOHN",
        components=(
            HL7Component("SMITH", ("SMITH",)),
            HL7Component("JOHN", ("JOHN",)),
        ),
    )
    field = HL7Field(raw_value="DOE^JOHN~SMITH^JOHN", repetitions=(first, second))

    assert field.component(1).value == "DOE"
    assert field.component(1, repetition=2).value == "SMITH"


def test_segment_uses_one_based_field_access() -> None:
    segment = HL7Segment(
        "PID",
        "PID|1||123",
        (
            build_field("1"),
            build_field(""),
            build_field("123"),
        ),
        2,
    )

    assert segment.field(3).value == "123"


def test_message_supports_repeated_segment_lookup() -> None:
    msh = HL7Segment("MSH", "MSH|^~\\&", (build_field("|"), build_field("^~\\&")), 1)
    first_obx = HL7Segment("OBX", "OBX|1", (build_field("1"),), 2)
    second_obx = HL7Segment("OBX", "OBX|2", (build_field("2"),), 3)
    message = HL7Message(
        raw_value="MSH|^~\\&\rOBX|1\rOBX|2\r",
        delimiters=HL7Delimiters.default(),
        segments=(msh, first_obx, second_obx),
    )

    assert message.segment("OBX", occurrence=2).field(1).value == "2"
    assert len(message.segments_named("OBX")) == 2


def test_message_requires_msh_first() -> None:
    pid = HL7Segment("PID", "PID|1", (build_field("1"),), 1)

    with pytest.raises(ValueError, match="first HL7 segment must be MSH"):
        HL7Message("PID|1\r", HL7Delimiters.default(), (pid,))
