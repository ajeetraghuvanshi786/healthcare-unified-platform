import pytest

from healthcare_pipeline.parsers.exceptions import InvalidMessageError
from healthcare_pipeline.parsers.hl7 import HL7MessageNormalizer


@pytest.mark.parametrize(
    "message",
    [
        "MSH|^~\\&|APP|FAC\rPID|1||123\r",
        "MSH|^~\\&|APP|FAC\nPID|1||123\n",
        "MSH|^~\\&|APP|FAC\r\nPID|1||123\r\n",
    ],
)
def test_normalizer_unifies_supported_line_endings(message: str) -> None:
    result = HL7MessageNormalizer().normalize(message)

    assert result == "MSH|^~\\&|APP|FAC\rPID|1||123"


def test_normalizer_rejects_empty_internal_segment() -> None:
    normalizer = HL7MessageNormalizer()
    normalized = normalizer.normalize("MSH|^~\\&|APP|FAC\r\rPID|1")

    with pytest.raises(InvalidMessageError, match="empty segment"):
        normalizer.split_segments(normalized)


def test_normalizer_does_not_trim_field_data() -> None:
    result = HL7MessageNormalizer().normalize(
        "MSH|^~\\&|APP|FAC\rNTE|1||  clinically relevant spaces  \r"
    )

    assert result.endswith("  clinically relevant spaces  ")
