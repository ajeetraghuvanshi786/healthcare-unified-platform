import pytest

from healthcare_pipeline.parsers.hl7 import HL7Version


def test_version_accepts_hl7_v2_versions() -> None:
    version = HL7Version("2.5.1")

    assert str(version) == "2.5.1"
    assert version.parts == (2, 5, 1)


@pytest.mark.parametrize("value", ["", "3.0", "R4", "2", "2.x"])
def test_version_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match="invalid HL7 v2 version"):
        HL7Version(value)
