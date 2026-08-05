import pytest

from healthcare_pipeline.parsers.exceptions import InvalidPayloadError
from healthcare_pipeline.parsers.hl7 import HL7PayloadDecoder


def test_decoder_decodes_utf8_payload() -> None:
    decoder = HL7PayloadDecoder()

    result = decoder.decode(b"MSH|^~\\&|APP|FAC")

    assert result == "MSH|^~\\&|APP|FAC"


def test_decoder_removes_utf8_bom() -> None:
    decoder = HL7PayloadDecoder()

    result = decoder.decode(b"\xef\xbb\xbfMSH|^~\\&|APP|FAC")

    assert result.startswith("MSH")
    assert not result.startswith("\ufeff")


@pytest.mark.parametrize("payload", [b"", b"\xef\xbb\xbf"])
def test_decoder_rejects_empty_content(payload: bytes) -> None:
    with pytest.raises(InvalidPayloadError):
        HL7PayloadDecoder().decode(payload)


def test_decoder_rejects_invalid_utf8() -> None:
    with pytest.raises(InvalidPayloadError, match="not valid UTF-8"):
        HL7PayloadDecoder().decode(b"\xff\xfeMSH")


def test_decoder_rejects_nul_character() -> None:
    with pytest.raises(InvalidPayloadError, match="NUL"):
        HL7PayloadDecoder().decode(b"MSH|^~\\&\x00")
