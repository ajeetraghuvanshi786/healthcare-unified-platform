import pytest

from healthcare_pipeline.parsers.hl7 import HL7Message, HL7Parser
from healthcare_pipeline.parsers.types import MessageFormat

VALID_MESSAGE = (
    b"MSH|^~\\&|EPIC|HOSPITAL|LAB|HOSPITAL|202608051030||"
    b"ADT^A01|MSG00001|P|2.5\r"
    b"PID|1||123456^^^HOSPITAL^MR||DOE^JOHN\r"
    b"PV1|1|I|WARD1^101^1\r"
)


def test_parser_builds_immutable_hl7_message() -> None:
    message = HL7Parser().parse_message(VALID_MESSAGE)

    assert isinstance(message, HL7Message)
    assert tuple(segment.name for segment in message.segments) == (
        "MSH",
        "PID",
        "PV1",
    )
    assert message.segment("PID").field(5).component(1).value == "DOE"


def test_parser_preserves_decoded_raw_line_endings() -> None:
    payload = VALID_MESSAGE.replace(b"\r", b"\r\n")

    message = HL7Parser().parse_message(payload)

    assert "\r\n" in message.raw_value
    assert len(message.segments) == 3


def test_framework_parse_returns_success_result() -> None:
    result = HL7Parser().parse(VALID_MESSAGE, correlation_id="corr-1001")

    assert result.success is True
    assert result.message_format is MessageFormat.HL7_V2
    assert isinstance(result.data, HL7Message)
    assert result.metadata["segment_count"] == 3


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"PID|1||123",
        b"MSH|^^\\&|APP|FAC",
        b"MSH|^~\\&|APP|FAC\r\rPID|1",
        b"\xff\xfeMSH",
    ],
)
def test_framework_parse_returns_structured_failure(payload: bytes) -> None:
    result = HL7Parser().parse(payload, correlation_id="corr-failed")

    assert result.success is False
    assert result.data is None
    assert result.errors[0].code == "HL7_STRUCTURE_INVALID"


def test_parser_rejects_blank_correlation_id() -> None:
    with pytest.raises(ValueError, match="correlation_id"):
        HL7Parser().parse(VALID_MESSAGE, correlation_id=" ")
