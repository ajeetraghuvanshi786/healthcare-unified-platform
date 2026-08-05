import pytest

from healthcare_pipeline.parsers import (
    InvalidPayloadError,
    MessageFormat,
    MessageFormatDetector,
)


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (b"MSH|^~\\&|LAB|HOSPITAL\rPID|1||123", MessageFormat.HL7_V2),
        (b'{"resourceType":"Patient","id":"1"}', MessageFormat.FHIR_JSON),
        (b'{"patient":"1"}', MessageFormat.JSON),
        (
            b'<Patient xmlns="http://hl7.org/fhir"><id value="1"/></Patient>',
            MessageFormat.FHIR_XML,
        ),
        (
            b'<ClinicalDocument xmlns="urn:hl7-org:v3"><id root="1"/></ClinicalDocument>',
            MessageFormat.CDA_XML,
        ),
        (b"<message><patient>1</patient></message>", MessageFormat.XML),
        (b"patient_id,name\n1,Alice\n2,Bob", MessageFormat.CSV),
        (b"not a healthcare payload", MessageFormat.UNKNOWN),
        (b"\xff\xfe\x00", MessageFormat.UNKNOWN),
    ],
)
def test_detects_supported_message_formats(
    payload: bytes,
    expected: MessageFormat,
) -> None:
    assert MessageFormatDetector().detect(payload) is expected


def test_detector_handles_utf8_bom_and_whitespace() -> None:
    payload = b"\xef\xbb\xbf  \r\n{\"resourceType\":\"Observation\"}"

    assert MessageFormatDetector().detect(payload) is MessageFormat.FHIR_JSON


def test_detector_rejects_empty_payload() -> None:
    with pytest.raises(InvalidPayloadError, match="must not be empty"):
        MessageFormatDetector().detect(b"")


def test_detector_rejects_non_bytes() -> None:
    with pytest.raises(TypeError, match="provided as bytes"):
        MessageFormatDetector().detect("MSH|^~\\&")  # type: ignore[arg-type]
