import pytest

from healthcare_pipeline.parsers.hl7 import (
    HL7ProcessingId,
    HL7ProcessingMode,
)


def test_processing_id_maps_standard_codes() -> None:
    processing_id = HL7ProcessingId.from_code("p")

    assert processing_id.mode is HL7ProcessingMode.PRODUCTION


def test_processing_id_preserves_optional_processing_version() -> None:
    processing_id = HL7ProcessingId.from_code(
        "T",
        processing_version=" 2.5 ",
    )

    assert processing_id.mode is HL7ProcessingMode.TRAINING
    assert processing_id.processing_version == "2.5"


def test_processing_id_rejects_unknown_code() -> None:
    with pytest.raises(ValueError, match="unsupported HL7 processing code"):
        HL7ProcessingId.from_code("X")
